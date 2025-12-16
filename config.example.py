#!/usr/bin/env python3
"""
Archivo de configuración para el sistema CDP

INSTRUCCIONES:
1. Copia este archivo y renómbralo a 'config.py'
2. Actualiza los valores con tus credenciales
3. NUNCA subas config.py a GitHub (está en .gitignore)
"""

# Configuración de Elasticsearch/Kibana
ELASTICSEARCH_URL = 'https://tu-cluster.es.europe-west1.gcp.cloud.es.io'
KIBANA_URL = 'https://tu-cluster.kb.europe-west1.gcp.cloud.es.io'

# Credenciales (CAMBIAR ESTOS VALORES)
USERNAME = 'tu_usuario'
PASSWORD = 'tu_contraseña'

# Configuración de índices
INDEX_NAME_RECORDS = 'cdp-consumption-records'
INDEX_NAME_SUMMARY = 'cdp-consumption-summary'
INDEX_NAME_FORECAST = 'cdp-consumption-forecast'

# Configuración de predicciones
FORECAST_DAYS = 7  # Días a predecir
CONFIDENCE_INTERVAL = 0.1  # 10% de banda de confianza

# Clusters principales para predicciones individuales
TOP_CLUSTERS = ['gea-cem-prod', 'gcp-prod-datahub']

# Configuración de datos históricos
HISTORICAL_DAYS = 30  # Días de datos históricos a obtener
