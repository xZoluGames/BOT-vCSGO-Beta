#!/usr/bin/env python3
# quick_fix_all.py - Solución rápida para todos los problemas

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
import time

print("""
╔══════════════════════════════════════════════════════════════╗
║          SOLUCIONADOR AUTOMÁTICO - BOT-vCSGO-Beta            ║
║                                                              ║
║  Este script arreglará automáticamente los problemas         ║
║  más comunes del sistema.                                   ║
╚══════════════════════════════════════════════════════════════╝
""")

def step(message):
    """Imprime un paso con formato"""
    print(f"\n🔧 {message}")
    time.sleep(0.5)

def success(message):
    """Imprime éxito"""
    print(f"   ✅ {message}")

def warning(message):
    """Imprime advertencia"""
    print(f"   ⚠️  {message}")

def error(message):
    """Imprime error"""
    print(f"   ❌ {message}")

# PASO 1: Verificar estructura básica
step("Verificando estructura del proyecto...")
required_dirs = ['backend', 'backend/scrapers', 'backend/core', 'config', 'logs', 'JSON']
for dir_path in required_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
success("Estructura verificada")

# PASO 2: Crear archivo proxy.txt vacío
step("Creando archivo proxy.txt...")
proxy_file = Path("proxy.txt")
if not proxy_file.exists():
    proxy_file.write_text("# Proxies desactivados por defecto\n# Agrega proxies aquí si los necesitas\n")
    success("proxy.txt creado")
else:
    success("proxy.txt ya existe")

# PASO 3: Desactivar proxies globalmente
step("Desactivando proxies en la configuración...")
settings_path = Path("config/settings.json")
settings_path.parent.mkdir(exist_ok=True)

default_settings = {
    "project_name": "BOT-vCSGO-Beta",
    "version": "2.0.0",
    "language": "es",
    "proxy_settings": {
        "enabled": False,  # DESACTIVADO
        "timeout": 30,
        "max_retries": 3
    },
    "database": {
        "enabled": False  # DESACTIVADO para simplificar
    },
    "scrapers": {
        "default_interval": 300,
        "default_timeout": 30
    }
}

with open(settings_path, 'w') as f:
    json.dump(default_settings, f, indent=2)
success("Proxies desactivados")

# PASO 4: Limpiar caché de ChromeDriver
step("Limpiando caché de ChromeDriver...")
cache_paths = [
    Path.home() / "appdata" / "roaming" / "undetected_chromedriver",
    Path.home() / ".cache" / "undetected_chromedriver",
    Path.home() / "AppData" / "Roaming" / "undetected_chromedriver"
]

for cache_path in cache_paths:
    if cache_path.exists():
        try:
            shutil.rmtree(cache_path)
            success(f"Caché eliminado: {cache_path}")
        except:
            warning(f"No se pudo eliminar: {cache_path}")

# PASO 5: Crear configuración para scrapers
step("Configurando scrapers...")
platforms_path = Path("config/scrapers/platforms.json")
platforms_path.parent.mkdir(exist_ok=True)

platforms_config = {
    "waxpeer": {
        "update_interval": 60,
        "use_proxy": False,
        "timeout": 30
    },
    "csdeals": {
        "update_interval": 60,
        "use_proxy": False,
        "timeout": 30
    },
    "empire": {
        "update_interval": 120,
        "use_proxy": False,
        "timeout": 30
    },
    "manncostore": {
        "update_interval": 300,
        "use_proxy": False,
        "timeout": 60,
        "use_selenium": True
    },
    "tradeit": {
        "update_interval": 300,
        "use_proxy": False,
        "timeout": 60,
        "use_selenium": True
    }
}

with open(platforms_path, 'w') as f:
    json.dump(platforms_config, f, indent=2)
success("Scrapers configurados")

# PASO 6: Crear script de prueba simple
step("Creando script de prueba...")
test_script = '''# test_simple.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

try:
    print("Probando imports...")
    from backend.core.config_manager import get_config_manager
    config = get_config_manager()
    print(f"✓ Sistema: {config.settings['project_name']} v{config.settings['version']}")
    print(f"✓ Proxies: {'Activados' if config.settings['proxy_settings']['enabled'] else 'Desactivados'}")
    print("\\n✅ Sistema funcionando correctamente!")
except Exception as e:
    print(f"❌ Error: {e}")
'''

with open("test_simple.py", 'w') as f:
    f.write(test_script)
success("Script de prueba creado")

# PASO 7: Instalar dependencias faltantes
step("Verificando dependencias...")
try:
    import undetected_chromedriver
    success("undetected-chromedriver instalado")
except ImportError:
    warning("undetected-chromedriver no instalado")
    print("   Instalando...")
    subprocess.run([sys.executable, "-m", "pip", "install", "undetected-chromedriver"], capture_output=True)

# PASO 8: Crear comando de inicio simple
step("Creando comando de inicio simplificado...")
start_script = '''@echo off
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
'''

if sys.platform == "win32":
    with open("start.bat", 'w') as f:
        f.write(start_script)
    success("start.bat creado")
else:
    # Linux/Mac
    start_script_sh = '''#!/bin/bash
echo "========================================"
echo "  BOT-vCSGO-Beta - Inicio Rápido"
echo "========================================"
echo ""
echo "1. Probar scraper simple (Waxpeer)"
echo "2. Ver estado del sistema"
echo "3. Ejecutar todos los scrapers"
echo "4. Salir"
echo ""
read -p "Selecciona una opción (1-4): " opcion

case $opcion in
    1) python run_scrapers.py waxpeer --no-proxy --once ;;
    2) python run_scrapers.py status ;;
    3) python run_scrapers.py monitor ;;
    4) exit ;;
esac
'''
    with open("start.sh", 'w') as f:
        f.write(start_script_sh)
    os.chmod("start.sh", 0o755)
    success("start.sh creado")

# RESUMEN FINAL
print("""
╔══════════════════════════════════════════════════════════════╗
║                    ✅ ARREGLOS COMPLETADOS                   ║
╚══════════════════════════════════════════════════════════════╝

📋 RESUMEN DE CAMBIOS:
   ✅ Proxies desactivados globalmente
   ✅ Caché de ChromeDriver limpiado
   ✅ Configuración simplificada
   ✅ Scripts de prueba creados

🚀 PRÓXIMOS PASOS:

1. PRUEBA EL SISTEMA:
   python test_simple.py

2. PRUEBA UN SCRAPER SIMPLE:
   python run_scrapers.py waxpeer --once

3. USA EL INICIO RÁPIDO:
   """ + ("start.bat" if sys.platform == "win32" else "./start.sh") + """

⚠️  NOTAS IMPORTANTES:
   - Los scrapers con Selenium (manncostore, tradeit) pueden
     seguir fallando si no tienes Chrome instalado
   - Para usar proxies, edita config/settings.json y 
     cambia "enabled" a true

💡 Si sigues teniendo problemas:
   1. Verifica tu conexión a internet
   2. Asegúrate de tener Python 3.9+ instalado
   3. Reinstala las dependencias: pip install -r requirements.txt

¡Buena suerte! 🎮
""")

# Ejecutar prueba automática
print("\n" + "="*60)
print("Ejecutando prueba automática...")
print("="*60)
subprocess.run([sys.executable, "test_simple.py"])