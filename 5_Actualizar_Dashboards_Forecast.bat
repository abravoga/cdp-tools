@echo off
title CDP - Actualizar Dashboards de Predicciones
color 0B
echo ============================================================
echo    CDP - Actualizar Dashboards de Predicciones ML
echo ============================================================
echo.
echo Este script recreara los dashboards de predicciones en Kibana:
echo   - CDP - Predicciones de Consumo (ML) [Basico]
echo   - CDP - Predicciones ML Completo [Completo]
echo.
echo Presiona cualquier tecla para continuar...
pause >nul

echo.
echo ============================================================
echo    PASO 1/2: Creando dashboard basico
echo ============================================================
echo.

"C:\Program Files\Python312\python.exe" "C:\Users\abravoga\cdp-tools\create_forecast_visualizations.py"

echo.
echo ============================================================
echo    PASO 2/2: Creando dashboard completo
echo ============================================================
echo.

"C:\Program Files\Python312\python.exe" "C:\Users\abravoga\cdp-tools\create_complete_forecast_dashboard.py"

echo.
echo ============================================================
echo    DASHBOARDS DE PREDICCIONES ACTUALIZADOS!
echo ============================================================
echo.
echo Dashboards creados:
echo   - CDP - Predicciones de Consumo (ML)
echo   - CDP - Predicciones ML Completo
echo.
echo Refresca Kibana (Ctrl+F5) para ver los cambios.
echo.
echo Dashboard principal:
echo https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
