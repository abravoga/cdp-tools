#!/usr/bin/env python3
"""
Script para crear dashboards de CDP en Kibana usando la API
"""

import requests
import json
from requests.auth import HTTPBasicAuth
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class KibanaDashboardCreator:
    def __init__(self,
                 kibana_url='https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io',
                 username='infra_admin',
                 password='imdeveloperS'):

        self.kibana_url = kibana_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            'kbn-xsrf': 'true',
            'Content-Type': 'application/json'
        }

    def create_data_view(self, title, time_field='@timestamp', id_suffix=''):
        """Create a data view (index pattern)"""

        data_view_id = f"cdp-{id_suffix}-dataview"

        payload = {
            "data_view": {
                "title": title,
                "timeFieldName": time_field,
                "name": title.replace('-*', '')
            }
        }

        url = f"{self.kibana_url}/api/data_views/data_view/{data_view_id}"

        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                verify=True
            )

            if response.status_code in [200, 201, 409]:  # 409 = already exists
                print(f"[OK] Data View creado/existe: {title}")
                return data_view_id
            else:
                print(f"[ERROR] Error creando Data View {title}: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except Exception as e:
            print(f"[ERROR] Excepción creando Data View: {e}")
            return None

    def create_lens_visualization(self, vis_id, title, description, state, data_view_id):
        """Create a Lens visualization"""

        payload = {
            "attributes": {
                "title": title,
                "description": description,
                "visualizationType": state.get("visualizationType"),
                "state": state
            },
            "references": [
                {
                    "id": data_view_id,
                    "name": "indexpattern-datasource-layer-layer1",
                    "type": "index-pattern"
                }
            ]
        }

        url = f"{self.kibana_url}/api/saved_objects/lens/{vis_id}"

        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                verify=True
            )

            if response.status_code in [200, 201]:
                print(f"[OK] Visualización creada: {title}")
                return vis_id
            elif response.status_code == 409:
                print(f"[OK] Visualización ya existe: {title}")
                return vis_id
            else:
                print(f"[ERROR] Error creando visualización {title}: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except Exception as e:
            print(f"[ERROR] Excepción creando visualización: {e}")
            return None

    def create_simple_visualizations(self, data_view_id):
        """Create all possible visualizations with available data"""

        visualizations = []

        # 1. Total Créditos - Metric
        vis_id = self.create_lens_visualization(
            "lens-total-credits",
            "Total Créditos",
            "Suma total de créditos consumidos",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1"],
                                "columns": {
                                    "col1": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Total Créditos",
                                        "operationType": "sum",
                                        "sourceField": "credits"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "layerType": "data",
                    "metricAccessor": "col1"
                },
                "visualizationType": "lnsMetric",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 2. Total Horas
        vis_id = self.create_lens_visualization(
            "lens-total-hours",
            "Total Horas",
            "Suma total de horas computadas",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1"],
                                "columns": {
                                    "col1": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Total Horas",
                                        "operationType": "sum",
                                        "sourceField": "quantity"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "layerType": "data",
                    "metricAccessor": "col1"
                },
                "visualizationType": "lnsMetric",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 3. Créditos por Cluster - Donut
        vis_id = self.create_lens_visualization(
            "lens-credits-by-cluster",
            "Créditos por Cluster",
            "Distribución de créditos por cluster",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Cluster",
                                        "operationType": "terms",
                                        "sourceField": "cluster_name",
                                        "params": {
                                            "size": 10,
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
                    "shape": "donut",
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
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 4. Créditos por Entorno - Donut
        vis_id = self.create_lens_visualization(
            "lens-credits-by-env",
            "Créditos por Entorno",
            "Distribución de créditos por entorno",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Entorno",
                                        "operationType": "terms",
                                        "sourceField": "environment_name",
                                        "params": {
                                            "size": 10,
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
                    "shape": "donut",
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
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 5. Tendencia de Consumo - Line Chart
        vis_id = self.create_lens_visualization(
            "lens-consumption-trend",
            "Tendencia de Consumo",
            "Evolución temporal del consumo de créditos",
            {
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
                                        "params": {"interval": "auto"}
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Créditos",
                                        "operationType": "sum",
                                        "sourceField": "credits"
                                    },
                                    "col3": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Cluster",
                                        "operationType": "terms",
                                        "sourceField": "cluster_name",
                                        "params": {
                                            "size": 5,
                                            "orderBy": {"type": "column", "columnId": "col2"},
                                            "orderDirection": "desc"
                                        }
                                    }
                                }
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
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "line",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1",
                        "splitAccessor": "col3"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 6. Consumo por Franja Horaria - Bar Chart
        vis_id = self.create_lens_visualization(
            "lens-time-blocks",
            "Consumo por Franja Horaria",
            "Distribución de consumo por bloques de 4 horas",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Franja Horaria",
                                        "operationType": "terms",
                                        "sourceField": "time_block",
                                        "params": {
                                            "size": 10,
                                            "orderBy": {"type": "alphabetical"},
                                            "orderDirection": "asc"
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
                    "legend": {"isVisible": True, "position": "right"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "preferredSeriesType": "bar",
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "bar",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 7. Consumo por Día de la Semana - Bar Chart
        vis_id = self.create_lens_visualization(
            "lens-day-of-week",
            "Consumo por Día de Semana",
            "Distribución de consumo por día de la semana",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Día",
                                        "operationType": "terms",
                                        "sourceField": "day_of_week_name",
                                        "params": {
                                            "size": 10,
                                            "orderBy": {"type": "alphabetical"},
                                            "orderDirection": "asc"
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
                    "legend": {"isVisible": True, "position": "right"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "preferredSeriesType": "bar",
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "bar",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 8. Fin de Semana vs Semana - Pie Chart
        vis_id = self.create_lens_visualization(
            "lens-weekend-comparison",
            "Fin de Semana vs Semana",
            "Comparación de consumo entre días laborables y fin de semana",
            {
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
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 9. Nocturno vs Diurno - Pie Chart
        vis_id = self.create_lens_visualization(
            "lens-night-comparison",
            "Consumo Nocturno vs Diurno",
            "Comparación de consumo nocturno (20:00-06:00) vs diurno",
            {
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
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 10. Top Tipos de Instancia - Horizontal Bar
        vis_id = self.create_lens_visualization(
            "lens-instance-types",
            "Top Tipos de Instancia",
            "Tipos de instancia más utilizados por consumo",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Tipo de Instancia",
                                        "operationType": "terms",
                                        "sourceField": "instance_type",
                                        "params": {
                                            "size": 10,
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
                    "legend": {"isVisible": True, "position": "right"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "preferredSeriesType": "bar_horizontal",
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "bar_horizontal",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 11. Consumo por Cloud Provider - Pie
        vis_id = self.create_lens_visualization(
            "lens-cloud-provider",
            "Consumo por Cloud Provider",
            "Distribución de consumo por proveedor cloud",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Provider",
                                        "operationType": "terms",
                                        "sourceField": "cloud_provider",
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
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 12. Consumo por Tipo de Cluster
        vis_id = self.create_lens_visualization(
            "lens-cluster-type",
            "Consumo por Tipo de Cluster",
            "Distribución por tipo de cluster",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Tipo",
                                        "operationType": "terms",
                                        "sourceField": "cluster_type",
                                        "params": {
                                            "size": 10,
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
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 13. Número Total de Registros
        vis_id = self.create_lens_visualization(
            "lens-total-records",
            "Total Registros",
            "Número total de registros de consumo",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1"],
                                "columns": {
                                    "col1": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Registros",
                                        "operationType": "count",
                                        "sourceField": "___records___"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "layerType": "data",
                    "metricAccessor": "col1"
                },
                "visualizationType": "lnsMetric",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 14. Promedio de Créditos por Registro
        vis_id = self.create_lens_visualization(
            "lens-avg-credits",
            "Promedio Créditos por Registro",
            "Promedio de créditos por registro",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1"],
                                "columns": {
                                    "col1": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Avg Créditos",
                                        "operationType": "average",
                                        "sourceField": "credits"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "layerType": "data",
                    "metricAccessor": "col1"
                },
                "visualizationType": "lnsMetric",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 15. Promedio de Horas por Registro
        vis_id = self.create_lens_visualization(
            "lens-avg-hours",
            "Promedio Horas por Registro",
            "Promedio de horas por registro",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1"],
                                "columns": {
                                    "col1": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Avg Horas",
                                        "operationType": "average",
                                        "sourceField": "quantity"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "layerType": "data",
                    "metricAccessor": "col1"
                },
                "visualizationType": "lnsMetric",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 16. Tabla Top Clusters con Detalles
        vis_id = self.create_lens_visualization(
            "lens-table-top-clusters",
            "Top Clusters - Tabla Detallada",
            "Tabla con detalles de los clusters más costosos",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2", "col3", "col4", "col5"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Cluster",
                                        "operationType": "terms",
                                        "sourceField": "cluster_name",
                                        "params": {
                                            "size": 15,
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
                                    },
                                    "col3": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Horas",
                                        "operationType": "sum",
                                        "sourceField": "quantity"
                                    },
                                    "col4": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Avg Instancias",
                                        "operationType": "average",
                                        "sourceField": "instance_count"
                                    },
                                    "col5": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Registros",
                                        "operationType": "count",
                                        "sourceField": "___records___"
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
                "visualizationType": "lnsDatatable",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 17. Evolución Horas por Cluster
        vis_id = self.create_lens_visualization(
            "lens-hours-trend",
            "Evolución de Horas",
            "Tendencia temporal de horas computadas por cluster",
            {
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
                                        "params": {"interval": "auto"}
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Horas",
                                        "operationType": "sum",
                                        "sourceField": "quantity"
                                    },
                                    "col3": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Cluster",
                                        "operationType": "terms",
                                        "sourceField": "cluster_name",
                                        "params": {
                                            "size": 5,
                                            "orderBy": {"type": "column", "columnId": "col2"},
                                            "orderDirection": "desc"
                                        }
                                    }
                                }
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
                    "preferredSeriesType": "area",
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "area",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1",
                        "splitAccessor": "col3"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 18. Horas por Entorno
        vis_id = self.create_lens_visualization(
            "lens-hours-by-env",
            "Horas por Entorno",
            "Distribución de horas computadas por entorno",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Entorno",
                                        "operationType": "terms",
                                        "sourceField": "environment_name",
                                        "params": {
                                            "size": 10,
                                            "orderBy": {"type": "column", "columnId": "col2"},
                                            "orderDirection": "desc"
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
                    "legend": {"isVisible": True, "position": "right"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "preferredSeriesType": "bar",
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "bar",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 19. Promedio de Instancias
        vis_id = self.create_lens_visualization(
            "lens-avg-instances",
            "Promedio de Instancias",
            "Número promedio de instancias por registro",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1"],
                                "columns": {
                                    "col1": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Avg Instancias",
                                        "operationType": "average",
                                        "sourceField": "instance_count"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "layerType": "data",
                    "metricAccessor": "col1"
                },
                "visualizationType": "lnsMetric",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 20. Consumo Diario (Bar Chart Temporal)
        vis_id = self.create_lens_visualization(
            "lens-daily-consumption",
            "Consumo Diario",
            "Créditos consumidos por día",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
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
                    "legend": {"isVisible": True, "position": "right"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "preferredSeriesType": "bar",
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "bar",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 21. Top 10 Días con Mayor Consumo
        vis_id = self.create_lens_visualization(
            "lens-top-days",
            "Top 10 Días con Mayor Consumo",
            "Los 10 días con mayor gasto en créditos",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
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
                    "legend": {"isVisible": True, "position": "right"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "gridlinesVisibilitySettings": {"x": True, "yLeft": True, "yRight": True},
                    "preferredSeriesType": "bar_horizontal",
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "bar_horizontal",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        # 22. Distribución de Instancias por Cluster
        vis_id = self.create_lens_visualization(
            "lens-instances-by-cluster",
            "Instancias por Cluster",
            "Distribución de número de instancias",
            {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["col1", "col2"],
                                "columns": {
                                    "col1": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Cluster",
                                        "operationType": "terms",
                                        "sourceField": "cluster_name",
                                        "params": {
                                            "size": 10,
                                            "orderBy": {"type": "column", "columnId": "col2"},
                                            "orderDirection": "desc"
                                        }
                                    },
                                    "col2": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Total Instancias",
                                        "operationType": "sum",
                                        "sourceField": "instance_count"
                                    }
                                }
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
                    "preferredSeriesType": "bar_horizontal",
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["col2"],
                        "position": "top",
                        "seriesType": "bar_horizontal",
                        "showGridlines": False,
                        "layerType": "data",
                        "xAccessor": "col1"
                    }]
                },
                "visualizationType": "lnsXY",
                "query": {"query": "", "language": "kuery"},
                "filters": []
            },
            data_view_id
        )
        if vis_id:
            visualizations.append(vis_id)

        return visualizations

    def create_dashboard(self, vis_ids):
        """Create dashboard with visualizations in a beautiful layout"""

        if not vis_ids:
            print("[ERROR] No hay visualizaciones para añadir al dashboard")
            return False

        # Layout optimizado por tipo de visualización
        layout_config = {
            # Fila 1: Métricas principales (6 métricas en 2 filas de 3)
            "lens-total-credits": {"x": 0, "y": 0, "w": 16, "h": 8},
            "lens-total-hours": {"x": 16, "y": 0, "w": 16, "h": 8},
            "lens-total-records": {"x": 32, "y": 0, "w": 16, "h": 8},
            "lens-avg-credits": {"x": 0, "y": 8, "w": 16, "h": 8},
            "lens-avg-hours": {"x": 16, "y": 8, "w": 16, "h": 8},
            "lens-avg-instances": {"x": 32, "y": 8, "w": 16, "h": 8},

            # Fila 2: Gráficos de tendencia temporal (grandes)
            "lens-consumption-trend": {"x": 0, "y": 16, "w": 24, "h": 15},
            "lens-hours-trend": {"x": 24, "y": 16, "w": 24, "h": 15},

            # Fila 3: Consumo diario y top días
            "lens-daily-consumption": {"x": 0, "y": 31, "w": 32, "h": 12},
            "lens-top-days": {"x": 32, "y": 31, "w": 16, "h": 12},

            # Fila 4: Distribuciones circulares (4 donuts)
            "lens-credits-by-cluster": {"x": 0, "y": 43, "w": 12, "h": 12},
            "lens-credits-by-env": {"x": 12, "y": 43, "w": 12, "h": 12},
            "lens-cloud-provider": {"x": 24, "y": 43, "w": 12, "h": 12},
            "lens-cluster-type": {"x": 36, "y": 43, "w": 12, "h": 12},

            # Fila 5: Análisis de patrones
            "lens-weekend-comparison": {"x": 0, "y": 55, "w": 12, "h": 10},
            "lens-night-comparison": {"x": 12, "y": 55, "w": 12, "h": 10},
            "lens-time-blocks": {"x": 24, "y": 55, "w": 24, "h": 12},

            # Fila 6: Día de la semana y análisis por horas
            "lens-day-of-week": {"x": 0, "y": 67, "w": 24, "h": 12},
            "lens-hours-by-env": {"x": 24, "y": 67, "w": 24, "h": 12},

            # Fila 7: Top instancias e instancias por cluster
            "lens-instance-types": {"x": 0, "y": 79, "w": 24, "h": 12},
            "lens-instances-by-cluster": {"x": 24, "y": 79, "w": 24, "h": 12},

            # Fila 8: Tabla detallada (grande)
            "lens-table-top-clusters": {"x": 0, "y": 91, "w": 48, "h": 15},
        }

        panels = []
        panel_idx = 1

        # Crear paneles según el layout configurado
        for vis_id in vis_ids:
            if vis_id in layout_config:
                config = layout_config[vis_id]
                panel = {
                    "version": "8.8.0",
                    "type": "lens",
                    "gridData": {
                        "x": config["x"],
                        "y": config["y"],
                        "w": config["w"],
                        "h": config["h"],
                        "i": str(panel_idx)
                    },
                    "panelIndex": str(panel_idx),
                    "embeddableConfig": {
                        "enhancements": {}
                    },
                    "panelRefName": f"panel_{panel_idx}"
                }
                panels.append(panel)
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
                "title": "CDP - Análisis de Consumo",
                "description": "Dashboard de análisis de consumo CDP",
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

        url = f"{self.kibana_url}/api/saved_objects/dashboard/dashboard-cdp-main"

        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                verify=True
            )

            if response.status_code in [200, 201]:
                print(f"[OK] Dashboard creado exitosamente!")
                return True
            elif response.status_code == 409:
                print(f"[OK] Dashboard ya existe, actualizando...")
                # Try updating instead
                response = requests.put(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    json=payload,
                    verify=True
                )
                if response.status_code == 200:
                    print(f"[OK] Dashboard actualizado!")
                    return True

            print(f"[ERROR] Error creando dashboard: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        except Exception as e:
            print(f"[ERROR] Excepción creando dashboard: {e}")
            return False

    def create_executive_dashboard(self, vis_ids):
        """Dashboard ejecutivo con KPIs clave"""

        executive_vis = [
            "lens-total-credits",
            "lens-total-hours",
            "lens-total-records",
            "lens-consumption-trend",
            "lens-credits-by-cluster",
            "lens-credits-by-env",
            "lens-table-top-clusters"
        ]

        layout = {
            "lens-total-credits": {"x": 0, "y": 0, "w": 16, "h": 10},
            "lens-total-hours": {"x": 16, "y": 0, "w": 16, "h": 10},
            "lens-total-records": {"x": 32, "y": 0, "w": 16, "h": 10},
            "lens-consumption-trend": {"x": 0, "y": 10, "w": 48, "h": 15},
            "lens-credits-by-cluster": {"x": 0, "y": 25, "w": 24, "h": 15},
            "lens-credits-by-env": {"x": 24, "y": 25, "w": 24, "h": 15},
            "lens-table-top-clusters": {"x": 0, "y": 40, "w": 48, "h": 15},
        }

        return self.create_themed_dashboard(
            "dashboard-cdp-executive",
            "CDP - Dashboard Ejecutivo",
            "Vista ejecutiva con KPIs clave de consumo CDP",
            executive_vis,
            layout
        )

    def create_temporal_dashboard(self, vis_ids):
        """Dashboard de análisis temporal"""

        temporal_vis = [
            "lens-consumption-trend",
            "lens-hours-trend",
            "lens-daily-consumption",
            "lens-top-days",
            "lens-day-of-week",
            "lens-time-blocks"
        ]

        layout = {
            "lens-consumption-trend": {"x": 0, "y": 0, "w": 24, "h": 15},
            "lens-hours-trend": {"x": 24, "y": 0, "w": 24, "h": 15},
            "lens-daily-consumption": {"x": 0, "y": 15, "w": 32, "h": 15},
            "lens-top-days": {"x": 32, "y": 15, "w": 16, "h": 15},
            "lens-day-of-week": {"x": 0, "y": 30, "w": 24, "h": 15},
            "lens-time-blocks": {"x": 24, "y": 30, "w": 24, "h": 15},
        }

        return self.create_themed_dashboard(
            "dashboard-cdp-temporal",
            "CDP - Análisis Temporal",
            "Tendencias y patrones temporales de consumo",
            temporal_vis,
            layout
        )

    def create_cost_dashboard(self, vis_ids):
        """Dashboard de análisis de costos"""

        cost_vis = [
            "lens-total-credits",
            "lens-avg-credits",
            "lens-credits-by-cluster",
            "lens-credits-by-env",
            "lens-cloud-provider",
            "lens-cluster-type",
            "lens-instance-types",
            "lens-consumption-trend",
            "lens-table-top-clusters"
        ]

        layout = {
            "lens-total-credits": {"x": 0, "y": 0, "w": 16, "h": 8},
            "lens-avg-credits": {"x": 16, "y": 0, "w": 16, "h": 8},
            "lens-consumption-trend": {"x": 32, "y": 0, "w": 16, "h": 16},
            "lens-credits-by-cluster": {"x": 0, "y": 8, "w": 16, "h": 12},
            "lens-credits-by-env": {"x": 16, "y": 8, "w": 16, "h": 12},
            "lens-cloud-provider": {"x": 0, "y": 20, "w": 12, "h": 12},
            "lens-cluster-type": {"x": 12, "y": 20, "w": 12, "h": 12},
            "lens-instance-types": {"x": 24, "y": 20, "w": 24, "h": 12},
            "lens-table-top-clusters": {"x": 0, "y": 32, "w": 48, "h": 15},
        }

        return self.create_themed_dashboard(
            "dashboard-cdp-costs",
            "CDP - Análisis de Costos",
            "Análisis detallado de costos y consumo de créditos",
            cost_vis,
            layout
        )

    def create_distribution_dashboard(self, vis_ids):
        """Dashboard de distribuciones"""

        dist_vis = [
            "lens-credits-by-cluster",
            "lens-credits-by-env",
            "lens-cloud-provider",
            "lens-cluster-type",
            "lens-instance-types",
            "lens-instances-by-cluster",
            "lens-hours-by-env"
        ]

        layout = {
            "lens-credits-by-cluster": {"x": 0, "y": 0, "w": 12, "h": 15},
            "lens-credits-by-env": {"x": 12, "y": 0, "w": 12, "h": 15},
            "lens-cloud-provider": {"x": 24, "y": 0, "w": 12, "h": 15},
            "lens-cluster-type": {"x": 36, "y": 0, "w": 12, "h": 15},
            "lens-instance-types": {"x": 0, "y": 15, "w": 24, "h": 15},
            "lens-instances-by-cluster": {"x": 24, "y": 15, "w": 24, "h": 15},
            "lens-hours-by-env": {"x": 0, "y": 30, "w": 48, "h": 12},
        }

        return self.create_themed_dashboard(
            "dashboard-cdp-distribution",
            "CDP - Distribuciones",
            "Distribución de recursos por diferentes dimensiones",
            dist_vis,
            layout
        )

    def create_efficiency_dashboard(self, vis_ids):
        """Dashboard de eficiencia y patrones de uso"""

        efficiency_vis = [
            "lens-weekend-comparison",
            "lens-night-comparison",
            "lens-time-blocks",
            "lens-day-of-week",
            "lens-avg-credits",
            "lens-avg-hours",
            "lens-avg-instances",
            "lens-hours-trend"
        ]

        layout = {
            "lens-weekend-comparison": {"x": 0, "y": 0, "w": 12, "h": 12},
            "lens-night-comparison": {"x": 12, "y": 0, "w": 12, "h": 12},
            "lens-avg-credits": {"x": 24, "y": 0, "w": 8, "h": 12},
            "lens-avg-hours": {"x": 32, "y": 0, "w": 8, "h": 12},
            "lens-avg-instances": {"x": 40, "y": 0, "w": 8, "h": 12},
            "lens-time-blocks": {"x": 0, "y": 12, "w": 24, "h": 15},
            "lens-day-of-week": {"x": 24, "y": 12, "w": 24, "h": 15},
            "lens-hours-trend": {"x": 0, "y": 27, "w": 48, "h": 15},
        }

        return self.create_themed_dashboard(
            "dashboard-cdp-efficiency",
            "CDP - Eficiencia y Patrones",
            "Análisis de patrones de uso y oportunidades de optimización",
            efficiency_vis,
            layout
        )

    def create_themed_dashboard(self, dashboard_id, title, description, vis_list, layout_config):
        """Create a themed dashboard with custom layout"""

        panels = []
        panel_idx = 1
        references = []

        for vis_id in vis_list:
            if vis_id in layout_config:
                config = layout_config[vis_id]
                panel = {
                    "version": "8.8.0",
                    "type": "lens",
                    "gridData": {
                        "x": config["x"],
                        "y": config["y"],
                        "w": config["w"],
                        "h": config["h"],
                        "i": str(panel_idx)
                    },
                    "panelIndex": str(panel_idx),
                    "embeddableConfig": {
                        "enhancements": {}
                    },
                    "panelRefName": f"panel_{panel_idx}"
                }
                panels.append(panel)

                references.append({
                    "name": f"panel_{panel_idx}",
                    "type": "lens",
                    "id": vis_id
                })

                panel_idx += 1

        payload = {
            "attributes": {
                "title": title,
                "description": description,
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

        url = f"{self.kibana_url}/api/saved_objects/dashboard/{dashboard_id}"

        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                verify=True
            )

            if response.status_code in [200, 201]:
                print(f"[OK] Dashboard creado: {title}")
                return True
            elif response.status_code == 409:
                # Update if exists
                response = requests.put(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    json=payload,
                    verify=True
                )
                if response.status_code == 200:
                    print(f"[OK] Dashboard actualizado: {title}")
                    return True

            print(f"[ERROR] Error creando dashboard {title}: {response.status_code}")
            return False

        except Exception as e:
            print(f"[ERROR] Excepción creando dashboard: {e}")
            return False

    def run(self):
        """Main execution"""
        print("=" * 60)
        print("Creador de Dashboards Temáticos CDP para Kibana")
        print("=" * 60)

        # Create Data View
        print("\n1. Creando Data View...")
        data_view_id = self.create_data_view(
            "cdp-consumption-records-*",
            time_field="@timestamp",
            id_suffix="records"
        )

        if not data_view_id:
            print("[ERROR] No se pudo crear el Data View")
            return

        # Create Visualizations
        print("\n2. Creando visualizaciones...")
        vis_ids = self.create_simple_visualizations(data_view_id)

        if not vis_ids:
            print("[ERROR] No se pudieron crear visualizaciones")
            return

        # Create Main Dashboard
        print("\n3. Creando dashboard principal...")
        self.create_dashboard(vis_ids)

        # Create Themed Dashboards
        print("\n4. Creando dashboards temáticos...")
        self.create_executive_dashboard(vis_ids)
        self.create_temporal_dashboard(vis_ids)
        self.create_cost_dashboard(vis_ids)
        self.create_distribution_dashboard(vis_ids)
        self.create_efficiency_dashboard(vis_ids)

        print("\n" + "=" * 60)
        print("[OK] Todos los dashboards creados exitosamente!")
        print("=" * 60)
        print(f"\nAccede a Kibana:")
        print(f"{self.kibana_url}/app/dashboards")
        print(f"\nDashboards disponibles:")
        print(f"  1. CDP - Análisis de Consumo (completo)")
        print(f"  2. CDP - Dashboard Ejecutivo")
        print(f"  3. CDP - Análisis Temporal")
        print(f"  4. CDP - Análisis de Costos")
        print(f"  5. CDP - Distribuciones")
        print(f"  6. CDP - Eficiencia y Patrones")


def main():
    try:
        creator = KibanaDashboardCreator()
        creator.run()
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
