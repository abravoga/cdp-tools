#!/usr/bin/env python3
"""Verify the new human-readable labels in Elasticsearch"""

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
print("Verificacion de campos legibles en Elasticsearch")
print("=" * 80)

# Get a sample document
result = es.search(
    index="cdp-consumption-records-*",
    body={
        "query": {"match_all": {}},
        "size": 5,
        "sort": [{"@timestamp": "desc"}]
    }
)

print("\nEjemplos de registros con campos legibles:")
print("-" * 80)

for i, hit in enumerate(result['hits']['hits'], 1):
    doc = hit['_source']
    print(f"\nRegistro {i}:")
    print(f"  Cluster:              {doc.get('cluster_name')}")
    print(f"  Fecha/Hora:           {doc.get('usage_start')}")
    print(f"  ")
    print(f"  is_weekend:           {doc.get('is_weekend')}  <- Valor booleano")
    print(f"  weekend_label:        {doc.get('weekend_label')}  <- USAR ESTE en dashboards!")
    print(f"  ")
    print(f"  is_night:             {doc.get('is_night')}  <- Valor booleano")
    print(f"  time_of_day_label:    {doc.get('time_of_day_label')}  <- USAR ESTE en dashboards!")
    print(f"  ")
    print(f"  Credits:              {doc.get('credits')}")

# Get unique values for the new fields
print("\n" + "=" * 80)
print("Valores disponibles en los campos legibles:")
print("-" * 80)

# Weekend labels
weekend_agg = es.search(
    index="cdp-consumption-records-*",
    body={
        "size": 0,
        "aggs": {
            "weekend_values": {
                "terms": {"field": "weekend_label"}
            }
        }
    }
)

print("\nCampo 'weekend_label':")
for bucket in weekend_agg['aggregations']['weekend_values']['buckets']:
    print(f"  - {bucket['key']:20s} ({bucket['doc_count']:,} registros)")

# Time of day labels
time_agg = es.search(
    index="cdp-consumption-records-*",
    body={
        "size": 0,
        "aggs": {
            "time_values": {
                "terms": {"field": "time_of_day_label"}
            }
        }
    }
)

print("\nCampo 'time_of_day_label':")
for bucket in time_agg['aggregations']['time_values']['buckets']:
    print(f"  - {bucket['key']:20s} ({bucket['doc_count']:,} registros)")

print("\n" + "=" * 80)
print("INSTRUCCIONES PARA KIBANA:")
print("-" * 80)
print("""
Para actualizar tus dashboards en Kibana:

1. Ve a Kibana -> Dashboard -> [Tu dashboard]
2. Edita las visualizaciones que usan is_weekend o is_night
3. Reemplaza los campos:
   - is_weekend        ->  weekend_label
   - is_night          ->  time_of_day_label

4. Ahora veras:
   - "Fin de semana" / "Entre semana"  (en lugar de true/false)
   - "Nocturno" / "Diurno"              (en lugar de true/false)

5. Guarda el dashboard
""")
print("=" * 80)
