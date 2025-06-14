#!/usr/bin/env python3
# setup_database.py - Configuración inicial de la base de datos

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from backend.database.models import get_database_manager, Base
from backend.services.database_service import get_database_service
from loguru import logger
import json


def setup_database():
    """Configura la base de datos inicial"""
    print("\n" + "="*60)
    print("CONFIGURACIÓN DE BASE DE DATOS - BOT-vCSGO-Beta")
    print("="*60)
    
    try:
        # Crear carpeta data si no existe
        Path("data").mkdir(exist_ok=True)
        
        # Inicializar base de datos
        print("\n1. Creando tablas...")
        db_manager = get_database_manager()
        
        print("   ✓ Tabla 'items' creada")
        print("   ✓ Tabla 'price_history' creada")
        print("   ✓ Tabla 'profitable_opportunities' creada")
        print("   ✓ Tabla 'scraper_status' creada")
        
        # Verificar conexión
        print("\n2. Verificando conexión...")
        from sqlalchemy import text
        session = db_manager.get_session()
        session.execute(text("SELECT 1"))
        session.close()
        print("   ✓ Conexión exitosa")
        
        # Importar datos existentes si hay JSONs
        print("\n3. Buscando datos existentes...")
        json_path = Path("JSON")
        imported = 0
        
        if json_path.exists():
            db_service = get_database_service()
            
            for json_file in json_path.glob("*_data.json"):
                platform = json_file.stem.replace("_data", "")
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if data:
                        print(f"   → Importando {len(data)} items de {platform}...")
                        db_service.save_scraper_data(platform, data)
                        imported += len(data)
                        
                except Exception as e:
                    print(f"   ✗ Error importando {platform}: {e}")
        
        if imported > 0:
            print(f"\n   ✓ {imported} items importados exitosamente")
        else:
            print("   → No se encontraron datos para importar")
        
        print("\n" + "="*60)
        print("✅ BASE DE DATOS CONFIGURADA EXITOSAMENTE")
        print("="*60)
        print("\nAhora puedes usar los comandos con base de datos:")
        print("  python run_scrapers.py monitor")
        print("  python run_profitability.py")
        print("\nLa base de datos se encuentra en: data/csgo_arbitrage.db")
        
    except Exception as e:
        print(f"\n❌ Error configurando base de datos: {e}")
        print("\nPor favor, verifica que tienes SQLAlchemy instalado:")
        print("  pip install sqlalchemy")
        sys.exit(1)


def check_database():
    """Verifica el estado de la base de datos"""
    try:
        db_service = get_database_service()
        
        print("\n" + "="*60)
        print("ESTADO DE LA BASE DE DATOS")
        print("="*60)
        
        # Obtener estadísticas
        session = db_service.db_manager.get_session()
        
        # Contar items
        from backend.database.models import Item, PriceHistory, ProfitableOpportunity
        
        items_count = session.query(Item).count()
        history_count = session.query(PriceHistory).count()
        opportunities_count = session.query(ProfitableOpportunity).filter_by(is_active=True).count()
        
        print(f"\n📊 Estadísticas:")
        print(f"   Items totales: {items_count}")
        print(f"   Registros de histórico: {history_count}")
        print(f"   Oportunidades activas: {opportunities_count}")
        
        # Estado de scrapers
        print(f"\n🤖 Estado de Scrapers:")
        scrapers_status = db_service.get_scrapers_status()
        
        for scraper in scrapers_status:
            status_emoji = "✅" if scraper['status'] == 'idle' else "🔄" if scraper['status'] == 'running' else "❌"
            print(f"   {status_emoji} {scraper['name']}: {scraper['status']} - {scraper['items_found']} items")
        
        session.close()
        
    except Exception as e:
        print(f"\n❌ Error verificando base de datos: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Configuración de base de datos')
    parser.add_argument('--check', action='store_true', help='Verificar estado de la base de datos')
    parser.add_argument('--cleanup', type=int, help='Limpiar datos antiguos (días)')
    
    args = parser.parse_args()
    
    if args.check:
        check_database()
    elif args.cleanup:
        db_service = get_database_service()
        db_service.cleanup_old_data(args.cleanup)
        print(f"✓ Limpieza completada (datos más antiguos de {args.cleanup} días)")
    else:
        setup_database()