@echo off
echo ================================================================================
echo GENERANDO DASHBOARD GCP MULTI-PROYECTO (DEV + PROD)
echo ================================================================================
echo.

cd /d "%~dp0"
"C:\Program Files\Python312\python.exe" generate_gcp_dashboard_multiproject.py

echo.
echo ================================================================================
echo Dashboard generado correctamente!
echo ================================================================================
echo.
echo Abriendo dashboard en el navegador...
echo.

for %%f in (gcp_dashboard_multiproject_*.html) do set LATEST=%%f

if defined LATEST (
    start "" "%LATEST%"
) else (
    echo No se encontro el archivo generado
)

echo.
pause
