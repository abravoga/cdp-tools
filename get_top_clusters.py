#!/usr/bin/env python3
"""Get top clusters by consumption"""

from elasticsearch import Elasticsearch
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

es = Elasticsearch(
    ['https://gea-data-cloud-masorange-es.es.europe-west1.gcp.cloud.es.io'],
    basic_auth=('infra_admin', 'imdeveloperS'),
    verify_certs=True,
    request_timeout=30
)

# Get top clusters by credits
query = {
    "size": 0,
    "aggs": {
        "top_clusters": {
            "terms": {
                "field": "cluster_name",
                "size": 10,
                "order": {"total_credits": "desc"}
            },
            "aggs": {
                "total_credits": {
                    "sum": {"field": "credits"}
                }
            }
        }
    }
}

result = es.search(index="cdp-consumption-records-*", body=query)

print("=" * 70)
print("Top Clusters por Consumo de Créditos")
print("=" * 70)

buckets = result['aggregations']['top_clusters']['buckets']

for i, bucket in enumerate(buckets, 1):
    print(f"{i}. {bucket['key']:30s} - {bucket['total_credits']['value']:,.2f} créditos")

print("\n" + "=" * 70)
