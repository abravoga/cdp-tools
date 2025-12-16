#!/usr/bin/env python3
"""List all CDP indices in Elasticsearch"""

from elasticsearch import Elasticsearch
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

es = Elasticsearch(
    ['https://gea-data-cloud-masorange-es.es.europe-west1.gcp.cloud.es.io'],
    basic_auth=('infra_admin', 'imdeveloperS'),
    verify_certs=True,
    request_timeout=30
)

print("=" * 80)
print("Índices de CDP en Elasticsearch")
print("=" * 80)

# Get all indices matching the pattern
indices = es.cat.indices(index="cdp-consumption-*", format="json")

records_indices = []
summary_indices = []

for idx in indices:
    name = idx['index']
    docs = idx['docs.count']
    size = idx['store.size']

    if 'records' in name:
        records_indices.append((name, docs, size))
    else:
        summary_indices.append((name, docs, size))

print("\nÍndices de RECORDS (cdp-consumption-records-*):")
print("-" * 80)
for name, docs, size in sorted(records_indices):
    print(f"  {name:40s}  {docs:>10s} docs  {size:>10s}")

print(f"\nTotal: {len(records_indices)} índices de records")

print("\n\nÍndices de SUMMARY (cdp-consumption-summary-*):")
print("-" * 80)
for name, docs, size in sorted(summary_indices):
    print(f"  {name:40s}  {docs:>10s} docs  {size:>10s}")

print(f"\nTotal: {len(summary_indices)} índices de summary")

# Count total docs
total_record_docs = sum(int(docs) for _, docs, _ in records_indices if docs != 'null')
print("\n" + "=" * 80)
print(f"TOTAL DOCUMENTOS EN TODOS LOS ÍNDICES: {total_record_docs:,}")
print("=" * 80)

if len(records_indices) > 1:
    print("\n⚠ PROBLEMA DETECTADO:")
    print(f"  Hay {len(records_indices)} índices diferentes")
    print("  Esto causa duplicación de datos en los dashboards")
    print("\n  SOLUCIÓN: Deberías:")
    print("  1. Eliminar todos los índices antiguos")
    print("  2. Mantener solo el índice más reciente")
    print("  3. O configurar el script para eliminar índices viejos automáticamente")
