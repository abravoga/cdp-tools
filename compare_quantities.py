#!/usr/bin/env python3
"""Compare quantity totals between CDP and Elasticsearch"""

import subprocess
import json
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Connect to Elasticsearch
es = Elasticsearch(
    ['https://gea-data-cloud-masorange-es.es.europe-west1.gcp.cloud.es.io'],
    basic_auth=('infra_admin', 'imdeveloperS'),
    verify_certs=True,
    request_timeout=30
)

def get_cdp_total_quantity(days=30):
    """Get total quantity from CDP for last N days"""
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=days)

    from_timestamp = from_date.strftime('%Y-%m-%dT00:00:00Z')
    to_timestamp = to_date.strftime('%Y-%m-%dT23:59:59Z')

    print(f"\nObteniendo datos de CDP ({from_timestamp} a {to_timestamp})...")

    total_quantity = 0
    total_records = 0
    next_token = None

    cdp_cli = r"C:\Program Files\Python312\Scripts\cdp.exe"

    while True:
        args = [
            cdp_cli,
            'consumption', 'list-compute-usage-records',
            '--from-timestamp', from_timestamp,
            '--to-timestamp', to_timestamp,
            '--page-size', '1000'
        ]

        if next_token:
            args.extend(['--starting-token', next_token])

        result = subprocess.run(args, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        if 'records' in data:
            for record in data['records']:
                total_quantity += record.get('quantity', 0)
                total_records += 1

        next_token = data.get('nextToken')
        if not next_token:
            break

    return total_quantity, total_records

def get_es_total_quantity(days=30):
    """Get total quantity from Elasticsearch for last N days"""
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=days)

    print(f"\nConsultando Elasticsearch...")

    # Query using usage_start field (the actual CDP usage timestamp)
    query = {
        "query": {
            "range": {
                "usage_start": {
                    "gte": from_date.strftime('%Y-%m-%dT00:00:00Z'),
                    "lte": to_date.strftime('%Y-%m-%dT23:59:59Z')
                }
            }
        },
        "aggs": {
            "total_quantity": {
                "sum": {
                    "field": "quantity"
                }
            }
        },
        "size": 0
    }

    # Search in all cdp-consumption-records indices
    result = es.search(index="cdp-consumption-records-*", body=query)

    total_quantity = result['aggregations']['total_quantity']['value']
    total_records = result['hits']['total']['value']

    return total_quantity, total_records

def check_duplicates():
    """Check for duplicate records in Elasticsearch"""
    print("\nBuscando duplicados...")

    # Group by cluster + usage_start + instance_type to find duplicates
    query = {
        "size": 0,
        "aggs": {
            "duplicates": {
                "composite": {
                    "size": 1000,
                    "sources": [
                        {"cluster": {"terms": {"field": "cluster_name"}}},
                        {"usage_start": {"terms": {"field": "usage_start"}}},
                        {"instance_type": {"terms": {"field": "instance_type"}}}
                    ]
                },
                "aggs": {
                    "doc_count_agg": {
                        "value_count": {
                            "field": "_id"
                        }
                    },
                    "duplicates_filter": {
                        "bucket_selector": {
                            "buckets_path": {
                                "count": "doc_count_agg"
                            },
                            "script": "params.count > 1"
                        }
                    }
                }
            }
        }
    }

    result = es.search(index="cdp-consumption-records-*", body=query)

    duplicates = []
    if 'aggregations' in result and 'duplicates' in result['aggregations']:
        buckets = result['aggregations']['duplicates'].get('buckets', [])
        for bucket in buckets:
            if bucket['doc_count'] > 1:
                duplicates.append({
                    'key': bucket['key'],
                    'count': bucket['doc_count']
                })

    return duplicates

def main():
    print("=" * 80)
    print("Comparación CDP vs Elasticsearch - Quantity")
    print("=" * 80)

    # Get CDP totals
    print("\n1. DATOS DE CDP (últimos 30 días):")
    print("-" * 80)
    cdp_quantity, cdp_records = get_cdp_total_quantity(30)
    print(f"  Total quantity:     {cdp_quantity:,.2f}")
    print(f"  Total registros:    {cdp_records:,}")

    # Get ES totals
    print("\n2. DATOS DE ELASTICSEARCH (últimos 30 días):")
    print("-" * 80)
    es_quantity, es_records = get_es_total_quantity(30)
    print(f"  Total quantity:     {es_quantity:,.2f}")
    print(f"  Total registros:    {es_records:,}")

    # Check for duplicates
    print("\n3. VERIFICACIÓN DE DUPLICADOS:")
    print("-" * 80)
    duplicates = check_duplicates()
    if duplicates:
        print(f"  ¡ADVERTENCIA! Se encontraron {len(duplicates)} grupos con registros duplicados:")
        for i, dup in enumerate(duplicates[:5], 1):
            print(f"    {i}. {dup['key']} - {dup['count']} veces")
        if len(duplicates) > 5:
            print(f"    ... y {len(duplicates) - 5} más")
    else:
        print("  ✓ No se encontraron duplicados evidentes")

    # Comparison
    print("\n4. COMPARACIÓN:")
    print("-" * 80)
    diff_quantity = es_quantity - cdp_quantity
    diff_records = es_records - cdp_records

    print(f"  Diferencia en quantity:  {diff_quantity:+,.2f} ({(diff_quantity/cdp_quantity*100):+.2f}%)")
    print(f"  Diferencia en registros: {diff_records:+,} ({(diff_records/cdp_records*100):+.2f}%)")

    if abs(diff_quantity) < 0.01 and abs(diff_records) == 0:
        print("\n  ✓ Los datos coinciden perfectamente")
    elif diff_records > cdp_records * 0.5:
        print("\n  ⚠ PROBLEMA: Elasticsearch tiene muchos más registros que CDP")
        print("    Causa probable: Datos duplicados por múltiples ejecuciones del script")
        print("    Solución: Eliminar índices antiguos antes de cada ingesta")
    elif diff_records < -cdp_records * 0.1:
        print("\n  ⚠ PROBLEMA: Elasticsearch tiene menos registros que CDP")
        print("    Causa probable: No todos los datos se indexaron correctamente")
    else:
        print("\n  ℹ Los datos tienen una pequeña diferencia")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
