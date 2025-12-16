#!/usr/bin/env python3
"""
CDP to Elasticsearch Ingestion Script
Indexes CDP consumption data into Elasticsearch for Kibana visualization
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import urllib3

# Disable SSL warnings if needed (for self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CDPToElasticsearch:
    def __init__(self,
                 elk_url='gea-data-cloud-masorange-es.es.europe-west1.gcp.cloud.es.io',
                 username='infra_admin',
                 password='imdeveloperS',
                 cdp_cli_path=r"C:\Program Files\Python312\Scripts\cdp.exe"):

        self.cdp_cli = cdp_cli_path

        # Connect to Elasticsearch (Elastic Cloud)
        print(f"Conectando a Elasticsearch: {elk_url}")
        self.es = Elasticsearch(
            [f'https://{elk_url}'],
            basic_auth=(username, password),
            verify_certs=True,  # Elastic Cloud has valid SSL certificates
            request_timeout=30
        )

        # Test connection
        try:
            print("Conectando a Elasticsearch...")
            info = self.es.info()
            print(f"[OK] Conectado a Elasticsearch {info['version']['number']}")
            print(f"     Cluster: {info['cluster_name']}")
        except Exception as e:
            print(f"[ERROR] Error de conexion: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"No se pudo conectar a Elasticsearch: {e}")

        self.index_name_records = 'cdp-consumption-records'
        self.index_name_summary = 'cdp-consumption-summary'

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

    def collect_consumption_data(self, days=30):
        """Collect consumption data for the last N days"""
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=days)

        from_timestamp = from_date.strftime('%Y-%m-%dT00:00:00Z')
        to_timestamp = to_date.strftime('%Y-%m-%dT23:59:59Z')

        print(f"\nObteniendo datos de consumo ({from_timestamp} a {to_timestamp})...")

        try:
            all_records = []
            next_token = None
            max_pages = 100
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

            print(f"[OK] Obtenidos {len(all_records)} registros de consumo")
            return all_records

        except Exception as e:
            print(f"Error obteniendo datos de consumo: {e}")
            return []

    def create_index_templates(self):
        """Create index templates for both indices"""

        # Template for raw consumption records
        records_template = {
            "index_patterns": [f"{self.index_name_records}-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                    "index.codec": "best_compression"
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "ingestion_time": {"type": "date"},
                        "usage_start": {"type": "date"},
                        "usage_end": {"type": "date"},
                        "cluster_name": {"type": "keyword"},
                        "cluster_crn": {"type": "keyword"},
                        "environment_name": {"type": "keyword"},
                        "cloud_provider": {"type": "keyword"},
                        "instance_type": {"type": "keyword"},
                        "instance_count": {"type": "integer"},
                        "hours": {"type": "float"},
                        "quantity": {"type": "float"},
                        "credits": {"type": "float"},
                        "list_rate": {"type": "float"},
                        "cluster_type": {"type": "keyword"},
                        "cluster_template": {"type": "keyword"},
                        "hour_of_day": {"type": "integer"},
                        "day_of_week": {"type": "integer"},
                        "day_of_week_name": {"type": "keyword"},
                        "is_weekend": {"type": "boolean"},
                        "is_night": {"type": "boolean"},
                        "weekend_label": {"type": "keyword"},
                        "time_of_day_label": {"type": "keyword"},
                        "time_block": {"type": "keyword"}
                    }
                }
            }
        }

        # Template for aggregated summary
        summary_template = {
            "index_patterns": [f"{self.index_name_summary}-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "date": {"type": "date"},
                        "cluster_name": {"type": "keyword"},
                        "environment_name": {"type": "keyword"},
                        "total_credits": {"type": "float"},
                        "total_hours": {"type": "float"},
                        "total_quantity": {"type": "float"},
                        "instance_types": {"type": "keyword"},
                        "avg_credits_per_hour": {"type": "float"}
                    }
                }
            }
        }

        try:
            # Delete old templates if they exist
            for template_name in [f"{self.index_name_records}-template", f"{self.index_name_summary}-template"]:
                try:
                    self.es.options(ignore_status=404).indices.delete_index_template(name=template_name)
                except:
                    pass

            # Create new templates
            self.es.indices.put_index_template(
                name=f"{self.index_name_records}-template",
                body=records_template
            )
            print(f"[OK] Template creado para {self.index_name_records}")

            self.es.indices.put_index_template(
                name=f"{self.index_name_summary}-template",
                body=summary_template
            )
            print(f"[OK] Template creado para {self.index_name_summary}")

        except Exception as e:
            print(f"Advertencia: No se pudieron crear templates: {e}")

    def transform_record_for_es(self, record, ingestion_time):
        """Transform CDP record to Elasticsearch document"""

        usage_start = record.get('usageStartTimestamp', '')

        # Parse timestamp
        try:
            if usage_start:
                ts = datetime.fromisoformat(usage_start.replace('Z', '+00:00'))
                hour_of_day = ts.hour
                day_of_week = ts.weekday()  # 0=Monday, 6=Sunday
                day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                day_of_week_name = day_names[day_of_week]
                is_weekend = day_of_week >= 5
                is_night = hour_of_day >= 20 or hour_of_day <= 6

                # Human-readable labels for dashboards
                weekend_label = "Fin de semana" if is_weekend else "Entre semana"
                time_of_day_label = "Nocturno" if is_night else "Diurno"

                # Time block (4-hour blocks as CDP reports)
                time_block = f"{(hour_of_day // 4) * 4:02d}:00-{((hour_of_day // 4) * 4 + 4):02d}:00"
            else:
                ts = None
                hour_of_day = None
                day_of_week = None
                day_of_week_name = None
                is_weekend = None
                is_night = None
                weekend_label = None
                time_of_day_label = None
                time_block = None
        except:
            ts = None
            hour_of_day = None
            day_of_week = None
            day_of_week_name = None
            is_weekend = None
            is_night = None
            weekend_label = None
            time_of_day_label = None
            time_block = None

        doc = {
            '@timestamp': ts.isoformat() if ts else ingestion_time,
            'ingestion_time': ingestion_time,
            'usage_start': record.get('usageStartTimestamp'),
            'usage_end': record.get('usageEndTimestamp'),
            'cluster_name': record.get('clusterName'),
            'cluster_crn': record.get('clusterCrn'),
            'environment_name': record.get('environmentName'),
            'cloud_provider': record.get('cloudProvider'),
            'instance_type': record.get('instanceType'),
            'instance_count': record.get('instanceCount'),
            'hours': record.get('hours'),
            'quantity': record.get('quantity'),
            'credits': record.get('grossCharge'),
            'list_rate': record.get('listRate'),
            'cluster_type': record.get('clusterType'),
            'cluster_template': record.get('clusterTemplate'),
            'hour_of_day': hour_of_day,
            'day_of_week': day_of_week,
            'day_of_week_name': day_of_week_name,
            'is_weekend': is_weekend,
            'is_night': is_night,
            'weekend_label': weekend_label,
            'time_of_day_label': time_of_day_label,
            'time_block': time_block
        }

        return doc

    def generate_bulk_actions(self, records, index_name, ingestion_time):
        """Generate bulk actions for Elasticsearch"""
        for record in records:
            doc = self.transform_record_for_es(record, ingestion_time)
            yield {
                '_index': index_name,
                '_source': doc
            }

    def index_records(self, records):
        """Index individual consumption records"""

        if not records:
            print("No hay registros para indexar")
            return

        now = datetime.now(timezone.utc)
        ingestion_time = now.isoformat()
        index_name = f"{self.index_name_records}-{now.strftime('%Y.%m.%d')}"

        print(f"\nIndexando {len(records)} registros en {index_name}...")

        try:
            # Bulk index
            success, failed = bulk(
                self.es,
                self.generate_bulk_actions(records, index_name, ingestion_time),
                chunk_size=500,
                raise_on_error=False
            )

            print(f"[OK] Indexados: {success} registros")
            if failed:
                print(f"[ERROR] Fallidos: {len(failed)} registros")

            # Refresh index
            self.es.indices.refresh(index=index_name)

        except Exception as e:
            print(f"Error indexando registros: {e}")

    def delete_old_indices(self):
        """Delete old CDP indices to avoid duplicates"""
        print("\nEliminando índices antiguos...")

        try:
            # Get all indices matching our patterns
            indices_to_delete = []

            # Check for records indices
            try:
                records_indices = self.es.cat.indices(index=f"{self.index_name_records}-*", format="json")
                for idx in records_indices:
                    indices_to_delete.append(idx['index'])
            except:
                pass  # No indices found

            # Check for summary indices
            try:
                summary_indices = self.es.cat.indices(index=f"{self.index_name_summary}-*", format="json")
                for idx in summary_indices:
                    indices_to_delete.append(idx['index'])
            except:
                pass  # No indices found

            if indices_to_delete:
                print(f"  Eliminando {len(indices_to_delete)} índices antiguos:")
                for index_name in indices_to_delete:
                    print(f"    - {index_name}")
                    self.es.indices.delete(index=index_name)
                print(f"[OK] Índices antiguos eliminados")
            else:
                print("  No hay índices antiguos para eliminar")

        except Exception as e:
            print(f"Advertencia: Error eliminando índices antiguos: {e}")

    def index_summary(self, records):
        """Index aggregated summary data"""

        if not records:
            return

        print(f"\nGenerando datos agregados...")

        from collections import defaultdict

        # Aggregate by date and cluster
        summary = defaultdict(lambda: {
            'credits': 0,
            'hours': 0,
            'quantity': 0,
            'instance_types': set()
        })

        for record in records:
            usage_start = record.get('usageStartTimestamp', '')
            date_key = usage_start[:10] if usage_start else 'unknown'
            cluster_name = record.get('clusterName', 'Unknown')
            env_name = record.get('environmentName', 'Unknown')

            key = (date_key, cluster_name, env_name)

            summary[key]['credits'] += record.get('grossCharge', 0)
            summary[key]['hours'] += record.get('hours', 0)
            summary[key]['quantity'] += record.get('quantity', 0)
            summary[key]['instance_types'].add(record.get('instanceType', 'Unknown'))

        # Create documents
        docs = []
        for (date, cluster, env), data in summary.items():
            if date == 'unknown':
                continue

            doc = {
                '@timestamp': f"{date}T00:00:00Z",
                'date': date,
                'cluster_name': cluster,
                'environment_name': env,
                'total_credits': data['credits'],
                'total_hours': data['hours'],
                'total_quantity': data['quantity'],
                'instance_types': list(data['instance_types']),
                'avg_credits_per_hour': data['credits'] / data['hours'] if data['hours'] > 0 else 0
            }
            docs.append(doc)

        index_name = f"{self.index_name_summary}-{datetime.now(timezone.utc).strftime('%Y.%m.%d')}"

        print(f"Indexando {len(docs)} documentos agregados en {index_name}...")

        try:
            actions = [{'_index': index_name, '_source': doc} for doc in docs]
            success, failed = bulk(self.es, actions, chunk_size=500, raise_on_error=False)

            print(f"[OK] Indexados: {success} documentos agregados")
            if failed:
                print(f"[ERROR] Fallidos: {len(failed)} documentos")

            self.es.indices.refresh(index=index_name)

        except Exception as e:
            print(f"Error indexando resumen: {e}")

    def run(self):
        """Main execution"""
        print("=" * 60)
        print("CDP to Elasticsearch Ingestion")
        print("=" * 60)

        # Delete old indices to avoid duplicates
        self.delete_old_indices()

        # Create index templates
        self.create_index_templates()

        # Collect data
        records = self.collect_consumption_data(days=30)

        if not records:
            print("\n[ERROR] No se obtuvieron datos de CDP")
            return

        # Index raw records
        self.index_records(records)

        # Index aggregated summary
        self.index_summary(records)

        print("\n" + "=" * 60)
        print("[OK] Ingesta completada!")
        print("=" * 60)
        print(f"\nÍndices creados:")
        print(f"  - {self.index_name_records}-YYYY.MM.DD (registros individuales)")
        print(f"  - {self.index_name_summary}-YYYY.MM.DD (datos agregados)")
        print(f"\nPuedes crear visualizaciones en Kibana usando estos índices.")


def main():
    try:
        ingester = CDPToElasticsearch()
        ingester.run()
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
