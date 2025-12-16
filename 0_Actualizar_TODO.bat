@echo off
title CDP - Actualizacion Completa
color 0A
echo ============================================================
echo    CDP - Actualizacion Completa del Sistema
echo ============================================================
echo.
echo Este script ejecutara:
echo   1. Actualizacion de datos en Elasticsearch
echo   2. Generacion de predicciones ML
echo.
echo Presiona cualquier tecla para continuar...
pause >nul

echo.
echo ============================================================
echo    PASO 1/2: Actualizando datos en Elasticsearch
echo ============================================================
echo.

"C:\Program Files\Python312\python.exe" "C:\Users\abravoga\cdp-tools\cdp_to_elasticsearch.py"

echo.
echo ============================================================
echo    PASO 2/2: Generando predicciones ML
echo ============================================================
echo.

"C:\Program Files\Python312\python.exe" "C:\Users\abravoga\cdp-tools\forecast_with_prophet.py"

echo.
echo ============================================================
echo    ACTUALIZACION COMPLETA FINALIZADA!
echo ============================================================
echo.
echo Datos actualizados:
echo   - Registros de consumo CDP (ultimos 30 dias)
echo   - Predicciones ML (proximos 7 dias)
echo.
echo Dashboard principal:
echo https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
