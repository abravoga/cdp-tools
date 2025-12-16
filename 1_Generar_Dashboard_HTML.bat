@echo off
title CDP - Generador de Dashboard HTML
color 0A
echo ============================================================
echo    CDP - Generador de Dashboard HTML
echo ============================================================
echo.
echo Generando dashboard HTML con datos de consumo CDP...
echo.

"C:\Program Files\Python312\python.exe" "C:\Users\abravoga\cdp-tools\cdp_dashboard.py"

echo.
echo ============================================================
echo    Proceso completado!
echo ============================================================
echo.
echo El archivo HTML ha sido generado en:
echo C:\Users\abravoga\cdp-tools\cdp_dashboard.html
echo.

REM Abrir el HTML en el navegador predeterminado
start "" "C:\Users\abravoga\cdp-tools\cdp_dashboard.html"

echo Presiona cualquier tecla para cerrar...
pause >nul
