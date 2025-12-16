================================================================================
    CDP TOOLS - HERRAMIENTAS DE ANALISIS DE CONSUMO
================================================================================

DESCRIPCION:
------------
Suite de herramientas para analizar el consumo de Cloudera Data Platform (CDP)
y visualizarlo tanto en HTML local como en dashboards de Kibana/Elasticsearch.


ACCESOS DIRECTOS DISPONIBLES:
------------------------------

1. 1_Generar_Dashboard_HTML.bat
   - Genera un dashboard HTML autocontenido con graficos interactivos
   - Abre automaticamente el HTML en tu navegador
   - No requiere conexion a Elasticsearch
   - Ideal para: Reportes rapidos, presentaciones, analisis offline

2. 2_Actualizar_Elasticsearch.bat
   - Conecta a CDP y obtiene datos de consumo de los ultimos 30 dias
   - Ingesta los datos en Elasticsearch (Elastic Cloud)
   - Crea indices: cdp-consumption-records-* y cdp-consumption-summary-*
   - Ejecutar cuando: Necesites actualizar los datos en Kibana

3. 3_Actualizar_Dashboards_Kibana.bat
   - Crea/actualiza 22 visualizaciones en Kibana
   - Crea/actualiza 6 dashboards tematicos
   - Solo necesario ejecutar una vez o cuando quieras recrear dashboards
   - No actualiza datos, solo visualizaciones


FLUJO DE TRABAJO RECOMENDADO:
------------------------------

PRIMERA VEZ:
1. Ejecutar: 2_Actualizar_Elasticsearch.bat (ingesta datos)
2. Ejecutar: 3_Actualizar_Dashboards_Kibana.bat (crea dashboards)
3. Acceder a Kibana y explorar los dashboards

ACTUALIZACIONES DIARIAS/SEMANALES:
1. Ejecutar: 2_Actualizar_Elasticsearch.bat
   (Esto actualiza los datos, los dashboards ya estan creados)

PARA REPORTES RAPIDOS:
1. Ejecutar: 1_Generar_Dashboard_HTML.bat
   (Genera HTML con datos actuales de CDP)


DASHBOARDS DISPONIBLES EN KIBANA:
----------------------------------

1. CDP - Analisis de Consumo (completo)
   - Dashboard con las 22 visualizaciones completas
   - Para: Analisis exhaustivo

2. CDP - Dashboard Ejecutivo
   - Solo KPIs clave y metricas principales
   - Para: Directivos y managers

3. CDP - Analisis Temporal
   - Tendencias, consumo diario, patrones temporales
   - Para: Analizar evolucion en el tiempo

4. CDP - Analisis de Costos
   - Enfocado en creditos, gastos y optimizacion
   - Para: FinOps y control de costos

5. CDP - Distribuciones
   - Distribuciones por cluster, entorno, provider, tipo
   - Para: Entender distribucion de recursos

6. CDP - Eficiencia y Patrones
   - Patrones de uso, fin de semana, nocturnos, franjas horarias
   - Para: Optimizacion operativa


ARCHIVOS PRINCIPALES:
---------------------

cdp_dashboard.py              - Script Python que genera HTML
cdp_to_elasticsearch.py       - Script Python que ingesta a Elasticsearch
create_kibana_dashboard.py    - Script Python que crea dashboards en Kibana
cdp_dashboard.html            - Dashboard HTML generado (se actualiza cada ejecucion)


REQUISITOS:
-----------

- Python 3.12 instalado en: C:\Program Files\Python312
- CDP CLI configurado con credenciales
- Acceso a Elastic Cloud (usuario: infra_admin)
- Librerias Python: elasticsearch, requests, urllib3


URL DE KIBANA:
--------------

https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards


SOPORTE:
--------

Para modificar configuracion, editar los archivos .py directamente.
Los scripts .bat son solo accesos directos que ejecutan los .py.


================================================================================
Generado con Claude Code
https://claude.com/claude-code
================================================================================
