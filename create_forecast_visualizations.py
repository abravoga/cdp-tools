#!/usr/bin/env python3
"""
Create visualizations for forecast data
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

def create_forecast_dataview():
    """Create data view for forecast data"""

    dv_id = "cdp-forecast-dataview"

    payload = {
        "data_view": {
            "title": "cdp-consumption-forecast-*",
            "timeFieldName": "@timestamp",
            "name": "CDP Forecasts"
        }
    }

    # Try to create using the correct API endpoint
    url = f"{KIBANA_URL}/api/data_views/data_view/{dv_id}"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201, 409]:
            print(f"[OK] Data View creado: CDP Forecasts")
            return dv_id
        else:
            # If it fails, try using saved_objects API instead
            print(f"[INFO] Intentando con API alternativa...")
            url_alt = f"{KIBANA_URL}/api/saved_objects/index-pattern/{dv_id}?overwrite=true"
            payload_alt = {
                "attributes": {
                    "title": "cdp-consumption-forecast-*",
                    "timeFieldName": "@timestamp"
                }
            }
            response = requests.post(url_alt, auth=auth, headers=headers, json=payload_alt, verify=True)
            if response.status_code in [200, 201]:
                print(f"[OK] Data View creado: CDP Forecasts")
                return dv_id
            else:
                print(f"[ERROR] Error: {response.status_code}")
                print(f"Response: {response.text}")
                return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_forecast_total_viz(forecast_dv_id, records_dv_id):
    """Create visualization showing historical + forecast"""

    vis_id = "lens-forecast-total"

    payload = {
        "attributes": {
            "title": "Prediccion de Consumo Total - Proximos 7 Dias",
            "description": "Datos historicos + predicciones para los proximos 7 dias",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            # Historical data layer
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
                                        "label": "Creditos Reales",
                                        "operationType": "sum",
                                        "sourceField": "credits"
                                    }
                                },
                                "indexPatternId": records_dv_id
                            },
                            # Forecast data layer
                            "layer_forecast": {
                                "columnOrder": ["col3", "col4", "col5", "col6"],
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
                                    },
                                    "col5": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Limite Inferior",
                                        "operationType": "average",
                                        "sourceField": "predicted_credits_lower"
                                    },
                                    "col6": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Limite Superior",
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
                    "legend": {"isVisible": True, "position": "right"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
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
                            "xAccessor": "col3"
                        }
                    ]
                },
                "query": {"query": "cluster_name: Total", "language": "kuery"},
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
            print(f"[OK] Visualizacion creada: Prediccion Total")
            return vis_id
        else:
            print(f"[ERROR] Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_forecast_table(forecast_dv_id):
    """Create table showing forecast details"""

    vis_id = "lens-forecast-table"

    payload = {
        "attributes": {
            "title": "Tabla de Predicciones - Proximos 7 Dias",
            "description": "Desglose detallado de predicciones por dia y cluster",
            "visualizationType": "lnsDatatable",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2", "col3", "col4", "col5"],
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
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Cluster",
                                        "operationType": "terms",
                                        "sourceField": "cluster_name",
                                        "params": {"size": 10, "orderBy": {"type": "column", "columnId": "col3"}, "orderDirection": "desc"}
                                    },
                                    "col3": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Creditos Predichos",
                                        "operationType": "average",
                                        "sourceField": "predicted_credits"
                                    },
                                    "col4": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Minimo",
                                        "operationType": "average",
                                        "sourceField": "predicted_credits_lower"
                                    },
                                    "col5": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Maximo",
                                        "operationType": "average",
                                        "sourceField": "predicted_credits_upper"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "layerType": "data",
                    "columns": [
                        {"columnId": "col1"},
                        {"columnId": "col2"},
                        {"columnId": "col3"},
                        {"columnId": "col4"},
                        {"columnId": "col5"}
                    ]
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

    url = f"{KIBANA_URL}/api/saved_objects/lens/{vis_id}?overwrite=true"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201]:
            print(f"[OK] Visualizacion creada: Tabla de Predicciones")
            return vis_id
        else:
            print(f"[ERROR] Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def create_forecast_dashboard(vis_ids):
    """Create dashboard with forecast visualizations"""

    panels = [
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 0, "y": 0, "w": 48, "h": 15, "i": "1"},
            "panelIndex": "1",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_1"
        },
        {
            "version": "8.8.0",
            "type": "lens",
            "gridData": {"x": 0, "y": 15, "w": 48, "h": 15, "i": "2"},
            "panelIndex": "2",
            "embeddableConfig": {"enhancements": {}},
            "panelRefName": "panel_2"
        }
    ]

    references = [
        {"name": "panel_1", "type": "lens", "id": vis_ids[0]},
        {"name": "panel_2", "type": "lens", "id": vis_ids[1]}
    ]

    payload = {
        "attributes": {
            "title": "CDP - Predicciones de Consumo (ML)",
            "description": "Predicciones de consumo usando Machine Learning",
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

    url = f"{KIBANA_URL}/api/saved_objects/dashboard/dashboard-cdp-forecast?overwrite=true"

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload, verify=True)
        if response.status_code in [200, 201]:
            print(f"\n[OK] Dashboard creado: CDP - Predicciones de Consumo (ML)")
            return True
        else:
            print(f"\n[ERROR] Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

def main():
    print("=" * 70)
    print("Creacion de Visualizaciones de Predicciones ML")
    print("=" * 70)

    print("\n1. Creando Data View para predicciones...")
    forecast_dv_id = create_forecast_dataview()

    if forecast_dv_id:
        records_dv_id = "cdp-records-dataview"

        print("\n2. Creando visualizacion de tendencia con predicciones...")
        vis1 = create_forecast_total_viz(forecast_dv_id, records_dv_id)

        print("\n3. Creando tabla de predicciones detalladas...")
        vis2 = create_forecast_table(forecast_dv_id)

        if vis1 and vis2:
            print("\n4. Creando dashboard de predicciones...")
            create_forecast_dashboard([vis1, vis2])

    print("\n" + "=" * 70)
    print("Visualizaciones creadas!")
    print("=" * 70)
    print("\nNuevo dashboard: 'CDP - Predicciones de Consumo (ML)'")
    print("\nIncluye:")
    print("  - Grafico historico + predicciones para proximos 7 dias")
    print("  - Tabla detallada de predicciones por cluster")
    print("\nRefresca Kibana (Ctrl+F5) para verlo.")

if __name__ == "__main__":
    main()
