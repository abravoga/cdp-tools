#!/usr/bin/env python3
"""
Generar Dashboard HTML con información completa de costos y recursos GCP
"""

from gcp_integration import GCPClient
from datetime import datetime
from google.cloud import compute_v1
import json


def get_machine_type_info(machine_type_url):
    """Extraer info del tipo de máquina desde la URL"""
    parts = machine_type_url.split('/')
    return parts[-1] if parts else 'unknown'


def get_disk_info(client, zone):
    """Obtener información de discos"""
    try:
        disks_client = compute_v1.DisksClient(credentials=client.credentials)
        disks = list(disks_client.list(project=client.project_id, zone=zone))
        return disks
    except:
        return []


def collect_data(client):
    """Recopilar toda la información del proyecto"""

    print("Recopilando información del proyecto...")

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

    # 1. Obtener instancias
    print("  - Obteniendo instancias Compute Engine...")
    instances_by_zone = client.list_instances()

    if instances_by_zone:
        for zone, instances in instances_by_zone.items():
            region = '-'.join(zone.split('-')[:-1])
            if region not in data['regions']:
                data['regions'][region] = {'instances': 0, 'disks': 0}

            for instance in instances:
                data['instances']['total'] += 1
                data['regions'][region]['instances'] += 1

                machine_type = get_machine_type_info(instance.machine_type)

                # Contar tipos de máquina
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

            # Obtener discos de esta zona
            disks = get_disk_info(client, zone)
            for disk in disks:
                data['disks']['count'] += 1
                data['disks']['total_gb'] += disk.size_gb
                data['regions'][region]['disks'] += 1

                disk_type = disk.type.split('/')[-1] if disk.type else 'unknown'
                if disk_type not in data['disks']['types']:
                    data['disks']['types'][disk_type] = {'count': 0, 'total_gb': 0}

                data['disks']['types'][disk_type]['count'] += 1
                data['disks']['types'][disk_type]['total_gb'] += disk.size_gb

    # 2. Obtener información de storage
    print("  - Obteniendo información de Cloud Storage...")
    buckets = client.list_buckets()

    if buckets:
        from google.cloud import monitoring_v3
        import time

        monitoring_client = monitoring_v3.MetricServiceClient(credentials=client.credentials)

        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        interval = monitoring_v3.TimeInterval({
            "end_time": {"seconds": seconds, "nanos": nanos},
            "start_time": {"seconds": (seconds - 86400), "nanos": nanos},
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

    # 3. Estimar costos (precios aproximados de GCP Europe)
    print("  - Calculando estimación de costos...")

    # Compute Engine - precio por hora aproximado
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

    # Calcular costo mensual de instancias running
    for machine_type, info in data['machine_types'].items():
        cost_per_hour = machine_costs_hourly.get(machine_type, 0.1)  # Default si no está en la lista
        monthly_cost = info['running'] * cost_per_hour * 730  # 730 horas/mes
        data['costs']['compute'] += monthly_cost

    # Storage - $0.020 per GB/month (Standard Storage Europe)
    data['costs']['storage'] = data['storage']['total_gb'] * 0.020

    # Persistent Disks - $0.040 per GB/month (Standard)
    disk_cost = data['disks']['total_gb'] * 0.040
    data['costs']['compute'] += disk_cost

    data['costs']['total'] = data['costs']['compute'] + data['costs']['storage']

    print("  - Datos recopilados correctamente")

    return data


def generate_html_dashboard(data):
    """Generar dashboard HTML con toda la información"""

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard GCP - {data['project_id']}</title>
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

        .header .subtitle {{
            color: #666;
            font-size: 1.1em;
        }}

        .header .timestamp {{
            color: #999;
            font-size: 0.9em;
            margin-top: 10px;
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
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}

        .stat-card .label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
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
            <h1>Dashboard GCP</h1>
            <div class="subtitle">Proyecto: {data['project_id']}</div>
            <div class="timestamp">Última actualización: {data['timestamp']}</div>
        </div>

        <!-- Tarjetas de estadísticas principales -->
        <div class="stats-grid">
            <div class="stat-card cost">
                <div class="label">Costo Estimado Mensual</div>
                <div class="value">${data['costs']['total']:,.2f}</div>
                <div class="subvalue">Total del proyecto</div>
            </div>

            <div class="stat-card">
                <div class="label">Compute Engine</div>
                <div class="value">${data['costs']['compute']:,.2f}</div>
                <div class="subvalue">Instancias + Discos</div>
            </div>

            <div class="stat-card">
                <div class="label">Cloud Storage</div>
                <div class="value">${data['costs']['storage']:,.2f}</div>
                <div class="subvalue">{data['storage']['total_gb']:,.0f} GB</div>
            </div>

            <div class="stat-card success">
                <div class="label">Instancias Activas</div>
                <div class="value">{len(data['instances']['running'])}</div>
                <div class="subvalue">de {data['instances']['total']} totales</div>
            </div>

            <div class="stat-card">
                <div class="label">Tipos de Máquina</div>
                <div class="value">{len(data['machine_types'])}</div>
                <div class="subvalue">Diferentes configuraciones</div>
            </div>

            <div class="stat-card">
                <div class="label">Almacenamiento en Disco</div>
                <div class="value">{data['disks']['total_gb']:,.0f}</div>
                <div class="subvalue">GB en {data['disks']['count']} discos</div>
            </div>
        </div>

        <!-- Gráficos -->
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
    for machine_type, info in sorted(data['machine_types'].items(), key=lambda x: x[1]['count'], reverse=True):
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
    for bucket in sorted(data['storage']['buckets'], key=lambda x: x['size_gb'], reverse=True):
        monthly_cost = bucket['size_gb'] * 0.020
        html += f"""
                    <tr>
                        <td><strong>{bucket['name']}</strong></td>
                        <td>{bucket['location']}</td>
                        <td>{bucket['size_gb']:,.2f}</td>
                        <td>${monthly_cost:,.2f}</td>
                    </tr>
"""

    html += f"""
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
    for region, info in sorted(data['regions'].items()):
        html += f"""
                    <tr>
                        <td><strong>{region}</strong></td>
                        <td>{info['instances']}</td>
                        <td>{info['disks']}</td>
                    </tr>
"""

    # Preparar datos para los gráficos
    machine_labels = list(data['machine_types'].keys())
    machine_counts = [data['machine_types'][m]['count'] for m in machine_labels]

    disk_labels = list(data['disks']['types'].keys())
    disk_sizes = [data['disks']['types'][d]['total_gb'] for d in disk_labels]

    html += f"""
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Gráfico de costos
        new Chart(document.getElementById('costChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Compute Engine', 'Cloud Storage'],
                datasets: [{{
                    data: [{data['costs']['compute']:.2f}, {data['costs']['storage']:.2f}],
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
                    data: [{len(data['instances']['running'])}, {len(data['instances']['stopped'])}],
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
    </script>
</body>
</html>
"""

    return html


def main():
    """Generar el dashboard"""

    print("="*80)
    print("GENERADOR DE DASHBOARD GCP")
    print("="*80)
    print()

    # Conectar a GCP
    client = GCPClient()

    # Recopilar datos
    data = collect_data(client)

    # Generar HTML
    print("\nGenerando dashboard HTML...")
    html = generate_html_dashboard(data)

    # Guardar archivo
    output_file = f"gcp_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[OK] Dashboard generado: {output_file}")
    print("\nAbre el archivo en tu navegador para ver el dashboard completo")
    print("="*80)

    # Mostrar resumen
    print("\nRESUMEN:")
    print(f"  - Costo total estimado mensual: ${data['costs']['total']:,.2f}")
    print(f"  - Instancias totales: {data['instances']['total']} ({len(data['instances']['running'])} running)")
    print(f"  - Almacenamiento total: {data['storage']['total_gb']:,.0f} GB")
    print(f"  - Discos totales: {data['disks']['count']} ({data['disks']['total_gb']:,.0f} GB)")
    print("="*80)


if __name__ == "__main__":
    main()
