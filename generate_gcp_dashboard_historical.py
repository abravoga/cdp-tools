#!/usr/bin/env python3
"""
Generar Dashboard HTML con información histórica de costos y recursos GCP
Incluye vistas de 1 mes, 3 meses, 6 meses y 1 año
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

    # Obtener datos de storage total
    aggregation = monitoring_v3.Aggregation({
        "alignment_period": {"seconds": 86400},  # 1 día
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

        # Procesar resultados
        data_points = []
        for result in results:
            for point in result.points:
                # Convertir timestamp correctamente
                timestamp = point.interval.end_time.timestamp()
                value_gb = point.value.double_value / (1024**3)
                data_points.append({
                    'timestamp': timestamp,
                    'value_gb': value_gb
                })

        # Agrupar por día y sumar
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
    """Obtener conteo histórico de instancias (estimado)"""

    # Como no hay métrica directa, usamos CPU como proxy
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

        # Calcular costos estimados históricos
        cost_history = {}
        for date_str, storage_gb in storage_history.items():
            storage_cost = storage_gb * 0.020
            instance_count = instance_history.get(date_str, 0)
            compute_cost = instance_count * 100  # Estimación aproximada
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
    """Recopilar datos actuales (reutilizar del script anterior)"""

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
    for machine_type, info in data['machine_types'].items():
        monthly_cost = info['running'] * 0.1 * 730
        data['costs']['compute'] += monthly_cost

    data['costs']['storage'] = data['storage']['total_gb'] * 0.020
    disk_cost = data['disks']['total_gb'] * 0.040
    data['costs']['compute'] += disk_cost
    data['costs']['total'] = data['costs']['compute'] + data['costs']['storage']

    return data


def generate_html_dashboard_with_history(current_data, historical_data):
    """Generar dashboard HTML con datos históricos"""

    # Preparar datos para gráficos históricos
    periods_config = {
        '1month': {'label': '1 Mes', 'days': 30},
        '3months': {'label': '3 Meses', 'days': 90},
        '6months': {'label': '6 Meses', 'days': 180},
        '1year': {'label': '1 Año', 'days': 365}
    }

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard GCP Histórico - {current_data['project_id']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
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

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }}

        .trend-up {{
            color: #e74c3c;
        }}

        .trend-down {{
            color: #27ae60;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Dashboard GCP - Análisis Histórico</h1>
            <div style="color: #666; font-size: 1.1em;">Proyecto: {current_data['project_id']}</div>
            <div style="color: #999; margin-top: 10px;">Última actualización: {current_data['timestamp']}</div>

            <div class="period-selector">
                <button class="period-btn active" onclick="showPeriod('1month')">1 Mes</button>
                <button class="period-btn" onclick="showPeriod('3months')">3 Meses</button>
                <button class="period-btn" onclick="showPeriod('6months')">6 Meses</button>
                <button class="period-btn" onclick="showPeriod('1year')">1 Año</button>
            </div>
        </div>

        <!-- Estadísticas actuales -->
        <div class="stats-grid">
            <div class="stat-card cost">
                <div class="label">Costo Mensual Actual</div>
                <div class="value">${current_data['costs']['total']:,.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">Instancias Running</div>
                <div class="value">{len(current_data['instances']['running'])}</div>
            </div>
            <div class="stat-card">
                <div class="label">Almacenamiento Total</div>
                <div class="value">{current_data['storage']['total_gb']:,.0f} GB</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Discos</div>
                <div class="value">{current_data['disks']['total_gb']:,.0f} GB</div>
            </div>
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

        <!-- SECCIÓN DE DATOS DETALLADOS ACTUALES -->
        <div class="historical-chart">
            <h3>Análisis Detallado - Estado Actual</h3>
        </div>

        <!-- Gráficos de distribución actual -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px;">
            <div class="historical-chart">
                <h3>Distribución de Costos Actuales</h3>
                <div style="height: 300px;">
                    <canvas id="costChart"></canvas>
                </div>
            </div>

            <div class="historical-chart">
                <h3>Estado de Instancias</h3>
                <div style="height: 300px;">
                    <canvas id="statusChart"></canvas>
                </div>
            </div>

            <div class="historical-chart">
                <h3>Tipos de Máquina</h3>
                <div style="height: 300px;">
                    <canvas id="machineChart"></canvas>
                </div>
            </div>

            <div class="historical-chart">
                <h3>Tipos de Disco</h3>
                <div style="height: 300px;">
                    <canvas id="diskChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Tabla de tipos de máquina -->
        <div class="historical-chart">
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
{self._generate_machine_table(current_data)}
                </tbody>
            </table>
        </div>

        <!-- Tabla de buckets -->
        <div class="historical-chart">
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
{self._generate_buckets_table(current_data)}
                </tbody>
            </table>
        </div>

        <!-- Tabla de regiones -->
        <div class="historical-chart">
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
{self._generate_regions_table(current_data)}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Datos históricos
        const historicalData = {json.dumps(historical_data)};

        let costChart, storageChart, instanceChart;
        let currentPeriod = '1month';

        function showPeriod(period) {{
            currentPeriod = period;

            // Actualizar botones
            document.querySelectorAll('.period-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Actualizar gráficos
            updateCharts(period);
        }}

        function updateCharts(period) {{
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
            if (costChart) costChart.destroy();
            costChart = new Chart(document.getElementById('costTrendChart'), {{
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
            if (storageChart) storageChart.destroy();
            storageChart = new Chart(document.getElementById('storageTrendChart'), {{
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
            if (instanceChart) instanceChart.destroy();
            instanceChart = new Chart(document.getElementById('instanceTrendChart'), {{
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

        // Inicializar con período de 1 mes
        document.addEventListener('DOMContentLoaded', function() {{
            updateCharts('1month');
        }});
    </script>
</body>
</html>
"""

    return html


def main():
    """Generar dashboard con datos históricos"""

    print("="*80)
    print("DASHBOARD GCP - ANÁLISIS HISTÓRICO")
    print("="*80)
    print()

    client = GCPClient()

    # Recopilar datos actuales
    current_data = collect_current_data(client)

    # Recopilar datos históricos
    historical_data = collect_historical_data(client)

    # Generar HTML
    print("\nGenerando dashboard HTML...")
    html = generate_html_dashboard_with_history(current_data, historical_data)

    # Guardar
    output_file = f"gcp_dashboard_historical_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[OK] Dashboard histórico generado: {output_file}")
    print("\n="*80)
    print("FUNCIONALIDADES:")
    print("  - Vista de costos a 1 mes, 3 meses, 6 meses y 1 año")
    print("  - Gráficos de tendencia de costos")
    print("  - Evolución del almacenamiento")
    print("  - Evolución del número de instancias")
    print("  - Comparativas entre períodos")
    print("="*80)


if __name__ == "__main__":
    main()
