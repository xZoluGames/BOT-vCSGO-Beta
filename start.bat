@echo off
echo ========================================
echo   BOT-vCSGO-Beta - Inicio Rápido
echo ========================================
echo.
echo Opciones:
echo   1. Probar scraper simple (Waxpeer)
echo   2. Ver estado del sistema
echo   3. Ejecutar todos los scrapers
echo   4. Salir
echo.
set /p opcion="Selecciona una opción (1-4): "

if "%opcion%"=="1" (
    python run_scrapers.py waxpeer --no-proxy --once
) else if "%opcion%"=="2" (
    python run_scrapers.py status
) else if "%opcion%"=="3" (
    python run_scrapers.py monitor
) else if "%opcion%"=="4" (
    exit
)
pause
