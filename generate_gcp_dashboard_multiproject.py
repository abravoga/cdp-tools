#!/usr/bin/env python3
"""
Generar Dashboard HTML COMPLETO para MÚLTIPLES proyectos GCP
Permite comparar dev y prod con selector de proyecto
"""

from gcp_integration import GCPClient
from datetime import datetime
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
    print(f"  Recopilando datos históricos de {client.project_id}...")

    periods = {
        '1month': 30,
        '3months': 90,
        '6months': 180,
        '1year': 365
    }

    historical_data = {}

    for period_name, days in periods.items():
        print(f"    - {period_name}...")

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
    print(f"  Recopilando datos actuales de {client.project_id}...")

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


def generate_multiproject_html_dashboard(projects_data):
    """Generar dashboard HTML para múltiples proyectos"""

    # Obtener lista de proyectos
    project_ids = list(projects_data.keys())
    first_project = project_ids[0]

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard GCP Multi-Proyecto</title>
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

        .selector-group {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .selector-section {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }}

        .selector-label {{
            font-weight: 600;
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .selector-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }}

        .project-btn, .period-btn {{
            padding: 10px 25px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }}

        .project-btn:hover, .period-btn:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }}

        .project-btn.active, .period-btn.active {{
            background: #667eea;
            color: white;
        }}

        .project-btn.dev {{
            border-color: #3498db;
        }}

        .project-btn.dev.active {{
            background: #3498db;
        }}

        .project-btn.prod {{
            border-color: #e74c3c;
        }}

        .project-btn.prod.active {{
            background: #e74c3c;
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

        .project-content {{
            display: none;
        }}

        .project-content.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Dashboard GCP Multi-Proyecto</h1>
            <div style="color: #999; margin-top: 10px;">Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

            <div class="selector-group">
                <div class="selector-section">
                    <div class="selector-label">Proyecto</div>
                    <div class="selector-buttons">
"""

    # Generar botones de proyecto
    for idx, project_id in enumerate(project_ids):
        env_class = 'dev' if 'dev' in project_id else 'prod'
        env_label = 'DEV' if 'dev' in project_id else 'PROD'
        active_class = 'active' if idx == 0 else ''
        html += f"""                        <button class="project-btn {env_class} {active_class}" onclick="showProject('{project_id}')">{env_label}</button>\n"""

    html += """                    </div>
                </div>

                <div class="selector-section">
                    <div class="selector-label">Período Histórico</div>
                    <div class="selector-buttons">
                        <button class="period-btn active" onclick="showPeriod('1month')">1 Mes</button>
                        <button class="period-btn" onclick="showPeriod('3months')">3 Meses</button>
                        <button class="period-btn" onclick="showPeriod('6months')">6 Meses</button>
                        <button class="period-btn" onclick="showPeriod('1year')">1 Año</button>
                    </div>
                </div>
            </div>
        </div>

"""

    # Generar contenido para cada proyecto
    for project_id in project_ids:
        current_data = projects_data[project_id]['current']
        active_class = 'active' if project_id == first_project else ''

        # Preparar datos para gráficos
        machine_labels = list(current_data['machine_types'].keys()) if current_data['machine_types'] else []
        machine_counts = [current_data['machine_types'][m]['count'] for m in machine_labels] if machine_labels else []

        disk_labels = list(current_data['disks']['types'].keys()) if current_data['disks']['types'] else []
        disk_sizes = [current_data['disks']['types'][d]['total_gb'] for d in disk_labels] if disk_labels else []

        html += f"""
        <div class="project-content {active_class}" id="content-{project_id}">
            <div class="section-header">
                <h2>Proyecto: {project_id}</h2>
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

            <div class="historical-chart">
                <h3>Evolución de Costos Estimados</h3>
                <div class="chart-container">
                    <canvas id="costTrendChart-{project_id}"></canvas>
                </div>
            </div>

            <div class="historical-chart">
                <h3>Evolución del Almacenamiento (Cloud Storage)</h3>
                <div class="chart-container">
                    <canvas id="storageTrendChart-{project_id}"></canvas>
                </div>
            </div>

            <div class="historical-chart">
                <h3>Evolución del Número de Instancias</h3>
                <div class="chart-container">
                    <canvas id="instanceTrendChart-{project_id}"></canvas>
                </div>
            </div>

            <!-- SECCIÓN DETALLADA ACTUAL -->
            <div class="section-header">
                <h2>📊 Estado Actual Detallado</h2>
            </div>

            <div class="charts-grid">
                <div class="chart-card">
                    <h3>Distribución de Costos</h3>
                    <canvas id="costChart-{project_id}"></canvas>
                </div>

                <div class="chart-card">
                    <h3>Estado de Instancias</h3>
                    <canvas id="statusChart-{project_id}"></canvas>
                </div>

                <div class="chart-card">
                    <h3>Tipos de Máquina</h3>
                    <canvas id="machineChart-{project_id}"></canvas>
                </div>

                <div class="chart-card">
                    <h3>Tipos de Disco</h3>
                    <canvas id="diskChart-{project_id}"></canvas>
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
"""

    # JavaScript
    html += f"""
    </div>

    <script>
        // Datos de todos los proyectos
        const projectsData = {json.dumps(projects_data)};

        let currentProject = '{first_project}';
        let currentPeriod = '1month';
        let charts = {{}};

        function showProject(projectId) {{
            currentProject = projectId;

            // Actualizar botones de proyecto
            document.querySelectorAll('.project-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Mostrar/ocultar contenido
            document.querySelectorAll('.project-content').forEach(content => {{
                content.classList.remove('active');
            }});
            document.getElementById('content-' + projectId).classList.add('active');

            // Inicializar gráficos del proyecto
            initializeProjectCharts(projectId);
        }}

        function showPeriod(period) {{
            currentPeriod = period;

            // Actualizar botones de período
            document.querySelectorAll('.period-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Actualizar gráficos históricos
            updateHistoricalCharts(currentProject, period);
        }}

        function updateHistoricalCharts(projectId, period) {{
            const historicalData = projectsData[projectId].historical[period];

            // Preparar datos
            const costDates = Object.keys(historicalData.costs).sort();
            const costValues = costDates.map(date => historicalData.costs[date].total);

            const storageDates = Object.keys(historicalData.storage).sort();
            const storageValues = storageDates.map(date => historicalData.storage[date]);

            const instanceDates = Object.keys(historicalData.instances).sort();
            const instanceValues = instanceDates.map(date => historicalData.instances[date]);

            const chartPrefix = 'costTrendChart-' + projectId;
            const storagePrefix = 'storageTrendChart-' + projectId;
            const instancePrefix = 'instanceTrendChart-' + projectId;

            // Destruir gráficos anteriores
            if (charts[chartPrefix]) charts[chartPrefix].destroy();
            if (charts[storagePrefix]) charts[storagePrefix].destroy();
            if (charts[instancePrefix]) charts[instancePrefix].destroy();

            // Crear gráfico de costos
            charts[chartPrefix] = new Chart(document.getElementById(chartPrefix), {{
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
                        legend: {{ display: true, position: 'top' }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true }}
                    }}
                }}
            }});

            // Crear gráfico de storage
            charts[storagePrefix] = new Chart(document.getElementById(storagePrefix), {{
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
                        legend: {{ display: true, position: 'top' }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true }}
                    }}
                }}
            }});

            // Crear gráfico de instancias
            charts[instancePrefix] = new Chart(document.getElementById(instancePrefix), {{
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
                        legend: {{ display: true, position: 'top' }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{ stepSize: 1 }}
                        }}
                    }}
                }}
            }});
        }}

        function initializeProjectCharts(projectId) {{
            const currentData = projectsData[projectId].current;

            const machineLabels = Object.keys(currentData.machine_types);
            const machineCounts = machineLabels.map(m => currentData.machine_types[m].count);

            const diskLabels = Object.keys(currentData.disks.types);
            const diskSizes = diskLabels.map(d => currentData.disks.types[d].total_gb);

            const costPrefix = 'costChart-' + projectId;
            const statusPrefix = 'statusChart-' + projectId;
            const machinePrefix = 'machineChart-' + projectId;
            const diskPrefix = 'diskChart-' + projectId;

            // Destruir gráficos anteriores si existen
            if (charts[costPrefix]) charts[costPrefix].destroy();
            if (charts[statusPrefix]) charts[statusPrefix].destroy();
            if (charts[machinePrefix]) charts[machinePrefix].destroy();
            if (charts[diskPrefix]) charts[diskPrefix].destroy();

            // Gráfico de costos
            charts[costPrefix] = new Chart(document.getElementById(costPrefix), {{
                type: 'doughnut',
                data: {{
                    labels: ['Compute Engine', 'Cloud Storage'],
                    datasets: [{{
                        data: [currentData.costs.compute, currentData.costs.storage],
                        backgroundColor: ['#667eea', '#764ba2'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ position: 'bottom' }},
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

            // Gráfico de estado
            charts[statusPrefix] = new Chart(document.getElementById(statusPrefix), {{
                type: 'pie',
                data: {{
                    labels: ['Running', 'Stopped'],
                    datasets: [{{
                        data: [currentData.instances.running.length, currentData.instances.stopped.length],
                        backgroundColor: ['#27ae60', '#e74c3c'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ position: 'bottom' }}
                    }}
                }}
            }});

            // Gráfico de máquinas
            charts[machinePrefix] = new Chart(document.getElementById(machinePrefix), {{
                type: 'bar',
                data: {{
                    labels: machineLabels,
                    datasets: [{{
                        label: 'Número de instancias',
                        data: machineCounts,
                        backgroundColor: '#667eea',
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{ stepSize: 1 }}
                        }}
                    }}
                }}
            }});

            // Gráfico de discos
            charts[diskPrefix] = new Chart(document.getElementById(diskPrefix), {{
                type: 'bar',
                data: {{
                    labels: diskLabels,
                    datasets: [{{
                        label: 'Tamaño total (GB)',
                        data: diskSizes,
                        backgroundColor: '#764ba2',
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true }}
                    }}
                }}
            }});

            // Actualizar gráficos históricos
            updateHistoricalCharts(projectId, currentPeriod);
        }}

        // Inicializar con el primer proyecto
        document.addEventListener('DOMContentLoaded', function() {{
            initializeProjectCharts('{first_project}');
        }});
    </script>
</body>
</html>
"""

    return html


def main():
    """Generar dashboard multi-proyecto"""

    print("="*80)
    print("DASHBOARD GCP MULTI-PROYECTO")
    print("="*80)
    print()

    # Proyectos a analizar
    project_ids = ['mo-cloudera-dev', 'mo-cloudera-prod']

    projects_data = {}

    for project_id in project_ids:
        print(f"\n{'='*80}")
        print(f"Procesando proyecto: {project_id}")
        print(f"{'='*80}\n")

        try:
            client = GCPClient(project_id=project_id)

            # Recopilar datos actuales
            current_data = collect_current_data(client)

            # Recopilar datos históricos
            historical_data = collect_historical_data(client)

            projects_data[project_id] = {
                'current': current_data,
                'historical': historical_data
            }

            print(f"\n[OK] Datos de {project_id} recopilados correctamente")
            print(f"  - Costo mensual: ${current_data['costs']['total']:,.2f}")
            print(f"  - Instancias: {current_data['instances']['total']} ({len(current_data['instances']['running'])} running)")
            print(f"  - Almacenamiento: {current_data['storage']['total_gb']:,.0f} GB")

        except Exception as e:
            print(f"\n[ERROR] No se pudo procesar {project_id}: {e}")

    if not projects_data:
        print("\n[ERROR] No se pudo recopilar datos de ningún proyecto")
        return

    # Generar HTML
    print(f"\n{'='*80}")
    print("Generando dashboard HTML multi-proyecto...")
    print(f"{'='*80}\n")

    html = generate_multiproject_html_dashboard(projects_data)

    # Guardar
    output_file = f"gcp_dashboard_multiproject_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Dashboard multi-proyecto generado: {output_file}")
    print(f"\n{'='*80}")
    print("RESUMEN MULTI-PROYECTO:")
    print(f"{'='*80}\n")

    total_cost = 0
    total_instances = 0
    total_running = 0
    total_storage = 0

    for project_id, data in projects_data.items():
        current = data['current']
        env = 'DEV' if 'dev' in project_id else 'PROD'

        print(f"{env} ({project_id}):")
        print(f"  - Costo mensual: ${current['costs']['total']:,.2f}")
        print(f"  - Instancias: {current['instances']['total']} ({len(current['instances']['running'])} running)")
        print(f"  - Almacenamiento: {current['storage']['total_gb']:,.0f} GB")
        print()

        total_cost += current['costs']['total']
        total_instances += current['instances']['total']
        total_running += len(current['instances']['running'])
        total_storage += current['storage']['total_gb']

    print(f"{'='*80}")
    print("TOTAL COMBINADO:")
    print(f"  - Costo mensual total: ${total_cost:,.2f}")
    print(f"  - Instancias totales: {total_instances} ({total_running} running)")
    print(f"  - Almacenamiento total: {total_storage:,.0f} GB")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
