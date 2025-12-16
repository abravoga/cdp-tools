#!/usr/bin/env python3
"""
CDP Dashboard Generator
Generates an interactive HTML dashboard with CDP resource information
"""

import subprocess
import json
import sys
import base64
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class CDPDashboard:
    def __init__(self, cdp_cli_path=r"C:\Program Files\Python312\Scripts\cdp.exe",
                 logo_path=r"C:\Users\abravoga\OneDrive - MASORANGE\Descargas\logoO_positivo.jpg"):
        self.cdp_cli = cdp_cli_path
        self.logo_path = logo_path
        self.data = {}
        self.logo_base64 = self.encode_logo_to_base64()

    def encode_logo_to_base64(self):
        """Encode logo image to base64 for embedding in HTML"""
        try:
            logo_file = Path(self.logo_path)
            if logo_file.exists():
                with open(logo_file, 'rb') as f:
                    logo_data = f.read()
                    encoded = base64.b64encode(logo_data).decode('utf-8')
                    # Determine MIME type based on extension
                    ext = logo_file.suffix.lower()
                    mime_types = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.svg': 'image/svg+xml',
                        '.gif': 'image/gif'
                    }
                    mime_type = mime_types.get(ext, 'image/jpeg')
                    return f"data:{mime_type};base64,{encoded}"
            else:
                print(f"Advertencia: Logo no encontrado en {self.logo_path}")
                return ""
        except Exception as e:
            print(f"Error al cargar el logo: {e}")
            return ""

    def run_cdp_command(self, *args):
        """Execute CDP CLI command and return JSON result"""
        try:
            cmd = [self.cdp_cli] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout) if result.stdout else {}
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {' '.join(args)}", file=sys.stderr)
            print(f"Error: {e.stderr}", file=sys.stderr)
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            return {}

    def collect_data(self):
        """Collect all CDP data"""
        print("Recopilando datos de CDP...")

        print("  - Obteniendo información de usuario...")
        self.data['user'] = self.run_cdp_command('iam', 'get-user')

        print("  - Listando Data Lakes...")
        self.data['datalakes'] = self.run_cdp_command('datalake', 'list-datalakes')

        print("  - Listando Data Hubs...")
        self.data['datahubs'] = self.run_cdp_command('datahub', 'list-clusters')

        print("  - Listando entornos...")
        self.data['environments'] = self.run_cdp_command('environments', 'list-environments')

        print("  - Obteniendo datos de consumo (último mes)...")
        self.data['consumption'] = self.collect_consumption_data()

        print("Datos recopilados exitosamente!\n")

    def collect_consumption_data(self, days=30):
        """Collect consumption data for the last N days"""
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=days)

        from_timestamp = from_date.strftime('%Y-%m-%dT00:00:00Z')
        to_timestamp = to_date.strftime('%Y-%m-%dT23:59:59Z')

        try:
            # Get all consumption records (may require pagination)
            all_records = []
            next_token = None
            max_pages = 100  # Safety limit
            page_count = 0

            while page_count < max_pages:
                args = [
                    'consumption', 'list-compute-usage-records',
                    '--from-timestamp', from_timestamp,
                    '--to-timestamp', to_timestamp,
                    '--page-size', '1000'
                ]

                if next_token:
                    args.extend(['--starting-token', next_token])

                result = self.run_cdp_command(*args)

                if 'records' in result:
                    all_records.extend(result['records'])

                next_token = result.get('nextToken')
                page_count += 1

                if not next_token:
                    break

            print(f"    Obtenidos {len(all_records)} registros de consumo")
            return {'records': all_records, 'from_date': from_timestamp, 'to_date': to_timestamp}

        except Exception as e:
            print(f"    Advertencia: No se pudieron obtener datos de consumo: {e}")
            return {'records': [], 'from_date': from_timestamp, 'to_date': to_timestamp}

    def analyze_data(self):
        """Analyze collected data and generate metrics"""
        analysis = {
            'total_clusters': 0,
            'active_clusters': 0,
            'stopped_clusters': 0,
            'total_nodes': 0,
            'active_nodes': 0,
            'total_datalakes': 0,
            'running_datalakes': 0,
            'clusters_by_env': {},
            'clusters_by_type': {},
            'cost_estimate': 0
        }

        # Analyze Data Hubs
        if 'clusters' in self.data.get('datahubs', {}):
            clusters = self.data['datahubs']['clusters']
            analysis['total_clusters'] = len(clusters)

            for cluster in clusters:
                status = cluster.get('status', 'UNKNOWN')
                env_name = cluster.get('environmentName', 'Unknown')
                workload_type = cluster.get('workloadType', 'Unknown')
                node_count = cluster.get('nodeCount', 0)

                analysis['total_nodes'] += node_count

                if status == 'AVAILABLE':
                    analysis['active_clusters'] += 1
                    analysis['active_nodes'] += node_count
                elif status == 'STOPPED':
                    analysis['stopped_clusters'] += 1

                # Group by environment
                if env_name not in analysis['clusters_by_env']:
                    analysis['clusters_by_env'][env_name] = {'total': 0, 'active': 0, 'stopped': 0}
                analysis['clusters_by_env'][env_name]['total'] += 1
                if status == 'AVAILABLE':
                    analysis['clusters_by_env'][env_name]['active'] += 1
                else:
                    analysis['clusters_by_env'][env_name]['stopped'] += 1

                # Group by type
                if workload_type not in analysis['clusters_by_type']:
                    analysis['clusters_by_type'][workload_type] = 0
                analysis['clusters_by_type'][workload_type] += 1

        # Analyze Data Lakes
        if 'datalakes' in self.data.get('datalakes', {}):
            datalakes = self.data['datalakes']['datalakes']
            analysis['total_datalakes'] = len(datalakes)
            analysis['running_datalakes'] = sum(1 for dl in datalakes if dl.get('status') == 'RUNNING')

        # Analyze consumption data (real costs)
        consumption_data = self.data.get('consumption', {})
        records = consumption_data.get('records', [])

        analysis['consumption'] = {
            'total_credits': 0,
            'total_hours': 0,
            'by_cluster': defaultdict(lambda: {'credits': 0, 'hours': 0, 'instances': set(),
                                               'by_hour': defaultdict(float), 'by_day': defaultdict(float)}),
            'by_instance_type': defaultdict(lambda: {'credits': 0, 'hours': 0, 'count': 0}),
            'by_environment': defaultdict(lambda: {'credits': 0, 'hours': 0}),
            'by_date': defaultdict(lambda: {'credits': 0, 'hours': 0}),
            'by_cluster_and_date': defaultdict(lambda: defaultdict(float)),  # For stacked chart
            'by_hour_of_day': defaultdict(float),  # Total credits by hour (0-23)
            'by_day_of_week': defaultdict(float),  # Total credits by day (0-6, Mon-Sun)
            'period_days': 30,
            'from_date': consumption_data.get('from_date', 'N/A'),
            'to_date': consumption_data.get('to_date', 'N/A'),
            'has_data': len(records) > 0
        }

        for record in records:
            credits = record.get('grossCharge', 0)
            # Use 'quantity' which is the total billable hours (hours * instanceCount)
            # NOT 'hours' which is per-instance hours
            hours = record.get('quantity', 0)
            cluster_name = record.get('clusterName', 'Unknown')
            instance_type = record.get('instanceType', 'Unknown')
            env_name = record.get('environmentName', 'Unknown')
            usage_start = record.get('usageStartTimestamp', '')

            # Extract date from timestamp (YYYY-MM-DD)
            date_key = usage_start[:10] if usage_start else 'Unknown'

            # Extract hour and day of week from timestamp
            try:
                if usage_start:
                    timestamp = datetime.fromisoformat(usage_start.replace('Z', '+00:00'))
                    hour_of_day = timestamp.hour
                    day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
                else:
                    hour_of_day = None
                    day_of_week = None
            except:
                hour_of_day = None
                day_of_week = None

            analysis['consumption']['total_credits'] += credits
            analysis['consumption']['total_hours'] += hours

            # By cluster
            analysis['consumption']['by_cluster'][cluster_name]['credits'] += credits
            analysis['consumption']['by_cluster'][cluster_name]['hours'] += hours
            analysis['consumption']['by_cluster'][cluster_name]['instances'].add(instance_type)

            # By hour and day for this cluster
            if hour_of_day is not None:
                analysis['consumption']['by_cluster'][cluster_name]['by_hour'][hour_of_day] += credits
            if day_of_week is not None:
                analysis['consumption']['by_cluster'][cluster_name]['by_day'][day_of_week] += credits

            # By instance type
            analysis['consumption']['by_instance_type'][instance_type]['credits'] += credits
            analysis['consumption']['by_instance_type'][instance_type]['hours'] += hours
            analysis['consumption']['by_instance_type'][instance_type]['count'] += 1

            # By environment
            analysis['consumption']['by_environment'][env_name]['credits'] += credits
            analysis['consumption']['by_environment'][env_name]['hours'] += hours

            # By date (for trends)
            analysis['consumption']['by_date'][date_key]['credits'] += credits
            analysis['consumption']['by_date'][date_key]['hours'] += hours

            # By cluster and date (for stacked chart)
            analysis['consumption']['by_cluster_and_date'][date_key][cluster_name] += credits

            # By hour of day (aggregated for all clusters)
            if hour_of_day is not None:
                analysis['consumption']['by_hour_of_day'][hour_of_day] += credits

            # By day of week (aggregated for all clusters)
            if day_of_week is not None:
                analysis['consumption']['by_day_of_week'][day_of_week] += credits

        # Cost estimate: use real data if available, otherwise use simplified estimate
        if analysis['consumption']['has_data']:
            # Project monthly cost based on actual consumption
            days_in_period = analysis['consumption']['period_days']
            analysis['cost_estimate'] = (analysis['consumption']['total_credits'] / days_in_period) * 30
            analysis['cost_source'] = 'real'
        else:
            # Fallback to simplified estimate
            analysis['cost_estimate'] = analysis['active_nodes'] * 0.50 * 730
            analysis['cost_source'] = 'estimated'

        # Generate savings recommendations
        analysis['recommendations'] = self.generate_recommendations(analysis, clusters)

        return analysis

    def generate_recommendations(self, analysis, clusters):
        """Generate detailed savings recommendations based on usage patterns"""
        recommendations = []

        # Recommendation 1: Stopped clusters that could be deleted
        stopped_clusters = [c for c in clusters if c.get('status') == 'STOPPED']
        if stopped_clusters:
            potential_savings = len(stopped_clusters) * 5 * 730  # Approximate savings
            recommendations.append({
                'title': 'Clusters Detenidos',
                'severity': 'medium',
                'savings': potential_savings,
                'description': f'Tienes {len(stopped_clusters)} cluster(s) detenido(s). Si no los necesitas, considera eliminarlos para evitar costos de almacenamiento.',
                'clusters': [c.get('clusterName') for c in stopped_clusters],
                'action': 'Revisar y eliminar clusters que ya no se necesitan'
            })

        # Recommendation 2: High consumption clusters
        if analysis['consumption']['has_data']:
            # Find clusters with high consumption
            high_consumption = [(name, data['credits']) for name, data in
                              analysis['consumption']['by_cluster'].items()
                              if data['credits'] > analysis['consumption']['total_credits'] * 0.2]

            if high_consumption:
                total_high = sum(c[1] for c in high_consumption)
                recommendations.append({
                    'title': 'Clusters de Alto Consumo',
                    'severity': 'high',
                    'savings': total_high * 0.15,  # Potential 15% savings through optimization
                    'description': f'{len(high_consumption)} cluster(s) representan más del 20% del consumo total cada uno.',
                    'clusters': [c[0] for c in high_consumption],
                    'action': 'Revisar configuración de instancias, considerar auto-scaling o reducción de nodos'
                })

            # Recommendation 3: Expensive instance types
            expensive_instances = sorted(
                [(itype, data['credits']) for itype, data in analysis['consumption']['by_instance_type'].items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]

            if expensive_instances:
                total_expensive = sum(i[1] for i in expensive_instances)
                recommendations.append({
                    'title': 'Tipos de Instancia Costosos',
                    'severity': 'medium',
                    'savings': total_expensive * 0.20,  # Potential 20% savings
                    'description': f'Los 3 tipos de instancia más costosos representan {(total_expensive/analysis["consumption"]["total_credits"]*100):.1f}% del gasto.',
                    'instances': [i[0] for i in expensive_instances],
                    'action': 'Evaluar si se pueden usar tipos de instancia más económicos sin afectar rendimiento'
                })

            # Recommendation 4: Low utilization analysis (based on hours vs potential)
            for cluster_name, cluster_data in analysis['consumption']['by_cluster'].items():
                cluster_info = next((c for c in clusters if c.get('clusterName') == cluster_name), None)
                if cluster_info and cluster_info.get('status') == 'AVAILABLE':
                    node_count = cluster_info.get('nodeCount', 1)
                    # Calculate potential hours (30 days * 24 hours * nodes)
                    potential_hours = 30 * 24 * node_count
                    actual_hours = cluster_data['hours']
                    utilization = (actual_hours / potential_hours * 100) if potential_hours > 0 else 0

                    if utilization < 30:  # Less than 30% utilization
                        potential_savings = cluster_data['credits'] * 0.5
                        recommendations.append({
                            'title': f'Baja Utilización: {cluster_name}',
                            'severity': 'low',
                            'savings': potential_savings,
                            'description': f'Utilización estimada: {utilization:.1f}%. El cluster está infrautilizado.',
                            'clusters': [cluster_name],
                            'action': 'Considerar apagar en horarios no productivos o reducir número de nodos'
                        })

        # Recommendation 5: Consider autoscaling
        active_clusters_count = analysis.get('active_clusters', 0)
        if active_clusters_count > 3:
            recommendations.append({
                'title': 'Considerar Auto-scaling',
                'severity': 'low',
                'savings': analysis['cost_estimate'] * 0.10,  # Potential 10% savings
                'description': f'Tienes {active_clusters_count} clusters activos. El auto-scaling puede ayudar a reducir costos.',
                'clusters': [],
                'action': 'Implementar políticas de auto-scaling para ajustar capacidad según demanda'
            })

        # Sort by potential savings
        recommendations.sort(key=lambda x: x.get('savings', 0), reverse=True)

        return recommendations

    def generate_html(self, output_file='cdp_dashboard.html'):
        """Generate HTML dashboard"""
        analysis = self.analyze_data()
        clusters = self.data.get('datahubs', {}).get('clusters', [])
        datalakes = self.data.get('datalakes', {}).get('datalakes', [])
        user_info = self.data.get('user', {}).get('user', {})

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDP Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #FF7900 0%, #000000 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        h1 {{
            color: #000000;
            font-size: 2.2em;
        }}

        .subtitle {{
            color: #666;
            font-size: 1.0em;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0,0,0,0.15);
        }}

        .card-title {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .card-value {{
            color: #333;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .card-subtitle {{
            color: #999;
            font-size: 0.9em;
        }}

        .status-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
        }}

        .status-running {{
            background: #d4edda;
            color: #155724;
        }}

        .status-stopped {{
            background: #f8d7da;
            color: #721c24;
        }}

        .status-available {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .cluster-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        .cluster-table th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }}

        .cluster-table td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }}

        .cluster-table tr:hover {{
            background: #f8f9fa;
        }}

        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #FF7900 0%, #FF5500 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }}

        .chart-container {{
            margin-top: 20px;
        }}

        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .bar {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .bar-label {{
            min-width: 150px;
            font-size: 0.9em;
            color: #666;
        }}

        .bar-fill {{
            flex: 1;
            height: 30px;
            background: #e9ecef;
            border-radius: 5px;
            overflow: hidden;
        }}

        .bar-inner {{
            height: 100%;
            background: linear-gradient(90deg, #FF7900 0%, #FF5500 100%);
            display: flex;
            align-items: center;
            padding-left: 10px;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
        }}

        .cost-card {{
            background: linear-gradient(135deg, #FF7900 0%, #000000 100%);
            color: white;
            border: 2px solid #FF7900;
        }}

        .cost-card .card-title,
        .cost-card .card-subtitle {{
            color: rgba(255,255,255,0.95);
        }}

        .cost-card .card-value {{
            color: white;
        }}

        .timestamp {{
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 0.9em;
        }}

        .section {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        h2 {{
            color: #000000;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-left: 4px solid #FF7900;
            padding-left: 15px;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <div style="display: flex; align-items: center; gap: 30px; margin-bottom: 10px;">
                {f'<img src="{self.logo_base64}" alt="MasOrange Logo" style="height: 60px;">' if self.logo_base64 else ''}
                <div style="flex: 1;">
                    <h1 style="margin: 0;">Cloudera GCP Dashboard</h1>
                    <p class="subtitle" style="margin: 5px 0 0 0;">Cloudera Data Platform on Google Cloud Platform</p>
                </div>
            </div>
        </header>

        <!-- Métricas principales -->
        <div class="grid">
            <div class="card">
                <div class="card-title">Total Clusters</div>
                <div class="card-value">{analysis['total_clusters']}</div>
                <div class="card-subtitle">Data Hubs desplegados</div>
            </div>

            <div class="card">
                <div class="card-title">Clusters Activos</div>
                <div class="card-value" style="color: #28a745;">{analysis['active_clusters']}</div>
                <div class="card-subtitle">{analysis['stopped_clusters']} detenidos</div>
            </div>

            <div class="card">
                <div class="card-title">Nodos Totales</div>
                <div class="card-value">{analysis['total_nodes']}</div>
                <div class="card-subtitle">{analysis['active_nodes']} nodos activos</div>
            </div>

            <div class="card cost-card">
                <div class="card-title">{'Consumo Mensual' if analysis.get('cost_source') == 'real' else 'Estimación de Costo'}</div>
                <div class="card-value">{analysis['cost_estimate']:,.2f}</div>
                <div class="card-subtitle">{'Créditos CDP/mes (datos reales)' if analysis.get('cost_source') == 'real' else 'Créditos/mes (estimado)'}</div>
            </div>
        </div>

        <!-- Consumption Summary (if real data available) -->
        {f"""
        <div class="section" style="background: linear-gradient(135deg, #FFF5E6 0%, #FFFFFF 100%); border-left: 4px solid #FF7900;">
            <h2>💳 Resumen de Consumo Real (Últimos {analysis['consumption']['period_days']} días)</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Total Créditos Consumidos</div>
                    <div class="card-value" style="color: #FF7900;">{analysis['consumption']['total_credits']:,.2f}</div>
                    <div class="card-subtitle">Período: {analysis['consumption']['from_date'][:10]} a {analysis['consumption']['to_date'][:10]}</div>
                </div>

                <div class="card">
                    <div class="card-title">Total Horas de Computación</div>
                    <div class="card-value" style="color: #000000;">{analysis['consumption']['total_hours']:,.1f}</div>
                    <div class="card-subtitle">Horas de instancias activas</div>
                </div>

                <div class="card">
                    <div class="card-title">Costo Promedio por Hora</div>
                    <div class="card-value" style="color: #FF7900;">{(analysis['consumption']['total_credits'] / analysis['consumption']['total_hours']) if analysis['consumption']['total_hours'] > 0 else 0:.3f}</div>
                    <div class="card-subtitle">Créditos/hora</div>
                </div>

                <div class="card">
                    <div class="card-title">Proyección Mensual</div>
                    <div class="card-value" style="color: #000000;">{analysis['cost_estimate']:,.2f}</div>
                    <div class="card-subtitle">Créditos CDP (basado en uso real)</div>
                </div>
            </div>
        </div>

        <!-- Tendencias de Consumo -->
        <div class="section">
            <h2>📈 Tendencias de Consumo Diario</h2>
            <canvas id="consumptionTrendsChart" style="max-height: 400px;"></canvas>
        </div>

        <!-- Gasto Diario de Créditos -->
        <div class="section">
            <h2>💳 Gasto Diario de Créditos CDP</h2>
            <p style="color: #666; margin-bottom: 20px;">
                Visualización del gasto diario para identificar picos de consumo y patrones de uso.
            </p>
            <canvas id="dailyCreditsChart" style="max-height: 400px;"></canvas>
        </div>

        <!-- Consumo por Cluster a lo Largo del Tiempo -->
        <div class="section">
            <h2>📊 Consumo por Cluster (Evolución Temporal)</h2>
            <p style="color: #666; margin-bottom: 20px;">
                Distribución del gasto entre clusters para identificar cuáles consumen más en cada período.
            </p>
            <canvas id="clusterStackedChart" style="max-height: 450px;"></canvas>
        </div>

        <!-- Distribución Porcentual por Data Hub -->
        <div class="section">
            <h2>⏱️ Distribución de Tiempo de Uso por Data Hub</h2>
            <p style="color: #666; margin-bottom: 20px;">
                Porcentaje de horas de computación utilizadas por cada Data Hub. Muestra qué clusters están más activos.
            </p>
            <div style="max-width: 600px; margin: 0 auto;">
                <canvas id="clusterPieChart"></canvas>
            </div>
            <div style="margin-top: 30px; background: #FFF5E6; padding: 20px; border-radius: 10px; border-left: 4px solid #FF7900;">
                <h3 style="color: #000; margin-bottom: 15px;">💡 Análisis de Utilización</h3>
                <div id="pieChartInsights" style="color: #333; line-height: 1.8;"></div>
            </div>
        </div>

        <!-- Patrones de Uso por Franjas Horarias -->
        <div class="section">
            <h2>🕐 Patrones de Consumo por Franja Horaria (bloques de 4h)</h2>
            <p style="color: #666; margin-bottom: 20px;">
                CDP reporta el consumo en franjas de 4 horas. Este gráfico muestra el consumo agregado de los últimos 30 días por franja.
            </p>
            <canvas id="hourlyPatternChart" style="max-height: 400px;"></canvas>
            <div style="margin-top: 30px; background: #FFF5E6; padding: 20px; border-radius: 10px; border-left: 4px solid #FF7900;">
                <h3 style="color: #000; margin-bottom: 15px;">📊 Análisis de Franjas Horarias</h3>
                <div id="hourlyInsights" style="color: #333; line-height: 1.8;"></div>
            </div>
        </div>

        <!-- Patrones de Uso por Día de la Semana -->
        <div class="section">
            <h2>📅 Patrones de Consumo por Día de la Semana</h2>
            <p style="color: #666; margin-bottom: 20px;">
                Compara el consumo entre días laborables y fines de semana. Identifica oportunidades de ahorro.
            </p>
            <canvas id="weeklyPatternChart" style="max-height: 400px;"></canvas>
            <div style="margin-top: 30px; background: #FFF5E6; padding: 20px; border-radius: 10px; border-left: 4px solid #FF7900;">
                <h3 style="color: #000; margin-bottom: 15px;">📊 Análisis Semanal</h3>
                <div id="weeklyInsights" style="color: #333; line-height: 1.8;"></div>
            </div>
        </div>

        <!-- Análisis Detallado de Infrautilización por Cluster -->
        <div class="section" style="background: #FFF5E6; border: 2px solid #FF7900;">
            <h2>🔍 Análisis de Infrautilización por Franjas Horarias</h2>
            <p style="color: #666; margin-bottom: 20px;">
                Detalle de patrones de uso por cluster para identificar oportunidades específicas de optimización.
            </p>
            <div id="underutilizationAnalysis"></div>
        </div>
        """ if analysis['consumption']['has_data'] else ''}


        <!-- Data Lakes -->
        <div class="section">
            <h2>🏞️ Data Lakes ({analysis['total_datalakes']})</h2>
            <table class="cluster-table">
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Estado</th>
                        <th>Entorno</th>
                        <th>Fecha Creación</th>
                        <th>Ranger RAZ</th>
                        <th>Certificado</th>
                    </tr>
                </thead>
                <tbody>
"""

        for dl in datalakes:
            status = dl.get('status', 'UNKNOWN')
            status_class = 'status-running' if status == 'RUNNING' else 'status-stopped'
            html += f"""
                    <tr>
                        <td><strong>{dl.get('datalakeName', 'N/A')}</strong></td>
                        <td><span class="status-badge {status_class}">{status}</span></td>
                        <td>{dl.get('environmentCrn', '').split('/')[-1] if dl.get('environmentCrn') else 'N/A'}</td>
                        <td>{dl.get('creationDate', 'N/A')[:10]}</td>
                        <td>{'✓ Sí' if dl.get('enableRangerRaz') else '✗ No'}</td>
                        <td>{dl.get('certificateExpirationState', 'N/A')}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>

        <!-- Distribución por Entorno -->
        <div class="section">
            <h2>🌍 Distribución por Entorno</h2>
            <div class="chart-container">
                <div class="bar-chart">
"""

        for env_name, env_data in analysis['clusters_by_env'].items():
            percentage = (env_data['total'] / analysis['total_clusters'] * 100) if analysis['total_clusters'] > 0 else 0
            html += f"""
                    <div class="bar">
                        <div class="bar-label">{env_name}</div>
                        <div class="bar-fill">
                            <div class="bar-inner" style="width: {percentage}%;">
                                {env_data['total']} clusters ({env_data['active']} activos)
                            </div>
                        </div>
                    </div>
"""

        html += """
                </div>
            </div>
        </div>

        <!-- Detalles de Clusters -->
        <div class="section">
            <h2>🔧 Data Hub Clusters</h2>
            <table class="cluster-table">
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Estado</th>
                        <th>Tipo</th>
                        <th>Entorno</th>
                        <th>Nodos</th>
                        <th>Plataforma</th>
                        <th>Fecha Creación</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Sort clusters by status (AVAILABLE first, then STOPPED)
        sorted_clusters = sorted(clusters, key=lambda x: (x.get('status') != 'AVAILABLE', x.get('clusterName', '')))

        for cluster in sorted_clusters:
            status = cluster.get('status', 'UNKNOWN')
            status_class = 'status-available' if status == 'AVAILABLE' else 'status-stopped'
            html += f"""
                    <tr>
                        <td><strong>{cluster.get('clusterName', 'N/A')}</strong></td>
                        <td><span class="status-badge {status_class}">{status}</span></td>
                        <td>{cluster.get('workloadType', 'N/A')}</td>
                        <td>{cluster.get('environmentName', 'N/A')}</td>
                        <td><strong>{cluster.get('nodeCount', 0)}</strong> nodos</td>
                        <td>{cluster.get('cloudPlatform', 'N/A')}</td>
                        <td>{cluster.get('creationDate', 'N/A')[:10]}</td>
                    </tr>
"""

        html += f"""
                </tbody>
            </table>
        </div>

        <!-- Consumption by Cluster (if real data available) -->
        {'''
        <div class="section">
            <h2>📊 Consumo por Cluster (Últimos ''' + str(analysis['consumption']['period_days']) + ''' días)</h2>
            <table class="cluster-table">
                <thead>
                    <tr>
                        <th>Cluster</th>
                        <th>Créditos Consumidos</th>
                        <th>Horas de Computación</th>
                        <th>Costo/Hora Promedio</th>
                        <th>% del Total</th>
                    </tr>
                </thead>
                <tbody>
''' + ''.join([f'''
                    <tr>
                        <td><strong>{cluster_name}</strong></td>
                        <td>{data["credits"]:,.2f} créditos</td>
                        <td>{data["hours"]:,.1f} horas</td>
                        <td>{(data["credits"]/data["hours"]) if data["hours"] > 0 else 0:.3f}</td>
                        <td>{(data["credits"]/analysis["consumption"]["total_credits"]*100) if analysis["consumption"]["total_credits"] > 0 else 0:.1f}%</td>
                    </tr>
''' for cluster_name, data in sorted(analysis['consumption']['by_cluster'].items(), key=lambda x: x[1]['credits'], reverse=True)]) + '''
                </tbody>
            </table>
        </div>

        <!-- Consumption by Instance Type (if real data available) -->
        <div class="section">
            <h2>🖥️ Consumo por Tipo de Instancia</h2>
            <div class="chart-container">
                <div class="bar-chart">
''' + ''.join([f'''
                    <div class="bar">
                        <div class="bar-label"><strong>{instance_type}</strong></div>
                        <div class="bar-fill">
                            <div class="bar-inner" style="width: {(data["credits"]/analysis["consumption"]["total_credits"]*100) if analysis["consumption"]["total_credits"] > 0 else 0}%;">
                                {data["credits"]:,.1f} créditos ({data["hours"]:,.0f}h)
                            </div>
                        </div>
                    </div>
''' for instance_type, data in sorted(analysis['consumption']['by_instance_type'].items(), key=lambda x: x[1]['credits'], reverse=True)[:10]]) + '''
                </div>
            </div>
        </div>
        ''' if analysis['consumption']['has_data'] else ''}

        <!-- Análisis de Costos -->
        <div class="section">
            <h2>💰 Análisis de Costos</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Nodos Activos</div>
                    <div class="card-value">{analysis['active_nodes']}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {(analysis['active_nodes']/analysis['total_nodes']*100) if analysis['total_nodes'] > 0 else 0}%">
                            {(analysis['active_nodes']/analysis['total_nodes']*100) if analysis['total_nodes'] > 0 else 0:.1f}% utilización
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">Estimación Mensual</div>
                    <div class="card-value" style="color: #FF7900;">${analysis['cost_estimate']:,.2f}</div>
                    <div class="card-subtitle">Basado en datos reales de consumo</div>
                </div>

                <div class="card">
                    <div class="card-title">Potencial Ahorro</div>
                    <div class="card-value" style="color: #28a745;">${analysis['stopped_clusters'] * 5 * 730:,.2f}</div>
                    <div class="card-subtitle">Clusters detenidos ({analysis['stopped_clusters']})</div>
                </div>
            </div>

            <p style="color: #666; font-size: 0.9em; margin-top: 20px;">
                <strong>Nota:</strong> Los costos son estimaciones aproximadas. Los costos reales pueden variar según el tipo de instancia,
                región, y servicios adicionales utilizados. Consulta tu factura de GCP para costos precisos.
            </p>
        </div>

        <!-- Recommendations Section -->
        <div class="section" style="background: #FFF5E6; border: 2px solid #FF7900;">
            <h2>💡 Recomendaciones de Ahorro</h2>
            <p style="margin-bottom: 20px; color: #666;">
                Basado en el análisis de consumo, hemos identificado las siguientes oportunidades de optimización:
            </p>

"""
        # Generate recommendations HTML
        recommendations_html = ""
        for rec in analysis.get('recommendations', []):
            severity = rec.get("severity", "low")
            border_color = "#dc3545" if severity == "high" else "#FF7900" if severity == "medium" else "#28a745"
            emoji = "🔴" if severity == "high" else "🟠" if severity == "medium" else "🟢"

            clusters_html = ""
            if rec.get("clusters"):
                clusters_html = f'''
                <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>Clusters afectados:</strong><br>
                    {", ".join(rec.get("clusters", []))}
                </div>
                '''

            instances_html = ""
            if rec.get("instances"):
                instances_html = f'''
                <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>Tipos de instancia:</strong><br>
                    {", ".join(rec.get("instances", []))}
                </div>
                '''

            recommendations_html += f'''
            <div class="card" style="margin-bottom: 15px; border-left: 4px solid {border_color};">
                <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 10px;">
                    <div style="flex: 1;">
                        <h3 style="color: #000; margin-bottom: 5px; font-size: 1.2em;">
                            {emoji}
                            {rec.get("title", "")}
                        </h3>
                        <div style="color: #FF7900; font-weight: bold; font-size: 1.1em; margin-bottom: 10px;">
                            Ahorro potencial: {rec.get("savings", 0):,.2f} créditos/mes
                        </div>
                    </div>
                </div>
                <p style="color: #333; margin-bottom: 10px; line-height: 1.6;">
                    {rec.get("description", "")}
                </p>
                {clusters_html}
                {instances_html}
                <div style="background: #FF7900; color: white; padding: 10px; border-radius: 5px; font-weight: 500;">
                    <strong>⚡ Acción recomendada:</strong> {rec.get("action", "")}
                </div>
            </div>
            '''

        total_savings = sum(rec.get('savings', 0) for rec in analysis.get('recommendations', []))

        html += recommendations_html + f"""
            <div style="background: #000; color: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <h3 style="color: #FF7900; margin-bottom: 10px;">📊 Resumen de Ahorro Total</h3>
                <div style="font-size: 2em; font-weight: bold;">
                    {total_savings:,.2f} créditos/mes
                </div>
                <p style="margin-top: 10px; color: #ddd;">
                    Implementando estas recomendaciones podrías reducir tu gasto mensual significativamente.
                </p>
            </div>
        </div>

        <div class="timestamp">
            📅 Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}
        </div>
    </div>

    <script>
        console.log('=== CDP Dashboard JavaScript Starting ===');

        // Prepare data for consumption trends chart
        const consumptionByDate = {json.dumps(dict(sorted(analysis['consumption']['by_date'].items()))) if analysis['consumption']['has_data'] else '{}'};
        console.log('consumptionByDate loaded:', Object.keys(consumptionByDate).length, 'days');

        if (Object.keys(consumptionByDate).length > 0) {{
            const dates = Object.keys(consumptionByDate).sort();
            const credits = dates.map(date => consumptionByDate[date].credits);
            const hours = dates.map(date => consumptionByDate[date].hours);

            // Consumption Trends Line Chart
            try {{
                console.log('Creating consumptionTrendsChart...');
                const ctx = document.getElementById('consumptionTrendsChart');
                if (!ctx) throw new Error('Element consumptionTrendsChart not found');
                new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: dates,
                    datasets: [
                        {{
                            label: 'Créditos Consumidos',
                            data: credits,
                            borderColor: '#FF7900',
                            backgroundColor: 'rgba(255, 121, 0, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y'
                        }},
                        {{
                            label: 'Horas de Computación',
                            data: hours,
                            borderColor: '#000000',
                            backgroundColor: 'rgba(0, 0, 0, 0.05)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y1'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top'
                        }},
                        title: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {{
                                display: true,
                                text: 'Créditos CDP',
                                color: '#FF7900',
                                font: {{
                                    weight: 'bold'
                                }}
                            }},
                            ticks: {{
                                color: '#FF7900'
                            }}
                        }},
                        y1: {{
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {{
                                display: true,
                                text: 'Horas de Computación',
                                color: '#000000',
                                font: {{
                                    weight: 'bold'
                                }}
                            }},
                            ticks: {{
                                color: '#000000'
                            }},
                            grid: {{
                                drawOnChartArea: false
                            }}
                        }}
                    }}
                }}
            }});
                console.log('✓ consumptionTrendsChart created');
            }} catch(e) {{
                console.error('✗ Error creating consumptionTrendsChart:', e);
            }}

            // Daily Credits Bar Chart
            try {{
                console.log('Creating dailyCreditsChart...');
            const ctx2 = document.getElementById('dailyCreditsChart');
            new Chart(ctx2, {{
                type: 'bar',
                data: {{
                    labels: dates,
                    datasets: [{{
                        label: 'Créditos Consumidos',
                        data: credits,
                        backgroundColor: 'rgba(255, 121, 0, 0.7)',
                        borderColor: '#FF7900',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return 'Créditos: ' + context.parsed.y.toFixed(2);
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Créditos CDP',
                                color: '#FF7900',
                                font: {{
                                    weight: 'bold',
                                    size: 14
                                }}
                            }},
                            ticks: {{
                                color: '#000'
                            }},
                            grid: {{
                                color: 'rgba(0, 0, 0, 0.05)'
                            }}
                        }},
                        x: {{
                            ticks: {{
                                color: '#000'
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }}
                }}
            }});
                console.log('✓ dailyCreditsChart created');
            }} catch(e) {{
                console.error('✗ Error creating dailyCreditsChart:', e);
            }}

            // Stacked Bar Chart by Cluster
            try {{
                console.log('Creating clusterStackedChart...');
            const clusterData = {json.dumps(dict(sorted(analysis['consumption']['by_cluster_and_date'].items())))};
            const allClusters = [...new Set(Object.values(clusterData).flatMap(Object.keys))];

            // Define colors for each cluster (using Orange palette)
            const clusterColors = {{
                0: {{ bg: 'rgba(255, 121, 0, 0.8)', border: '#FF7900' }},
                1: {{ bg: 'rgba(0, 0, 0, 0.7)', border: '#000000' }},
                2: {{ bg: 'rgba(255, 165, 0, 0.7)', border: '#FFA500' }},
                3: {{ bg: 'rgba(128, 64, 0, 0.7)', border: '#804000' }},
                4: {{ bg: 'rgba(255, 200, 100, 0.7)', border: '#FFC864' }},
                5: {{ bg: 'rgba(64, 64, 64, 0.7)', border: '#404040' }},
                6: {{ bg: 'rgba(255, 100, 0, 0.7)', border: '#FF6400' }}
            }};

            const datasets = allClusters.map((cluster, idx) => ({{
                label: cluster,
                data: dates.map(date => clusterData[date]?.[cluster] || 0),
                backgroundColor: clusterColors[idx % 7].bg,
                borderColor: clusterColors[idx % 7].border,
                borderWidth: 1
            }}));

            const ctx3 = document.getElementById('clusterStackedChart');
            new Chart(ctx3, {{
                type: 'bar',
                data: {{
                    labels: dates,
                    datasets: datasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top',
                            labels: {{
                                color: '#000',
                                font: {{
                                    size: 11
                                }}
                            }}
                        }},
                        tooltip: {{
                            mode: 'index',
                            callbacks: {{
                                footer: function(tooltipItems) {{
                                    let total = 0;
                                    tooltipItems.forEach(item => {{
                                        total += item.parsed.y;
                                    }});
                                    return 'Total: ' + total.toFixed(2) + ' créditos';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            stacked: true,
                            ticks: {{
                                color: '#000'
                            }},
                            grid: {{
                                display: false
                            }}
                        }},
                        y: {{
                            stacked: true,
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Créditos CDP',
                                color: '#FF7900',
                                font: {{
                                    weight: 'bold',
                                    size: 14
                                }}
                            }},
                            ticks: {{
                                color: '#000'
                            }},
                            grid: {{
                                color: 'rgba(0, 0, 0, 0.05)'
                            }}
                        }}
                    }}
                }}
            }});
                console.log('✓ clusterStackedChart created');
            }} catch(e) {{
                console.error('✗ Error creating clusterStackedChart:', e);
            }}

            // Pie Chart - Usage Hours by Cluster
            try {{
                console.log('Creating clusterPieChart...');
            const clusterUsageHours = {json.dumps({k: v['hours'] for k, v in analysis['consumption']['by_cluster'].items()})};
            const clusterNames = Object.keys(clusterUsageHours);
            const clusterValues = Object.values(clusterUsageHours);
            const totalHours = clusterValues.reduce((a, b) => a + b, 0);

            // Generate dynamic colors for pie chart (Orange palette)
            const pieColors = [
                '#FF7900',  // Orange primary
                '#000000',  // Black
                '#FFA500',  // Light orange
                '#FF6400',  // Dark orange
                '#FFC864',  // Golden
                '#804000',  // Brown
                '#404040',  // Dark grey
                '#FF8C00',  // Dark orange 2
                '#FFB347',  // Pastel orange
                '#CC5500'   // Burnt orange
            ];

            const ctx4 = document.getElementById('clusterPieChart');
            new Chart(ctx4, {{
                type: 'doughnut',  // Using doughnut for modern look
                data: {{
                    labels: clusterNames,
                    datasets: [{{
                        data: clusterValues,
                        backgroundColor: pieColors.slice(0, clusterNames.length),
                        borderColor: '#FFFFFF',
                        borderWidth: 3
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'bottom',
                            labels: {{
                                color: '#000',
                                font: {{
                                    size: 12,
                                    weight: '500'
                                }},
                                padding: 15,
                                generateLabels: function(chart) {{
                                    const data = chart.data;
                                    return data.labels.map((label, i) => {{
                                        const value = data.datasets[0].data[i];
                                        const percentage = ((value / totalHours) * 100).toFixed(1);
                                        return {{
                                            text: `${{label}}: ${{percentage}}%`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            hidden: false,
                                            index: i
                                        }};
                                    }});
                                }}
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const percentage = ((value / totalHours) * 100).toFixed(1);
                                    return `${{label}}: ${{value.toFixed(1)}} horas (${{percentage}}%)`;
                                }}
                            }}
                        }}
                    }}
                }}
            }});

            // Generate insights for pie chart
            const sortedClusters = clusterNames
                .map((name, idx) => ({{ name, value: clusterValues[idx], percentage: (clusterValues[idx] / totalHours * 100).toFixed(1) }}))
                .sort((a, b) => b.value - a.value);

            let insightsHTML = '<ul style="margin: 0; padding-left: 20px;">';
            insightsHTML += `<li><strong>${{sortedClusters[0].name}}</strong> es el cluster más utilizado, consumiendo el <strong style="color: #FF7900;">${{sortedClusters[0].percentage}}%</strong> del tiempo total de computación (<strong>${{sortedClusters[0].value.toFixed(1)}} horas</strong>).</li>`;

            if (sortedClusters.length > 1) {{
                const top3 = sortedClusters.slice(0, 3);
                const top3Total = top3.reduce((sum, c) => sum + parseFloat(c.percentage), 0).toFixed(1);
                const top3Hours = top3.reduce((sum, c) => sum + parseFloat(c.value), 0).toFixed(1);
                insightsHTML += `<li>Los 3 clusters más activos (<strong>${{top3.map(c => c.name).join(', ')}}</strong>) representan el <strong style="color: #FF7900;">${{top3Total}}%</strong> del tiempo de uso (<strong>${{top3Hours}} horas</strong>).</li>`;
            }}

            if (sortedClusters.length > 3) {{
                const others = sortedClusters.slice(3);
                const othersTotal = others.reduce((sum, c) => sum + parseFloat(c.percentage), 0).toFixed(1);
                const othersHours = others.reduce((sum, c) => sum + parseFloat(c.value), 0).toFixed(1);
                insightsHTML += `<li>Los ${{others.length}} clusters restantes representan solo el <strong>${{othersTotal}}%</strong> del tiempo de uso (<strong>${{othersHours}} horas</strong>).</li>`;
            }}

            insightsHTML += '</ul>';
            document.getElementById('pieChartInsights').innerHTML = insightsHTML;
                console.log('✓ clusterPieChart created');
            }} catch(e) {{
                console.error('✗ Error creating clusterPieChart:', e);
            }}

            // Hourly Pattern Chart (4-hour blocks as reported by CDP)
            try {{
                console.log('Creating hourlyPatternChart...');
            const hourlyData = {json.dumps(dict(sorted(analysis['consumption']['by_hour_of_day'].items())))};
            // CDP reports in 4-hour blocks: 00-04, 04-08, 08-12, 12-16, 16-20, 20-24
            const timeBlocks = [0, 4, 8, 12, 16, 20];
            const blockLabels = ['00:00-04:00', '04:00-08:00', '08:00-12:00', '12:00-16:00', '16:00-20:00', '20:00-00:00'];
            const hourlyCredits = timeBlocks.map(h => hourlyData[h] || 0);
            const totalHourlyCredits = hourlyCredits.reduce((a, b) => a + b, 0);

            const ctx5 = document.getElementById('hourlyPatternChart');
            new Chart(ctx5, {{
                type: 'bar',
                data: {{
                    labels: blockLabels,
                    datasets: [{{
                        label: 'Créditos Consumidos',
                        data: hourlyCredits,
                        backgroundColor: hourlyCredits.map(val => {{
                            const intensity = totalHourlyCredits > 0 ? val / Math.max(...hourlyCredits) : 0;
                            return intensity > 0.7 ? 'rgba(255, 121, 0, 0.9)' :
                                   intensity > 0.4 ? 'rgba(255, 121, 0, 0.6)' :
                                   'rgba(255, 121, 0, 0.3)';
                        }}),
                        borderColor: '#FF7900',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const percentage = totalHourlyCredits > 0 ? (context.parsed.y / totalHourlyCredits * 100).toFixed(1) : 0;
                                    return `Créditos: ${{context.parsed.y.toFixed(2)}} (${{percentage}}%)`;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Créditos CDP',
                                color: '#FF7900',
                                font: {{
                                    weight: 'bold',
                                    size: 14
                                }}
                            }},
                            ticks: {{
                                color: '#000'
                            }},
                            grid: {{
                                color: 'rgba(0, 0, 0, 0.05)'
                            }}
                        }},
                        x: {{
                            ticks: {{
                                color: '#000',
                                font: {{
                                    size: 10
                                }}
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }}
                }}
            }});

            // Generate insights for 4-hour blocks
            const blockData = timeBlocks.map((hour, idx) => ({{
                label: blockLabels[idx],
                hour: hour,
                credits: hourlyCredits[idx],
                percentage: totalHourlyCredits > 0 ? (hourlyCredits[idx] / totalHourlyCredits * 100) : 0
            }})).filter(b => b.credits > 0).sort((a, b) => b.credits - a.credits);

            const peakBlock = blockData[0];

            // Business hours blocks (08:00-20:00): blocks starting at 8, 12, 16
            const businessBlocks = blockData.filter(b => b.hour >= 8 && b.hour < 20);
            const businessCredits = businessBlocks.reduce((sum, b) => sum + b.credits, 0);
            const businessPercentage = totalHourlyCredits > 0 ? (businessCredits / totalHourlyCredits * 100).toFixed(1) : 0;

            // Night blocks (20:00-08:00): blocks starting at 20, 0, 4
            const nightBlocks = blockData.filter(b => b.hour === 20 || b.hour === 0 || b.hour === 4);
            const nightCredits = nightBlocks.reduce((sum, b) => sum + b.credits, 0);
            const nightPercentage = totalHourlyCredits > 0 ? (nightCredits / totalHourlyCredits * 100).toFixed(1) : 0;

            let hourlyInsightsHTML = '<ul style="margin: 0; padding-left: 20px;">';
            hourlyInsightsHTML += `<li><strong>ℹ️ Nota:</strong> CDP reporta consumo en franjas de 4 horas. Los datos muestran estas franjas agregadas de los últimos 30 días.</li>`;

            if (peakBlock) {{
                hourlyInsightsHTML += `<li><strong>Franja pico:</strong> ${{peakBlock.label}} con <strong style="color: #FF7900;">${{peakBlock.credits.toFixed(2)}} créditos</strong> (${{peakBlock.percentage.toFixed(1)}}% del total).</li>`;
            }}

            hourlyInsightsHTML += `<li><strong>Horario laboral (08:00-20:00):</strong> <strong style="color: #FF7900;">${{businessPercentage}}%</strong> del consumo (${{businessCredits.toFixed(2)}} créditos).</li>`;

            if (nightCredits > 0) {{
                hourlyInsightsHTML += `<li><strong>⚠️ Uso nocturno (20:00-08:00):</strong> <strong style="color: #dc3545;">${{nightPercentage}}%</strong> del consumo (${{nightCredits.toFixed(2)}} créditos). Evalúa si es necesario mantener clusters activos en estas franjas.</li>`;
            }}

            hourlyInsightsHTML += '</ul>';
            document.getElementById('hourlyInsights').innerHTML = hourlyInsightsHTML;
                console.log('✓ hourlyPatternChart created');
            }} catch(e) {{
                console.error('✗ Error creating hourlyPatternChart:', e);
            }}

            // Weekly Pattern Chart (Mon-Sun)
            try {{
                console.log('Creating weeklyPatternChart...');
            const weeklyData = {json.dumps(dict(sorted(analysis['consumption']['by_day_of_week'].items())))};
            const dayNames = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
            const weeklyCredits = [0, 1, 2, 3, 4, 5, 6].map(d => weeklyData[d] || 0);
            const totalWeeklyCredits = weeklyCredits.reduce((a, b) => a + b, 0);

            const ctx6 = document.getElementById('weeklyPatternChart');
            new Chart(ctx6, {{
                type: 'bar',
                data: {{
                    labels: dayNames,
                    datasets: [{{
                        label: 'Créditos Consumidos',
                        data: weeklyCredits,
                        backgroundColor: weeklyCredits.map((val, idx) => {{
                            // Weekend days (Saturday=5, Sunday=6) in different color
                            return idx >= 5 ? 'rgba(0, 0, 0, 0.7)' : 'rgba(255, 121, 0, 0.8)';
                        }}),
                        borderColor: weeklyCredits.map((val, idx) => idx >= 5 ? '#000000' : '#FF7900'),
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const percentage = totalWeeklyCredits > 0 ? (context.parsed.y / totalWeeklyCredits * 100).toFixed(1) : 0;
                                    return `Créditos: ${{context.parsed.y.toFixed(2)}} (${{percentage}}%)`;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Créditos CDP',
                                color: '#FF7900',
                                font: {{
                                    weight: 'bold',
                                    size: 14
                                }}
                            }},
                            ticks: {{
                                color: '#000'
                            }},
                            grid: {{
                                color: 'rgba(0, 0, 0, 0.05)'
                            }}
                        }},
                        x: {{
                            ticks: {{
                                color: '#000'
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }}
                }}
            }});

            // Generate weekly insights
            const weekdayCredits = weeklyCredits.slice(0, 5).reduce((a, b) => a + b, 0);
            const weekendCredits = weeklyCredits.slice(5).reduce((a, b) => a + b, 0);
            const weekdayPercentage = totalWeeklyCredits > 0 ? (weekdayCredits / totalWeeklyCredits * 100).toFixed(1) : 0;
            const weekendPercentage = totalWeeklyCredits > 0 ? (weekendCredits / totalWeeklyCredits * 100).toFixed(1) : 0;

            const peakDay = dayNames[weeklyCredits.indexOf(Math.max(...weeklyCredits))];
            const peakDayCredits = Math.max(...weeklyCredits);
            const peakDayPercentage = totalWeeklyCredits > 0 ? (peakDayCredits / totalWeeklyCredits * 100).toFixed(1) : 0;

            let weeklyInsightsHTML = '<ul style="margin: 0; padding-left: 20px;">';
            weeklyInsightsHTML += `<li><strong>Día de mayor consumo:</strong> ${{peakDay}} con <strong style="color: #FF7900;">${{peakDayCredits.toFixed(2)}} créditos</strong> (${{peakDayPercentage}}%).</li>`;
            weeklyInsightsHTML += `<li><strong>Días laborables (Lun-Vie):</strong> <strong style="color: #FF7900;">${{weekdayPercentage}}%</strong> del consumo (${{weekdayCredits.toFixed(2)}} créditos).</li>`;

            if (weekendCredits > 0) {{
                weeklyInsightsHTML += `<li><strong>⚠️ Fin de semana (Sáb-Dom):</strong> <strong style="color: #dc3545;">${{weekendPercentage}}%</strong> del consumo (${{weekendCredits.toFixed(2)}} créditos). Evalúa si es necesario mantener clusters activos durante el fin de semana.</li>`;
            }} else {{
                weeklyInsightsHTML += `<li><strong>✅ Fin de semana:</strong> Sin consumo registrado. Excelente optimización!</li>`;
            }}

            weeklyInsightsHTML += '</ul>';
            document.getElementById('weeklyInsights').innerHTML = weeklyInsightsHTML;
                console.log('✓ weeklyPatternChart created');
            }} catch(e) {{
                console.error('✗ Error creating weeklyPatternChart:', e);
            }}

            // Detailed underutilization analysis by cluster
            try {{
                console.log('Creating underutilization analysis...');
            const clusterAnalysis = {json.dumps({name: {'hours': data['hours'], 'credits': data['credits'], 'by_hour': dict(data['by_hour']), 'by_day': dict(data['by_day'])} for name, data in analysis['consumption']['by_cluster'].items()})};

            let underutilHTML = '';

            for (const [clusterName, clusterData] of Object.entries(clusterAnalysis)) {{
                const hourlyData = clusterData.by_hour;
                const dailyData = clusterData.by_day;

                // CDP reports in 4-hour blocks
                const clusterTimeBlocks = [0, 4, 8, 12, 16, 20];
                const clusterBlockLabels = ['00:00-04:00', '04:00-08:00', '08:00-12:00', '12:00-16:00', '16:00-20:00', '20:00-00:00'];
                const clusterBlocks = clusterTimeBlocks.map((h, idx) => ({{
                    hour: h,
                    label: clusterBlockLabels[idx],
                    credits: hourlyData[h] || 0
                }}));

                const clusterTotalCredits = Object.values(hourlyData).reduce((a, b) => a + b, 0);
                const avgBlockCredits = clusterTotalCredits / 6;  // 6 blocks of 4 hours

                // Blocks with less than 20% of average usage
                const lowUsageBlocks = clusterBlocks.filter(b => b.credits < avgBlockCredits * 0.2 && b.credits > 0);

                // Blocks with zero usage
                const zeroUsageBlocks = clusterBlocks.filter(b => b.credits === 0);

                // Night usage (blocks 20:00-00:00, 00:00-04:00, 04:00-08:00)
                const nightBlocks = clusterBlocks.filter(b => b.hour === 20 || b.hour === 0 || b.hour === 4);
                const nightCredits = nightBlocks.reduce((sum, b) => sum + b.credits, 0);

                // Weekend usage
                const weekendCredits = (dailyData[5] || 0) + (dailyData[6] || 0);
                const weekendPercentage = clusterTotalCredits > 0 ? (weekendCredits / clusterTotalCredits * 100).toFixed(1) : 0;

                if (lowUsageBlocks.length > 0 || zeroUsageBlocks.length > 0 || nightCredits > 0 || weekendCredits > 0) {{
                    underutilHTML += `
                    <div class="card" style="margin-bottom: 20px; border-left: 4px solid #FF7900;">
                        <h3 style="color: #000; margin-bottom: 15px; font-size: 1.3em;">
                            🖥️ ${{clusterName}}
                        </h3>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                            <strong>Consumo total:</strong> ${{clusterData.credits.toFixed(2)}} créditos |
                            <strong>Horas totales:</strong> ${{clusterData.hours.toFixed(1)}}h
                        </div>
                        <ul style="margin: 0; padding-left: 20px; line-height: 2;">
                    `;

                    if (zeroUsageBlocks.length > 0) {{
                        const zeroBlockLabels = zeroUsageBlocks.map(b => b.label).join(', ');
                        underutilHTML += `<li><strong>✅ Sin consumo en:</strong> ${{zeroBlockLabels}} (${{zeroUsageBlocks.length}} franjas de 4h)</li>`;
                    }}

                    if (nightCredits > 0) {{
                        const nightPercentage = (nightCredits / clusterTotalCredits * 100).toFixed(1);
                        const nightBlocksWithUsage = nightBlocks.filter(b => b.credits > 0).map(b => b.label).join(', ');
                        underutilHTML += `<li><strong>⚠️ Uso nocturno (20:00-08:00):</strong> ${{nightCredits.toFixed(2)}} créditos (${{nightPercentage}}%) en las franjas: ${{nightBlocksWithUsage}}.</li>`;
                    }}

                    if (weekendCredits > 0) {{
                        underutilHTML += `<li><strong>⚠️ Uso en fin de semana:</strong> ${{weekendCredits.toFixed(2)}} créditos (${{weekendPercentage}}%). Evalúa si es necesario.</li>`;
                    }}

                    if (lowUsageBlocks.length > 0) {{
                        const lowBlockLabels = lowUsageBlocks.map(b => b.label).join(', ');
                        underutilHTML += `<li><strong>Baja utilización en:</strong> ${{lowBlockLabels}} (menos del 20% del promedio).</li>`;
                    }}

                    underutilHTML += `
                        </ul>
                        <div style="background: #FF7900; color: white; padding: 12px; border-radius: 5px; margin-top: 15px; font-weight: 500;">
                            <strong>💡 Recomendación:</strong> `;

                    if (nightCredits > clusterTotalCredits * 0.15) {{
                        underutilHTML += `Implementa schedule para apagar este cluster de 22:00 a 06:00. Ahorro estimado: <strong>${{(nightCredits * 0.7).toFixed(2)}} créditos/mes</strong>.`;
                    }} else if (weekendCredits > clusterTotalCredits * 0.15) {{
                        underutilHTML += `Detén este cluster durante fines de semana. Ahorro estimado: <strong>${{(weekendCredits * 0.7).toFixed(2)}} créditos/mes</strong>.`;
                    }} else {{
                        underutilHTML += `Revisa si este cluster puede reducir nodos o consolidarse con otro cluster.`;
                    }}

                    underutilHTML += `
                        </div>
                    </div>
                    `;
                }}
            }}

            if (underutilHTML === '') {{
                underutilHTML = '<div class="card"><p style="color: #28a745; font-size: 1.1em; text-align: center;"><strong>✅ No se detectaron patrones significativos de infrautilización por franjas horarias.</strong></p></div>';
            }}

            document.getElementById('underutilizationAnalysis').innerHTML = underutilHTML;
                console.log('✓ Underutilization analysis created');
            }} catch(e) {{
                console.error('✗ Error creating underutilization analysis:', e);
            }}

            console.log('=== All charts created successfully ===');
        }}
    </script>
</body>
</html>
"""

        # Write HTML file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"[OK] Dashboard generado exitosamente: {output_path.absolute()}")
        return str(output_path.absolute())

def main():
    """Main function"""
    print("=" * 60)
    print("CDP Dashboard Generator")
    print("=" * 60)
    print()

    dashboard = CDPDashboard()
    dashboard.collect_data()
    output_file = dashboard.generate_html()

    print()
    print("=" * 60)
    print(f"Abre el archivo en tu navegador:")
    print(f"  file:///{output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
