#!/usr/bin/env python3
"""
Create complete forecast dashboard with all visualizations
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

def create_metric_viz(viz_id, title, field, forecast_dv_id):
    """Create metric visualization"""

    payload = {
        "attributes": {
            "title": title,
            "visualizationType": "lnsMetric",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1"],
                                "columns": {
                                    "col1": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": title,
                                        "operationType": "sum",
                                        "sourceField": field
                                    }
                                },
                                "indexPatternId": forecast_dv_id
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "layerType": "data",
                    "metricAccessor": "col1"
                },
                "query": {"query": "", "language": "kuery"},
                "filters": []
            }
        },
        "references": [
            {
                "id": forecast_dv_id,
                "name": "indexpattern-datasource-layer-layer1",
                "type": "index-pattern"
            }
        ]
    }

    url = f"{KIBANA_URL}/api/saved_objects/lens/{viz_id}?overwrite=true"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] Metrica creada: {title}")
            return viz_id
        else:
            print(f"[ERROR] Error creando {title}: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_cluster_forecast_viz(viz_id, cluster_name, forecast_dv_id):
    """Create forecast visualization for specific cluster"""

    payload = {
        "attributes": {
            "title": f"Prediccion - {cluster_name}",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2", "col3", "col4"],
                                "columns": {
                                    "col1": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "Fecha",
                                        "operationType": "date_histogram",
                                        "sourceField": "@timestamp",
                                        "params": {"interval": "d"}
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Prediccion",
                                        "operationType": "average",
                                        "sourceField": "predicted_credits"
                                    },
                                    "col3": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Minimo",
                                        "operationType": "average",
                                        "sourceField": "predicted_credits_lower"
                                    },
                                    "col4": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Maximo",
                                        "operationType": "average",
                                        "sourceField": "predicted_credits_upper"
                                    }
                                },
                                "indexPatternId": forecast_dv_id
                            }
                        }
                    }
                },
                "visualization": {
                    "legend": {"isVisible": True, "position": "bottom"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "preferredSeriesType": "area",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "accessors": ["col2", "col3", "col4"],
                            "position": "top",
                            "seriesType": "area",
                            "showGridlines": False,
                            "layerType": "data",
                            "xAccessor": "col1"
                        }
                    ]
                },
                "query": {"query": f"cluster_name: \"{cluster_name}\"", "language": "kuery"},
                "filters": []
            }
        },
        "references": [
            {
                "id": forecast_dv_id,
                "name": "indexpattern-datasource-layer-layer1",
                "type": "index-pattern"
            }
        ]
    }

    url = f"{KIBANA_URL}/api/saved_objects/lens/{viz_id}?overwrite=true"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] Visualizacion creada: Prediccion - {cluster_name}")
            return viz_id
        else:
            print(f"[ERROR] Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_combined_historical_forecast_viz(forecast_dv_id, records_dv_id):
    """Create visualization combining historical data with forecast"""

    vis_id = "lens-combined-historical-forecast"

    payload = {
        "attributes": {
            "title": "Consumo Historico + Prediccion (7 dias)",
            "description": "Ultimos 30 dias reales + proximos 7 dias predichos",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer_historical": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "Fecha",
                                        "operationType": "date_histogram",
                                        "sourceField": "@timestamp",
                                        "params": {"interval": "d"}
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Consumo Real",
                                        "operationType": "sum",
                                        "sourceField": "credits"
                                    }
                                },
                                "indexPatternId": records_dv_id
                            },
                            "layer_forecast": {
                                "columnOrder": ["col3", "col4"],
                                "columns": {
                                    "col3": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "Fecha Prediccion",
                                        "operationType": "date_histogram",
                                        "sourceField": "@timestamp",
                                        "params": {"interval": "d"}
                                    },
                                    "col4": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Prediccion",
                                        "operationType": "average",
                                        "sourceField": "predicted_credits"
                                    }
                                },
                                "indexPatternId": forecast_dv_id
                            }
                        }
                    }
                },
                "visualization": {
                    "legend": {"isVisible": True, "position": "bottom"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "preferredSeriesType": "line",
                    "layers": [
                        {
                            "layerId": "layer_historical",
                            "accessors": ["col2"],
                            "position": "top",
                            "seriesType": "line",
                            "showGridlines": False,
                            "layerType": "data",
                            "xAccessor": "col1"
                        },
                        {
                            "layerId": "layer_forecast",
                            "accessors": ["col4"],
                            "position": "top",
                            "seriesType": "line",
                            "showGridlines": False,
                            "layerType": "data",
                            "xAccessor": "col3",
                            "yConfig": [{"forAccessor": "col4", "color": "#FF6B6B"}]
                        }
                    ]
                },
                "query": {"query": "", "language": "kuery"},
                "filters": []
            }
        },
        "references": [
            {
                "id": records_dv_id,
                "name": "indexpattern-datasource-layer-layer_historical",
                "type": "index-pattern"
            },
            {
                "id": forecast_dv_id,
                "name": "indexpattern-datasource-layer-layer_forecast",
                "type": "index-pattern"
            }
        ]
    }

    url = f"{KIBANA_URL}/api/saved_objects/lens/{vis_id}?overwrite=true"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] Visualizacion creada: Historico + Prediccion")
            return vis_id
        else:
            print(f"[ERROR] Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_complete_dashboard(vis_ids):
    """Create complete forecast dashboard"""

    panels = [
        # Row 1: Metrics (4 columns each)
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 0, "y": 0, "w": 12, "h": 8, "i": "1"},
            "panelIndex": "1",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_1"
        },
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 12, "y": 0, "w": 12, "h": 8, "i": "2"},
            "panelIndex": "2",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_2"
        },
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 24, "y": 0, "w": 12, "h": 8, "i": "3"},
            "panelIndex": "3",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_3"
        },
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 36, "y": 0, "w": 12, "h": 8, "i": "4"},
            "panelIndex": "4",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_4"
        },
        # Row 2: Combined historical + forecast (full width)
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 0, "y": 8, "w": 48, "h": 15, "i": "5"},
            "panelIndex": "5",
            "embeddableConfig": {"enhancements": {}, "title": "Tendencia: Datos Reales + Predicciones"},
            "panelRefName": "panel_5"
        },
        # Row 3: Table (full width)
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 0, "y": 23, "w": 48, "h": 12, "i": "6"},
            "panelIndex": "6",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_6"
        },
        # Row 4: Individual cluster forecasts (2 columns)
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 0, "y": 35, "w": 24, "h": 12, "i": "7"},
            "panelIndex": "7",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_7"
        },
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 24, "y": 35, "w": 24, "h": 12, "i": "8"},
            "panelIndex": "8",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_8"
        }
    ]

    references = [
        {"name": "panel_1", "type": "lens", "id": vis_ids[0]},  # Total predicted
        {"name": "panel_2", "type": "lens", "id": vis_ids[1]},  # Average daily
        {"name": "panel_3", "type": "lens", "id": vis_ids[2]},  # Min predicted
        {"name": "panel_4", "type": "lens", "id": vis_ids[3]},  # Max predicted
        {"name": "panel_5", "type": "lens", "id": vis_ids[4]},  # Combined historical + forecast
        {"name": "panel_6", "type": "lens", "id": vis_ids[5]},  # Table
        {"name": "panel_7", "type": "lens", "id": vis_ids[6]},  # Cluster 1 forecast
        {"name": "panel_8", "type": "lens", "id": vis_ids[7]}   # Cluster 2 forecast
    ]

    payload = {
        "attributes": {
            "title": "CDP - Predicciones ML Completo",
            "description": "Dashboard completo con predicciones de consumo usando Machine Learning",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "syncColors": False, "hidePanelTitles": False}),
            "version": 1,
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})
            }
        },
        "references": references
    }

    url = f"{KIBANA_URL}/api/saved_objects/dashboard/dashboard-cdp-forecast-complete?overwrite=true"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201]:
            print(f"\n[OK] Dashboard completo creado: CDP - Predicciones ML Completo")
            return True
        else:
            print(f"\n[ERROR] Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

def main():
    print("=" * 70)
    print("Creacion de Dashboard Completo de Predicciones ML")
    print("=" * 70)

    forecast_dv_id = "cdp-forecast-dataview"
    records_dv_id = "cdp-records-dataview"

    vis_ids = []

    # Create metric visualizations
    print("\n1. Creando metricas de resumen...")
    vis_ids.append(create_metric_viz("lens-forecast-total-metric", "Total Predicho (7 dias)", "predicted_credits", forecast_dv_id))
    vis_ids.append(create_metric_viz("lens-forecast-avg-metric", "Promedio Diario Predicho", "predicted_credits", forecast_dv_id))
    vis_ids.append(create_metric_viz("lens-forecast-min-metric", "Minimo Predicho", "predicted_credits_lower", forecast_dv_id))
    vis_ids.append(create_metric_viz("lens-forecast-max-metric", "Maximo Predicho", "predicted_credits_upper", forecast_dv_id))

    # Create combined historical + forecast
    print("\n2. Creando visualizacion combinada (historico + prediccion)...")
    vis_ids.append(create_combined_historical_forecast_viz(forecast_dv_id, records_dv_id))

    # Create table (reuse existing)
    print("\n3. Agregando tabla de predicciones...")
    vis_ids.append("lens-forecast-table")

    # Create cluster forecasts
    print("\n4. Creando predicciones por cluster...")
    vis_ids.append(create_cluster_forecast_viz("lens-forecast-gea-cem-prod", "gea-cem-prod", forecast_dv_id))
    vis_ids.append(create_cluster_forecast_viz("lens-forecast-gcp-prod-datahub", "gcp-prod-datahub", forecast_dv_id))

    # Create dashboard
    print("\n5. Creando dashboard completo...")
    if None not in vis_ids:
        create_complete_dashboard(vis_ids)

    print("\n" + "=" * 70)
    print("Dashboard Completo Creado!")
    print("=" * 70)
    print("\nNuevo dashboard: 'CDP - Predicciones ML Completo'")
    print("\nIncluye:")
    print("  - 4 metricas de resumen (total, promedio, min, max)")
    print("  - Grafico combinado: datos historicos + predicciones")
    print("  - Tabla detallada de predicciones por cluster")
    print("  - Graficos individuales de prediccion por cluster principal")
    print("\nRefresca Kibana (Ctrl+F5) para verlo.")

if __name__ == "__main__":
    main()
