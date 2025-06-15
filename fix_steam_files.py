# fix_steam_files.py - Arregla archivos faltantes de Steam

import json
from pathlib import Path

def create_empty_nameids():
    """Crea un archivo item_nameids.json vacío"""
    nameids_file = Path("JSON/item_nameids.json")
    nameids_file.parent.mkdir(exist_ok=True)
    
    # Crear estructura básica
    nameids_data = []
    
    with open(nameids_file, 'w', encoding='utf-8') as f:
        json.dump(nameids_data, f, indent=2)
    
    print(f"✓ Creado archivo {nameids_file}")

def create_empty_steam_data():
    """Crea un archivo steam_data.json vacío"""
    steam_file = Path("JSON/steam_data.json")
    steam_file.parent.mkdir(exist_ok=True)
    
    # Crear estructura básica
    steam_data = []
    
    with open(steam_file, 'w', encoding='utf-8') as f:
        json.dump(steam_data, f, indent=2)
    
    print(f"✓ Creado archivo {steam_file}")

if __name__ == "__main__":
    print("Creando archivos faltantes de Steam...")
    create_empty_nameids()
    create_empty_steam_data()
    print("\n✅ Archivos creados. Ahora ejecuta los scrapers de Steam para poblarlos:")
    print("  python run_scrapers.py steamnames --once")
    print("  python run_scrapers.py steamid --once")
    print("  python run_scrapers.py steammarket --once")