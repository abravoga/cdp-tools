@echo off
title CDP - Actualizar Datos en Elasticsearch
color 0B
echo ============================================================
echo    CDP - Actualizar Datos en Elasticsearch
echo ============================================================
echo.
echo Conectando a CDP y actualizando datos en Elasticsearch...
echo.

"C:\Program Files\Python312\python.exe" "C:\Users\abravoga\cdp-tools\cdp_to_elasticsearch.py"

echo.
echo ============================================================
echo    Proceso completado!
echo ============================================================
echo.
echo Los datos han sido actualizados en Elasticsearch.
echo Puedes ver los dashboards en Kibana:
echo https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
