#!/usr/bin/env python3
"""
Fix trend visualizations that have col3 error
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

def delete_visualization(vis_id):
    """Delete a visualization"""
    url = f"{KIBANA_URL}/api/saved_objects/lens/{vis_id}"
    try:
        response = requests.delete(url, auth=auth, headers=headers, verify=True)
        if response.status_code in [200, 204, 404]:
            print(f"[OK] Visualización eliminada: {vis_id}")
            return True
        return False
    except:
        return False

def create_consumption_trend(data_view_id):
    """Create consumption trend visualization"""

    vis_id = "lens-consumption-trend"

    payload = {
        "attributes": {
            "title": "Tendencia de Consumo",
            "description": "Evolución temporal del consumo de créditos",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2", "col3"],
                                "columns": {
                                    "col1": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "@timestamp",
                                        "operationType": "date_histogram",
                                        "sourceField": "@timestamp",
                                        "params": {
                                            "interval": "auto",
                                            "includeEmptyRows": False
                                        }
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Créditos",
                                        "operationType": "sum",
                                        "sourceField": "credits",
                                        "params": {
                                            "emptyAsNull": False
                                        }
                                    },
                                    "col3": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Top 5 Clusters",
                                        "operationType": "terms",
                                        "sourceField": "cluster_name",
                                        "params": {
                                            "size": 5,
                                            "orderBy": {
                                                "type": "column",
                                                "columnId": "col2"
                                            },
                                            "orderDirection": "desc",
                                            "otherBucket": False,
                                            "missingBucket": False,
                                            "parentFormat": {
                                                "id": "terms"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "legend": {
                        "isVisible": True,
                        "position": "right",
                        "showSingleSeries": False
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
                    "preferredSeriesType": "line",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "accessors": ["col2"],
                            "position": "top",
                            "seriesType": "line",
                            "showGridlines": False,
                            "layerType": "data",
                            "xAccessor": "col1",
                            "splitAccessor": "col3"
                        }
                    ]
                },
                "query": {
                    "query": "",
                    "language": "kuery"
                },
                "filters": []
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
            print(f"[OK] Visualización creada: Tendencia de Consumo")
            return True
        else:
            print(f"[ERROR] Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def create_hours_trend(data_view_id):
    """Create hours trend visualization"""

    vis_id = "lens-hours-trend"

    payload = {
        "attributes": {
            "title": "Evolución de Horas",
            "description": "Tendencia temporal de horas computadas por cluster",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2", "col3"],
                                "columns": {
                                    "col1": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "@timestamp",
                                        "operationType": "date_histogram",
                                        "sourceField": "@timestamp",
                                        "params": {
                                            "interval": "auto",
                                            "includeEmptyRows": False
                                        }
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Horas",
                                        "operationType": "sum",
                                        "sourceField": "quantity",
                                        "params": {
                                            "emptyAsNull": False
                                        }
                                    },
                                    "col3": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Top 5 Clusters",
                                        "operationType": "terms",
                                        "sourceField": "cluster_name",
                                        "params": {
                                            "size": 5,
                                            "orderBy": {
                                                "type": "column",
                                                "columnId": "col2"
                                            },
                                            "orderDirection": "desc",
                                            "otherBucket": False,
                                            "missingBucket": False,
                                            "parentFormat": {
                                                "id": "terms"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "legend": {
                        "isVisible": True,
                        "position": "right",
                        "showSingleSeries": False
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
                            "xAccessor": "col1",
                            "splitAccessor": "col3"
                        }
                    ]
                },
                "query": {
                    "query": "",
                    "language": "kuery"
                },
                "filters": []
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
            print(f"[OK] Visualización creada: Evolución de Horas")
            return True
        else:
            print(f"[ERROR] Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def main():
    print("=" * 70)
    print("Corrección de Visualizaciones de Tendencia")
    print("=" * 70)

    data_view_id = "cdp-records-dataview"

    print("\n1. Eliminando visualizaciones con error...")
    delete_visualization("lens-consumption-trend")
    delete_visualization("lens-hours-trend")

    print("\n2. Recreando visualizaciones corregidas...")
    create_consumption_trend(data_view_id)
    create_hours_trend(data_view_id)

    print("\n" + "=" * 70)
    print("[OK] Visualizaciones corregidas!")
    print("=" * 70)
    print("\nRefresca Kibana (Ctrl+F5) para ver los cambios.")

if __name__ == "__main__":
    main()
