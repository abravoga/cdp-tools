@echo off
title CDP - Actualizar Dashboards en Kibana
color 0E
echo ============================================================
echo    CDP - Actualizar Dashboards en Kibana
echo ============================================================
echo.
echo Creando/actualizando visualizaciones y dashboards en Kibana...
echo.

"C:\Program Files\Python312\python.exe" "C:\Users\abravoga\cdp-tools\create_kibana_dashboard.py"

echo.
echo ============================================================
echo    Proceso completado!
echo ============================================================
echo.
echo Los dashboards han sido actualizados en Kibana.
echo.
echo Accede a tus dashboards:
echo https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards
echo.
echo Dashboards disponibles:
echo   1. CDP - Analisis de Consumo (completo)
echo   2. CDP - Dashboard Ejecutivo
echo   3. CDP - Analisis Temporal
echo   4. CDP - Analisis de Costos
echo   5. CDP - Distribuciones
echo   6. CDP - Eficiencia y Patrones
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
