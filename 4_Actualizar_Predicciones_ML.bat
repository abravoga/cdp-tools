@echo off
title CDP - Actualizar Predicciones ML
color 0E
echo ============================================================
echo    CDP - Actualizar Predicciones con Machine Learning
echo ============================================================
echo.
echo Generando predicciones para los proximos 7 dias...
echo.

"C:\Program Files\Python312\python.exe" "C:\Users\abravoga\cdp-tools\forecast_with_prophet.py"

echo.
echo ============================================================
echo    Predicciones actualizadas!
echo ============================================================
echo.
echo Las predicciones se han guardado en Elasticsearch.
echo Indice: cdp-consumption-forecast-*
echo.
echo Puedes verlas en Kibana:
echo https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/discover
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
