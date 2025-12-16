#!/usr/bin/env python3
"""
Create individual hours trend visualizations for each top cluster
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KIBANA_URL = 'https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io'
USERNAME = 'infra_admin'
PASSWORD = 'imdeveloperS'

auth = HTTPBasicAuth(USERNAME, PASSWORD)
headers = {
    'kbn-xsrf': 'true',
    'Content-Type': 'application/json'
}

# Top 5 clusters
CLUSTERS = [
    "gea-cem-prod",
    "gcp-prod-datahub",
    "gcp-pre-datahub",
    "gea-solr-dev",
    "gea-kafka-pro"
]

def create_cluster_hours_trend(cluster_name, data_view_id):
    """Create hours trend visualization for a specific cluster"""

    # Clean cluster name for ID
    cluster_id = cluster_name.replace('-', '_')
    vis_id = f"lens-hours-{cluster_id}"

    payload = {
        "attributes": {
            "title": f"Horas - {cluster_name}",
            "description": f"Evolucion de horas computadas para {cluster_name}",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "@timestamp",
                                        "operationType": "date_histogram",
                                        "sourceField": "@timestamp",
                                        "params": {
                                            "interval": "auto"
                                        }
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Horas",
                                        "operationType": "sum",
                                        "sourceField": "quantity"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "legend": {
                        "isVisible": True,
                        "position": "right"
                    },
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {
                        "x": True,
                        "yLeft": True,
                        "yRight": True
                    },
                    "tickLabelsVisibilitySettings": {
                        "x": True,
                        "yLeft": True,
                        "yRight": True
                    },
                    "gridlinesVisibilitySettings": {
                        "x": True,
                        "yLeft": True,
                        "yRight": True
                    },
                    "preferredSeriesType": "area",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "accessors": ["col2"],
                            "position": "top",
                            "seriesType": "area",
                            "showGridlines": False,
                            "layerType": "data",
                            "xAccessor": "col1"
                        }
                    ]
                },
                "query": {
                    "query": "",
                    "language": "kuery"
                },
                "filters": [
                    {
                        "meta": {
                            "alias": None,
                            "negate": False,
                            "disabled": False,
                            "type": "phrase",
                            "key": "cluster_name",
                            "params": {
                                "query": cluster_name
                            },
                            "index": data_view_id
                        },
                        "query": {
                            "match_phrase": {
                                "cluster_name": cluster_name
                            }
                        }
                    }
                ]
            }
        },
        "references": [
            {
                "id": data_view_id,
                "name": "indexpattern-datasource-layer-layer1",
                "type": "index-pattern"
            }
        ]
    }

    url = f"{KIBANA_URL}/api/saved_objects/lens/{vis_id}?overwrite=true"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] Visualizacion creada: {cluster_name}")
            return vis_id
        else:
            print(f"[ERROR] Error creando {cluster_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_hours_dashboard(vis_ids):
    """Create dashboard with all cluster hours trends"""

    # Create panel layout
    panels = []
    y_position = 0

    # Main total trend at top (full width)
    panels.append({
        "version": "8.8.0",
        "type": "lens",
        "gridData": {
            "x": 0,
            "y": y_position,
            "w": 48,
            "h": 12,
            "i": "1"
        },
        "panelIndex": "1",
        "embeddableConfig": {"enhancements": {}},
        "panelRefName": "panel_1"
    })
    y_position += 12

    # Individual cluster trends (2 per row)
    panel_idx = 2
    for i, vis_id in enumerate(vis_ids[1:], 1):  # Skip first one (total)
        col = 0 if i % 2 == 1 else 24
        if i > 1 and i % 2 == 1:
            y_position += 12

        panels.append({
            "version": "8.8.0",
            "type": "lens",
            "gridData": {
                "x": col,
                "y": y_position,
                "w": 24,
                "h": 12,
                "i": str(panel_idx)
            },
            "panelIndex": str(panel_idx),
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": f"panel_{panel_idx}"
        })
        panel_idx += 1

    # Create references
    references = [
        {
            "name": f"panel_{idx + 1}",
            "type": "lens",
            "id": vis_id
        }
        for idx, vis_id in enumerate(vis_ids)
    ]

    payload = {
        "attributes": {
            "title": "CDP - Evolucion de Horas por Cluster",
            "description": "Tendencias de horas computadas individuales por cluster",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({
                "useMargins": True,
                "syncColors": False,
                "hidePanelTitles": False
            }),
            "version": 1,
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"query": "", "language": "kuery"},
                    "filter": []
                })
            }
        },
        "references": references
    }

    url = f"{KIBANA_URL}/api/saved_objects/dashboard/dashboard-cdp-hours-trends?overwrite=true"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201]:
            print(f"\n[OK] Dashboard creado: CDP - Evolucion de Horas por Cluster")
            return True
        else:
            print(f"\n[ERROR] Error creando dashboard: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

def main():
    print("=" * 70)
    print("Creacion de Evolucion de Horas por Cluster")
    print("=" * 70)

    data_view_id = "cdp-records-dataview"
    vis_ids = []

    # Add main total trend
    vis_ids.append("lens-hours-trend")

    print("\nCreando visualizaciones para cada cluster...")
    for cluster in CLUSTERS:
        vis_id = create_cluster_hours_trend(cluster, data_view_id)
        if vis_id:
            vis_ids.append(vis_id)

    if vis_ids:
        print("\nCreando dashboard con todas las tendencias de horas...")
        create_hours_dashboard(vis_ids)

    print("\n" + "=" * 70)
    print("[OK] Proceso completado!")
    print("=" * 70)
    print("\nNuevo dashboard creado: 'CDP - Evolucion de Horas por Cluster'")
    print("Incluye:")
    print("  - Evolucion total de horas (arriba)")
    print("  - Evolucion individual de top 5 clusters")
    print("\nRefresca Kibana (Ctrl+F5) para verlo.")

if __name__ == "__main__":
    main()
