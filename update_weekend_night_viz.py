#!/usr/bin/env python3
"""
Script para actualizar las visualizaciones de fin de semana y nocturno
Elimina y recrea las visualizaciones para usar los campos legibles
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
        if response.status_code in [200, 204]:
            print(f"[OK] Visualización eliminada: {vis_id}")
            return True
        elif response.status_code == 404:
            print(f"[INFO] Visualización no existe: {vis_id}")
            return True
        else:
            print(f"[ERROR] Error eliminando {vis_id}: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Excepción eliminando visualización: {e}")
        return False

def create_weekend_viz(data_view_id):
    """Create weekend comparison visualization with readable labels"""

    vis_id = "lens-weekend-comparison"

    payload = {
        "attributes": {
            "title": "Fin de Semana vs Semana",
            "description": "Comparación de consumo entre días laborables y fin de semana",
            "visualizationType": "lnsPie",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Tipo de Día",
                                        "operationType": "terms",
                                        "sourceField": "weekend_label",
                                        "params": {
                                            "size": 5,
                                            "orderBy": {"type": "column", "columnId": "col2"},
                                            "orderDirection": "desc"
                                        }
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Créditos",
                                        "operationType": "sum",
                                        "sourceField": "credits"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "shape": "pie",
                    "layers": [{
                        "layerId": "layer1",
                        "primaryGroups": ["col1"],
                        "metrics": ["col2"],
                        "numberDisplay": "percent",
                        "categoryDisplay": "default",
                        "legendDisplay": "show"
                    }]
                },
                "visualizationType": "lnsPie",
                "query": {"query": "", "language": "kuery"},
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

    url = f"{KIBANA_URL}/api/saved_objects/lens/{vis_id}"

    try:
        # Force overwrite
        url_with_overwrite = f"{url}?overwrite=true"
        response = requests.post(
            url_with_overwrite,
            auth=auth,
            headers=headers,
            json=payload,
            verify=True
        )

        if response.status_code in [200, 201]:
            print(f"[OK] Visualización creada: Fin de Semana vs Semana")
            return True
        else:
            print(f"[ERROR] Error creando visualización: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Excepción: {e}")
        return False

def create_night_viz(data_view_id):
    """Create night/day comparison visualization with readable labels"""

    vis_id = "lens-night-comparison"

    payload = {
        "attributes": {
            "title": "Consumo Nocturno vs Diurno",
            "description": "Comparación de consumo nocturno (20:00-06:00) vs diurno",
            "visualizationType": "lnsPie",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Horario",
                                        "operationType": "terms",
                                        "sourceField": "time_of_day_label",
                                        "params": {
                                            "size": 5,
                                            "orderBy": {"type": "column", "columnId": "col2"},
                                            "orderDirection": "desc"
                                        }
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Créditos",
                                        "operationType": "sum",
                                        "sourceField": "credits"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "shape": "pie",
                    "layers": [{
                        "layerId": "layer1",
                        "primaryGroups": ["col1"],
                        "metrics": ["col2"],
                        "numberDisplay": "percent",
                        "categoryDisplay": "default",
                        "legendDisplay": "show"
                    }]
                },
                "visualizationType": "lnsPie",
                "query": {"query": "", "language": "kuery"},
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

    url = f"{KIBANA_URL}/api/saved_objects/lens/{vis_id}"

    try:
        # Force overwrite
        url_with_overwrite = f"{url}?overwrite=true"
        response = requests.post(
            url_with_overwrite,
            auth=auth,
            headers=headers,
            json=payload,
            verify=True
        )

        if response.status_code in [200, 201]:
            print(f"[OK] Visualización creada: Consumo Nocturno vs Diurno")
            return True
        else:
            print(f"[ERROR] Error creando visualización: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Excepción: {e}")
        return False

def main():
    print("=" * 70)
    print("Actualización de Visualizaciones - Campos Legibles")
    print("=" * 70)

    data_view_id = "cdp-records-dataview"

    print("\n1. Eliminando visualizaciones antiguas...")
    delete_visualization("lens-weekend-comparison")
    delete_visualization("lens-night-comparison")

    print("\n2. Creando visualizaciones con campos legibles...")
    create_weekend_viz(data_view_id)
    create_night_viz(data_view_id)

    print("\n" + "=" * 70)
    print("[OK] Actualización completada!")
    print("=" * 70)
    print("\nRefresca tu navegador en Kibana para ver los cambios.")
    print("Los dashboards ahora mostrarán:")
    print("  - 'Fin de semana' / 'Entre semana' (en lugar de true/false)")
    print("  - 'Nocturno' / 'Diurno' (en lugar de true/false)")

if __name__ == "__main__":
    main()
