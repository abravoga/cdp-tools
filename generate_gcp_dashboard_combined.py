#!/usr/bin/env python3
"""
Generar Dashboard HTML COMPLETO con información histórica Y detallada de costos y recursos GCP
Combina análisis temporal (1m, 3m, 6m, 1año) con datos detallados actuales
"""

from gcp_integration import GCPClient
from datetime import datetime, timedelta
from google.cloud import compute_v1, monitoring_v3
import json
import time


def get_historical_storage_data(client, days=30):
    """Obtener datos históricos de almacenamiento"""

    monitoring_client = monitoring_v3.MetricServiceClient(credentials=client.credentials)

    now = time.time()
    start_time = now - (days * 86400)

    interval = monitoring_v3.TimeInterval({
        "end_time": {"seconds": int(now), "nanos": 0},
        "start_time": {"seconds": int(start_time), "nanos": 0},
    })

    aggregation = monitoring_v3.Aggregation({
        "alignment_period": {"seconds": 86400},
        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
    })

    try:
        results = monitoring_client.list_time_series(
            request={
                "name": f"projects/{client.project_id}",
                "filter": 'metric.type="storage.googleapis.com/storage/total_bytes"',
                "interval": interval,
                "aggregation": aggregation,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )

        data_points = []
        for result in results:
            for point in result.points:
                timestamp = point.interval.end_time.timestamp()
                value_gb = point.value.double_value / (1024**3)
                data_points.append({
                    'timestamp': timestamp,
                    'value_gb': value_gb
                })

        daily_totals = {}
        for point in data_points:
            date_str = datetime.fromtimestamp(point['timestamp']).strftime('%Y-%m-%d')
            if date_str not in daily_totals:
                daily_totals[date_str] = 0
            daily_totals[date_str] += point['value_gb']

        return daily_totals

    except Exception as e:
        print(f"  [WARNING] Error obteniendo datos históricos de storage: {e}")
        return {}


def get_historical_instance_count(client, days=30):
    """Obtener conteo histórico de instancias"""

    monitoring_client = monitoring_v3.MetricServiceClient(credentials=client.credentials)

    now = time.time()
    start_time = now - (days * 86400)

    interval = monitoring_v3.TimeInterval({
        "end_time": {"seconds": int(now), "nanos": 0},
        "start_time": {"seconds": int(start_time), "nanos": 0},
    })

    aggregation = monitoring_v3.Aggregation({
        "alignment_period": {"seconds": 86400},
        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
        "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_COUNT,
    })

    try:
        results = monitoring_client.list_time_series(
            request={
                "name": f"projects/{client.project_id}",
                "filter": 'metric.type="compute.googleapis.com/instance/cpu/utilization"',
                "interval": interval,
                "aggregation": aggregation,
            }
        )

        data_points = {}
        for result in results:
            for point in result.points:
                timestamp = point.interval.end_time.timestamp()
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                data_points[date_str] = int(point.value.double_value)

        return data_points

    except Exception as e:
        print(f"  [WARNING] Error obteniendo conteo histórico de instancias: {e}")
        return {}


def collect_historical_data(client):
    """Recopilar datos históricos para diferentes períodos"""

    print("Recopilando datos históricos...")

    periods = {
        '1month': 30,
        '3months': 90,
        '6months': 180,
        '1year': 365
    }

    historical_data = {}

    for period_name, days in periods.items():
        print(f"  - Obteniendo datos de {period_name}...")

        storage_history = get_historical_storage_data(client, days)
        instance_history = get_historical_instance_count(client, days)

        cost_history = {}
        for date_str, storage_gb in storage_history.items():
            storage_cost = storage_gb * 0.020
            instance_count = instance_history.get(date_str, 0)
            compute_cost = instance_count * 100
            cost_history[date_str] = {
                'storage': storage_cost,
                'compute': compute_cost,
                'total': storage_cost + compute_cost
            }

        historical_data[period_name] = {
            'storage': storage_history,
            'instances': instance_history,
            'costs': cost_history,
            'days': days
        }

    return historical_data


def collect_current_data(client):
    """Recopilar datos actuales completos"""

    print("Recopilando datos actuales...")

    data = {
        'project_id': client.project_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'instances': {'running': [], 'stopped': [], 'total': 0},
        'machine_types': {},
        'disks': {'types': {}, 'total_gb': 0, 'count': 0},
        'storage': {'buckets': [], 'total_gb': 0},
        'costs': {'compute': 0, 'storage': 0, 'total': 0},
        'regions': {}
    }

    # Obtener instancias
    print("  - Obteniendo instancias...")
    instances_by_zone = client.list_instances()

    if instances_by_zone:
        for zone, instances in instances_by_zone.items():
            region = '-'.join(zone.split('-')[:-1])
            if region not in data['regions']:
                data['regions'][region] = {'instances': 0, 'disks': 0}

            for instance in instances:
                data['instances']['total'] += 1
                data['regions'][region]['instances'] += 1

                machine_type = instance.machine_type.split('/')[-1]

                if machine_type not in data['machine_types']:
                    data['machine_types'][machine_type] = {'count': 0, 'running': 0, 'stopped': 0}

                data['machine_types'][machine_type]['count'] += 1

                instance_info = {
                    'name': instance.name,
                    'machine_type': machine_type,
                    'zone': zone,
                    'status': instance.status
                }

                if instance.status == 'RUNNING':
                    data['instances']['running'].append(instance_info)
                    data['machine_types'][machine_type]['running'] += 1
                else:
                    data['instances']['stopped'].append(instance_info)
                    data['machine_types'][machine_type]['stopped'] += 1

            # Discos
            disks_client = compute_v1.DisksClient(credentials=client.credentials)
            try:
                disks = list(disks_client.list(project=client.project_id, zone=zone))
                for disk in disks:
                    data['disks']['count'] += 1
                    data['disks']['total_gb'] += disk.size_gb
                    data['regions'][region]['disks'] += 1

                    disk_type = disk.type.split('/')[-1]
                    if disk_type not in data['disks']['types']:
                        data['disks']['types'][disk_type] = {'count': 0, 'total_gb': 0}

                    data['disks']['types'][disk_type]['count'] += 1
                    data['disks']['types'][disk_type]['total_gb'] += disk.size_gb
            except:
                pass

    # Storage
    print("  - Obteniendo storage...")
    buckets = client.list_buckets()

    if buckets:
        monitoring_client = monitoring_v3.MetricServiceClient(credentials=client.credentials)

        now = time.time()
        interval = monitoring_v3.TimeInterval({
            "end_time": {"seconds": int(now), "nanos": 0},
            "start_time": {"seconds": int(now - 86400), "nanos": 0},
        })

        for bucket in buckets:
            try:
                results = monitoring_client.list_time_series(
                    request={
                        "name": f"projects/{client.project_id}",
                        "filter": f'metric.type="storage.googleapis.com/storage/total_bytes" '
                                  f'AND resource.labels.bucket_name="{bucket.name}"',
                        "interval": interval,
                        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                    }
                )

                size_bytes = 0
                for result in results:
                    if result.points:
                        size_bytes = result.points[0].value.double_value
                        break

                size_gb = size_bytes / (1024**3)
                data['storage']['total_gb'] += size_gb
                data['storage']['buckets'].append({
                    'name': bucket.name,
                    'location': bucket.location,
                    'size_gb': size_gb
                })
            except:
                pass

    # Calcular costos
    print("  - Calculando costos...")

    machine_costs_hourly = {
        'e2-standard-2': 0.067,
        'e2-standard-4': 0.134,
        'e2-standard-8': 0.268,
        'n1-standard-1': 0.0475,
        'n1-standard-2': 0.095,
        'n1-standard-4': 0.19,
        'n1-standard-8': 0.38,
        'n2-standard-2': 0.097,
        'n2-standard-4': 0.194,
        'n2-standard-8': 0.388,
        'n2-highmem-4': 0.260,
        'n2-highmem-8': 0.520,
    }

    for machine_type, info in data['machine_types'].items():
        cost_per_hour = machine_costs_hourly.get(machine_type, 0.1)
        monthly_cost = info['running'] * cost_per_hour * 730
        data['costs']['compute'] += monthly_cost

    data['costs']['storage'] = data['storage']['total_gb'] * 0.020
    disk_cost = data['disks']['total_gb'] * 0.040
    data['costs']['compute'] += disk_cost
    data['costs']['total'] = data['costs']['compute'] + data['costs']['storage']

    return data


def generate_combined_html_dashboard(current_data, historical_data):
    """Generar dashboard HTML completo con datos históricos Y detallados"""

    # Preparar datos para gráficos
    machine_labels = list(current_data['machine_types'].keys())
    machine_counts = [current_data['machine_types'][m]['count'] for m in machine_labels]

    disk_labels = list(current_data['disks']['types'].keys())
    disk_sizes = [current_data['disks']['types'][d]['total_gb'] for d in disk_labels]

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard GCP Completo - {current_data['project_id']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }}

        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .period-selector {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .period-btn {{
            padding: 10px 25px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }}

        .period-btn:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }}

        .period-btn.active {{
            background: #667eea;
            color: white;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card .label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-card.cost .value {{
            color: #e74c3c;
        }}

        .stat-card.success .value {{
            color: #27ae60;
        }}

        .stat-card .subvalue {{
            font-size: 0.9em;
            color: #999;
            margin-top: 5px;
        }}

        .section-header {{
            background: white;
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin: 40px 0 20px 0;
        }}

        .section-header h2 {{
            color: #667eea;
            font-size: 1.8em;
        }}

        .historical-chart {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .historical-chart h3 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .chart-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .chart-card h3 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}

        .table-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}

        .table-card h3 {{
            color: #667eea;
            margin-bottom: 20px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .status-badge {{
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .status-running {{
            background: #d4edda;
            color: #155724;
        }}

        .status-stopped {{
            background: #f8d7da;
            color: #721c24;
        }}

        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Dashboard GCP - Análisis Completo</h1>
            <div style="color: #666; font-size: 1.1em;">Proyecto: {current_data['project_id']}</div>
            <div style="color: #999; margin-top: 10px;">Última actualización: {current_data['timestamp']}</div>

            <div class="period-selector">
                <button class="period-btn active" onclick="showPeriod('1month')">1 Mes</button>
                <button class="period-btn" onclick="showPeriod('3months')">3 Meses</button>
                <button class="period-btn" onclick="showPeriod('6months')">6 Meses</button>
                <button class="period-btn" onclick="showPeriod('1year')">1 Año</button>
            </div>
        </div>

        <!-- Tarjetas de estadísticas principales -->
        <div class="stats-grid">
            <div class="stat-card cost">
                <div class="label">Costo Estimado Mensual</div>
                <div class="value">${current_data['costs']['total']:,.2f}</div>
                <div class="subvalue">Total del proyecto</div>
            </div>

            <div class="stat-card">
                <div class="label">Compute Engine</div>
                <div class="value">${current_data['costs']['compute']:,.2f}</div>
                <div class="subvalue">Instancias + Discos</div>
            </div>

            <div class="stat-card">
                <div class="label">Cloud Storage</div>
                <div class="value">${current_data['costs']['storage']:,.2f}</div>
                <div class="subvalue">{current_data['storage']['total_gb']:,.0f} GB</div>
            </div>

            <div class="stat-card success">
                <div class="label">Instancias Activas</div>
                <div class="value">{len(current_data['instances']['running'])}</div>
                <div class="subvalue">de {current_data['instances']['total']} totales</div>
            </div>

            <div class="stat-card">
                <div class="label">Tipos de Máquina</div>
                <div class="value">{len(current_data['machine_types'])}</div>
                <div class="subvalue">Diferentes configuraciones</div>
            </div>

            <div class="stat-card">
                <div class="label">Almacenamiento en Disco</div>
                <div class="value">{current_data['disks']['total_gb']:,.0f}</div>
                <div class="subvalue">GB en {current_data['disks']['count']} discos</div>
            </div>
        </div>

        <!-- SECCIÓN HISTÓRICA -->
        <div class="section-header">
            <h2>📈 Análisis Histórico - Evolución Temporal</h2>
        </div>

        <!-- Gráfico de costos históricos -->
        <div class="historical-chart">
            <h3>Evolución de Costos Estimados</h3>
            <div class="chart-container">
                <canvas id="costTrendChart"></canvas>
            </div>
        </div>

        <!-- Gráfico de almacenamiento histórico -->
        <div class="historical-chart">
            <h3>Evolución del Almacenamiento (Cloud Storage)</h3>
            <div class="chart-container">
                <canvas id="storageTrendChart"></canvas>
            </div>
        </div>

        <!-- Gráfico de instancias histórico -->
        <div class="historical-chart">
            <h3>Evolución del Número de Instancias</h3>
            <div class="chart-container">
                <canvas id="instanceTrendChart"></canvas>
            </div>
        </div>

        <!-- SECCIÓN DETALLADA ACTUAL -->
        <div class="section-header">
            <h2>📊 Estado Actual Detallado</h2>
        </div>

        <!-- Gráficos de distribución -->
        <div class="charts-grid">
            <div class="chart-card">
                <h3>Distribución de Costos</h3>
                <canvas id="costChart"></canvas>
            </div>

            <div class="chart-card">
                <h3>Estado de Instancias</h3>
                <canvas id="statusChart"></canvas>
            </div>

            <div class="chart-card">
                <h3>Tipos de Máquina</h3>
                <canvas id="machineChart"></canvas>
            </div>

            <div class="chart-card">
                <h3>Tipos de Disco</h3>
                <canvas id="diskChart"></canvas>
            </div>
        </div>

        <!-- Tabla de tipos de máquina -->
        <div class="table-card">
            <h3>Detalle de Tipos de Máquina</h3>
            <table>
                <thead>
                    <tr>
                        <th>Tipo de Máquina</th>
                        <th>Total</th>
                        <th>Running</th>
                        <th>Stopped</th>
                        <th>% Utilización</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Agregar filas de tipos de máquina
    for machine_type, info in sorted(current_data['machine_types'].items(), key=lambda x: x[1]['count'], reverse=True):
        utilization = (info['running'] / info['count'] * 100) if info['count'] > 0 else 0
        html += f"""
                    <tr>
                        <td><strong>{machine_type}</strong></td>
                        <td>{info['count']}</td>
                        <td><span class="status-badge status-running">{info['running']}</span></td>
                        <td><span class="status-badge status-stopped">{info['stopped']}</span></td>
                        <td>
                            {utilization:.1f}%
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {utilization}%"></div>
                            </div>
                        </td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>

        <!-- Tabla de buckets -->
        <div class="table-card">
            <h3>Buckets de Cloud Storage</h3>
            <table>
                <thead>
                    <tr>
                        <th>Bucket</th>
                        <th>Ubicación</th>
                        <th>Tamaño (GB)</th>
                        <th>Costo Mensual</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Agregar filas de buckets
    for bucket in sorted(current_data['storage']['buckets'], key=lambda x: x['size_gb'], reverse=True):
        monthly_cost = bucket['size_gb'] * 0.020
        html += f"""
                    <tr>
                        <td><strong>{bucket['name']}</strong></td>
                        <td>{bucket['location']}</td>
                        <td>{bucket['size_gb']:,.2f}</td>
                        <td>${monthly_cost:,.2f}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>

        <!-- Tabla de regiones -->
        <div class="table-card">
            <h3>Distribución por Región</h3>
            <table>
                <thead>
                    <tr>
                        <th>Región</th>
                        <th>Instancias</th>
                        <th>Discos</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Agregar filas de regiones
    for region, info in sorted(current_data['regions'].items()):
        html += f"""
                    <tr>
                        <td><strong>{region}</strong></td>
                        <td>{info['instances']}</td>
                        <td>{info['disks']}</td>
                    </tr>
"""

    html += f"""
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Datos históricos
        const historicalData = {json.dumps(historical_data)};

        let costTrendChart, storageTrendChart, instanceTrendChart;
        let currentPeriod = '1month';

        function showPeriod(period) {{
            currentPeriod = period;

            // Actualizar botones
            document.querySelectorAll('.period-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Actualizar gráficos
            updateHistoricalCharts(period);
        }}

        function updateHistoricalCharts(period) {{
            const data = historicalData[period];

            // Preparar datos de costos
            const costDates = Object.keys(data.costs).sort();
            const costValues = costDates.map(date => data.costs[date].total);

            // Preparar datos de storage
            const storageDates = Object.keys(data.storage).sort();
            const storageValues = storageDates.map(date => data.storage[date]);

            // Preparar datos de instancias
            const instanceDates = Object.keys(data.instances).sort();
            const instanceValues = instanceDates.map(date => data.instances[date]);

            // Actualizar gráfico de costos
            if (costTrendChart) costTrendChart.destroy();
            costTrendChart = new Chart(document.getElementById('costTrendChart'), {{
                type: 'line',
                data: {{
                    labels: costDates,
                    datasets: [{{
                        label: 'Costo Total Estimado ($)',
                        data: costValues,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});

            // Actualizar gráfico de storage
            if (storageTrendChart) storageTrendChart.destroy();
            storageTrendChart = new Chart(document.getElementById('storageTrendChart'), {{
                type: 'line',
                data: {{
                    labels: storageDates,
                    datasets: [{{
                        label: 'Almacenamiento (GB)',
                        data: storageValues,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});

            // Actualizar gráfico de instancias
            if (instanceTrendChart) instanceTrendChart.destroy();
            instanceTrendChart = new Chart(document.getElementById('instanceTrendChart'), {{
                type: 'line',
                data: {{
                    labels: instanceDates,
                    datasets: [{{
                        label: 'Número de Instancias',
                        data: instanceValues,
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                stepSize: 1
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // Gráficos de estado actual (estáticos)

        // Gráfico de costos
        new Chart(document.getElementById('costChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Compute Engine', 'Cloud Storage'],
                datasets: [{{
                    data: [{current_data['costs']['compute']:.2f}, {current_data['costs']['storage']:.2f}],
                    backgroundColor: ['#667eea', '#764ba2'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.label + ': $' + context.parsed.toFixed(2);
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Gráfico de estado de instancias
        new Chart(document.getElementById('statusChart'), {{
            type: 'pie',
            data: {{
                labels: ['Running', 'Stopped'],
                datasets: [{{
                    data: [{len(current_data['instances']['running'])}, {len(current_data['instances']['stopped'])}],
                    backgroundColor: ['#27ae60', '#e74c3c'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});

        // Gráfico de tipos de máquina
        new Chart(document.getElementById('machineChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(machine_labels)},
                datasets: [{{
                    label: 'Número de instancias',
                    data: {json.dumps(machine_counts)},
                    backgroundColor: '#667eea',
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});

        // Gráfico de tipos de disco
        new Chart(document.getElementById('diskChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(disk_labels)},
                datasets: [{{
                    label: 'Tamaño total (GB)',
                    data: {json.dumps(disk_sizes)},
                    backgroundColor: '#764ba2',
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Inicializar con período de 1 mes
        document.addEventListener('DOMContentLoaded', function() {{
            updateHistoricalCharts('1month');
        }});
    </script>
</body>
</html>
"""

    return html


def main():
    """Generar dashboard completo combinado"""

    print("="*80)
    print("DASHBOARD GCP COMPLETO - HISTÓRICO + DETALLADO")
    print("="*80)
    print()

    client = GCPClient()

    # Recopilar datos actuales
    current_data = collect_current_data(client)

    # Recopilar datos históricos
    historical_data = collect_historical_data(client)

    # Generar HTML
    print("\nGenerando dashboard HTML combinado...")
    html = generate_combined_html_dashboard(current_data, historical_data)

    # Guardar
    output_file = f"gcp_dashboard_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[OK] Dashboard completo generado: {output_file}")
    print("\n="*80)
    print("CONTENIDO DEL DASHBOARD:")
    print("  ANÁLISIS HISTÓRICO:")
    print("    - Selector de período (1m, 3m, 6m, 1 año)")
    print("    - Evolución de costos en el tiempo")
    print("    - Evolución de almacenamiento")
    print("    - Evolución de número de instancias")
    print()
    print("  ANÁLISIS DETALLADO ACTUAL:")
    print("    - Tarjetas de estadísticas principales")
    print("    - Gráficos de distribución de costos")
    print("    - Gráfico de estado de instancias")
    print("    - Gráfico de tipos de máquina")
    print("    - Gráfico de tipos de disco")
    print("    - Tabla detallada de tipos de máquina con % utilización")
    print("    - Tabla completa de buckets con costos")
    print("    - Tabla de distribución por región")
    print("="*80)
    print("\nRESUMEN:")
    print(f"  - Costo total mensual: ${current_data['costs']['total']:,.2f}")
    print(f"  - Instancias totales: {current_data['instances']['total']} ({len(current_data['instances']['running'])} running)")
    print(f"  - Almacenamiento: {current_data['storage']['total_gb']:,.0f} GB")
    print(f"  - Discos: {current_data['disks']['count']} ({current_data['disks']['total_gb']:,.0f} GB)")
    print("="*80)


if __name__ == "__main__":
    main()
