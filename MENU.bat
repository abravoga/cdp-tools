@echo off
title CDP - Menu Principal
color 0B

:MENU
cls
echo ============================================================
echo    CDP - MENU PRINCIPAL
echo ============================================================
echo.
echo    Sistema de Analisis y Prediccion de Consumo CDP
echo.
echo ============================================================
echo.
echo    OPCIONES PRINCIPALES:
echo.
echo    [0] Actualizar TODO (Datos + Predicciones) *** RECOMENDADO ***
echo.
echo    ACTUALIZACIONES INDIVIDUALES:
echo.
echo    [1] Actualizar solo Datos en Elasticsearch
echo    [2] Actualizar solo Predicciones ML
echo    [3] Actualizar Dashboards Principales en Kibana
echo    [4] Actualizar Dashboards de Predicciones
echo.
echo    VERIFICACION:
echo.
echo    [5] Verificar Dashboards en Kibana
echo    [6] Comparar Datos CDP vs Elasticsearch
echo.
echo    DOCUMENTACION:
echo.
echo    [7] Ver Resumen Completo
echo    [8] Ver Lista de Dashboards
echo.
echo    KIBANA:
echo.
echo    [9] Abrir Kibana - Dashboards
echo    [A] Abrir Kibana - Predicciones ML Completo
echo.
echo    [X] Salir
echo.
echo ============================================================
echo.
set /p opcion="Selecciona una opcion: "

if /i "%opcion%"=="0" goto ACTUALIZAR_TODO
if /i "%opcion%"=="1" goto ACTUALIZAR_DATOS
if /i "%opcion%"=="2" goto ACTUALIZAR_PREDICCIONES
if /i "%opcion%"=="3" goto ACTUALIZAR_DASHBOARDS
if /i "%opcion%"=="4" goto ACTUALIZAR_DASHBOARDS_FORECAST
if /i "%opcion%"=="5" goto VERIFICAR_DASHBOARDS
if /i "%opcion%"=="6" goto COMPARAR_DATOS
if /i "%opcion%"=="7" goto VER_RESUMEN
if /i "%opcion%"=="8" goto VER_DASHBOARDS
if /i "%opcion%"=="9" goto ABRIR_KIBANA
if /i "%opcion%"=="A" goto ABRIR_PREDICCIONES
if /i "%opcion%"=="X" goto SALIR

echo.
echo Opcion invalida. Presiona cualquier tecla para continuar...
pause >nul
goto MENU

:ACTUALIZAR_TODO
cls
echo ============================================================
echo    Ejecutando: Actualizacion Completa
echo ============================================================
echo.
call "0_Actualizar_TODO.bat"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:ACTUALIZAR_DATOS
cls
echo ============================================================
echo    Ejecutando: Actualizacion de Datos
echo ============================================================
echo.
call "2_Actualizar_Elasticsearch.bat"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:ACTUALIZAR_PREDICCIONES
cls
echo ============================================================
echo    Ejecutando: Actualizacion de Predicciones ML
echo ============================================================
echo.
call "4_Actualizar_Predicciones_ML.bat"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:ACTUALIZAR_DASHBOARDS
cls
echo ============================================================
echo    Ejecutando: Actualizacion de Dashboards Principales
echo ============================================================
echo.
call "3_Actualizar_Dashboards_Kibana.bat"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:ACTUALIZAR_DASHBOARDS_FORECAST
cls
echo ============================================================
echo    Ejecutando: Actualizacion de Dashboards de Predicciones
echo ============================================================
echo.
call "5_Actualizar_Dashboards_Forecast.bat"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:VERIFICAR_DASHBOARDS
cls
echo ============================================================
echo    Verificando Dashboards en Kibana
echo ============================================================
echo.
"C:\Program Files\Python312\python.exe" "verify_kibana_dashboards.py"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:COMPARAR_DATOS
cls
echo ============================================================
echo    Comparando Datos CDP vs Elasticsearch
echo ============================================================
echo.
"C:\Program Files\Python312\python.exe" "compare_quantities.py"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:VER_RESUMEN
cls
type "RESUMEN_COMPLETO.md"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:VER_DASHBOARDS
cls
type "DASHBOARDS_KIBANA.md"
echo.
echo Presiona cualquier tecla para volver al menu...
pause >nul
goto MENU

:ABRIR_KIBANA
start https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards
goto MENU

:ABRIR_PREDICCIONES
start https://gea-data-cloud-masorange-es.kb.europe-west1.gcp.cloud.es.io/app/dashboards#/view/dashboard-cdp-forecast-complete
goto MENU

:SALIR
cls
echo.
echo Gracias por usar el sistema CDP!
echo.
timeout /t 2 >nul
exit
