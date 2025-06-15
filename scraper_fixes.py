# scraper_fixes.py - Arreglos adicionales para scrapers

import json
from pathlib import Path

def fix_database_models():
    """Arregla el modelo de base de datos"""
    print("Arreglando modelos de base de datos...")
    
    models_file = Path("backend/database/models.py")
    if models_file.exists():
        content = models_file.read_text()
        
        # Buscar la línea problemática
        if "scraper_status.run_count += 1" in content:
            # Ya está en el artifact database_service_fixed
            print("  ⚠️ Necesitas aplicar el fix manualmente en database_service.py")
        else:
            print("  ✓ Modelos parecen estar bien")

def fix_base_scraper():
    """Arregla base_scraper.py"""
    print("Arreglando base_scraper.py...")
    
    base_scraper_file = Path("backend/core/base_scraper.py")
    if base_scraper_file.exists():
        print("  ⚠️ Necesitas aplicar el fix manualmente en base_scraper.py")
        print("     Ver instrucciones en web_interface_readme.md")
    else:
        print("  ❌ No se encontró base_scraper.py")

def create_scraper_configs():
    """Crea archivo de configuraciones por defecto para scrapers"""
    print("Creando configuraciones por defecto...")
    
    config_file = Path("config/scraper_configs.json")
    config_file.parent.mkdir(exist_ok=True)
    
    default_configs = {
        "waxpeer": {
            "enabled": True,
            "use_proxy": False,
            "interval": 60,
            "max_retries": 5,
            "timeout": 10
        },
        "csdeals": {
            "enabled": True,
            "use_proxy": False,
            "interval": 60,
            "max_retries": 5,
            "timeout": 10
        },
        "empire": {
            "enabled": True,
            "use_proxy": False,
            "interval": 30,
            "max_retries": 5,
            "timeout": 10
        },
        "steammarket": {
            "enabled": True,
            "use_proxy": False,
            "interval": 300,
            "max_retries": 10,
            "timeout": 15
        }
    }
    
    # Aplicar configuración similar a todos los scrapers
    scrapers = [
        'waxpeer', 'csdeals', 'empire', 'skinport', 'cstrade', 
        'bitskins', 'marketcsgo', 'manncostore', 'tradeit', 
        'skindeck', 'white', 'lisskins', 'shadowpay', 'skinout',
        'rapidskins', 'steammarket', 'steamnames', 'steamid', 'steamlisting'
    ]
    
    for scraper in scrapers:
        if scraper not in default_configs:
            # Configuración por defecto
            use_proxy = scraper in ['manncostore', 'tradeit']  # Estos suelen necesitar proxy
            interval = 300 if 'steam' in scraper else 60
            
            default_configs[scraper] = {
                "enabled": True,
                "use_proxy": use_proxy,
                "interval": interval,
                "max_retries": 5,
                "timeout": 10
            }
    
    with open(config_file, 'w') as f:
        json.dump(default_configs, f, indent=2)
    
    print(f"  ✓ Creado {config_file}")

def check_dependencies():
    """Verifica dependencias necesarias"""
    print("\nVerificando dependencias...")
    
    try:
        import fastapi
        print("  ✓ FastAPI instalado")
    except ImportError:
        print("  ❌ FastAPI no instalado - ejecuta: pip install fastapi")
    
    try:
        import uvicorn
        print("  ✓ Uvicorn instalado")
    except ImportError:
        print("  ❌ Uvicorn no instalado - ejecuta: pip install uvicorn")
    
    try:
        import websockets
        print("  ✓ WebSockets instalado")
    except ImportError:
        print("  ❌ WebSockets no instalado - ejecuta: pip install websockets")

def main():
    print("\n" + "="*60)
    print("ARREGLOS PARA BOT-vCSGO-Beta")
    print("="*60)
    
    # Ejecutar arreglos
    fix_database_models()
    fix_base_scraper()
    create_scraper_configs()
    check_dependencies()
    
    print("\n" + "="*60)
    print("PRÓXIMOS PASOS:")
    print("="*60)
    print("\n1. Aplica los fixes manuales indicados arriba")
    print("2. Instala dependencias faltantes si las hay")
    print("3. Ejecuta: python fix_steam_files.py")
    print("4. Ejecuta: python start_web.py")
    print("\n¡Listo para usar la nueva interfaz web!")

if __name__ == "__main__":
    main()