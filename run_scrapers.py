# run_scrapers.py - Versión actualizada con todos los scrapers migrados

import sys
import argparse
from pathlib import Path
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Agregar backend al path
sys.path.append(str(Path(__file__).parent))

from backend.core.config_manager import get_config_manager
from backend.services.profitability_service import ProfitabilityService
# Importar todos los scrapers migrados
from backend.scrapers.waxpeer_scraper import WaxpeerScraper
from backend.scrapers.csdeals_scraper import CSDealsScraper
from backend.scrapers.empire_scraper import EmpireScraper
from backend.scrapers.skinport_scraper import SkinportScraper
from backend.scrapers.cstrade_scraper import CstradeScraper
from backend.scrapers.bitskins_scraper import BitskinsScraper
from backend.scrapers.marketcsgo_scraper import MarketCSGOScraper

# Importar scrapers complejos
from backend.scrapers.manncostore_scraper import ManncoStoreScraper
from backend.scrapers.tradeit_scraper import TradeitScraper
from backend.scrapers.skindeck_scraper import SkindeckScraper

# Importar scrapers simples
from backend.scrapers.white_scraper import WhiteScraper
from backend.scrapers.lisskins_scraper import LisskinsScraper
from backend.scrapers.shadowpay_scraper import ShadowpayScraper

# Importar scrapers de Steam
from backend.scrapers.steammarket_scraper import SteamMarketScraper
from backend.scrapers.steamnames_scraper import SteamNamesScraper
from backend.scrapers.steamid_scraper import SteamIDScraper
from backend.scrapers.steamlisting_scraper import SteamListingScraper

# Importar scrapers adicionales
from backend.scrapers.skinout_scraper import SkinoutScraper
from backend.scrapers.rapidskins_scraper import RapidskinsScraper


# Diccionario completo de scrapers disponibles
SCRAPERS = {
    # Scrapers principales de trading
    'waxpeer': WaxpeerScraper,
    'csdeals': CSDealsScraper,
    'empire': EmpireScraper,
    'skinport': SkinportScraper,
    'cstrade': CstradeScraper,
    'bitskins': BitskinsScraper,
    'marketcsgo': MarketCSGOScraper,
    
    # Scrapers que requieren Selenium
    'manncostore': ManncoStoreScraper,
    'tradeit': TradeitScraper,
    'skindeck': SkindeckScraper,
    
    # Scrapers simples
    'white': WhiteScraper,
    'lisskins': LisskinsScraper,
    'shadowpay': ShadowpayScraper,
    
    # Scrapers de Steam
    'steammarket': SteamMarketScraper,
    'steamnames': SteamNamesScraper,
    'steamid': SteamIDScraper,
    'steamlisting': SteamListingScraper,
    
    # Scrapers adicionales
    'skinout': SkinoutScraper,
    'rapidskins': RapidskinsScraper,
}

# Grupos de scrapers para facilitar el uso
SCRAPER_GROUPS = {
    'trading': [
        'waxpeer', 'csdeals', 'empire', 'skinport', 'cstrade', 
        'bitskins', 'marketcsgo', 'white', 'lisskins', 'shadowpay',
        'skinout', 'rapidskins'
    ],
    'selenium': ['manncostore', 'tradeit', 'skindeck'],
    'steam': ['steammarket', 'steamnames', 'steamid', 'steamlisting'],
    'fast': ['waxpeer', 'csdeals', 'bitskins', 'marketcsgo'],
    'slow': ['manncostore', 'tradeit', 'skinport'],
    'essential': ['waxpeer', 'csdeals', 'empire', 'steammarket'],
    'profitable': ['waxpeer', 'csdeals', 'empire', 'skinport', 'cstrade'],  # Scrapers más rentables
}


def setup_logging():
    """Configura el sistema de logging"""
    config = get_config_manager()
    log_config = config.settings.get('logging', {})
    
    # Remover handler por defecto
    logger.remove()
    
    # Agregar handler de consola
    logger.add(
        sys.stdout,
        format=log_config.get('format', '{time} | {level} | {message}'),
        level=log_config.get('level', 'INFO'),
        colorize=True
    )
    
    # Agregar handler de archivo
    log_path = config.get_log_path('scrapers.log')
    logger.add(
        log_path,
        format=log_config.get('format', '{time} | {level} | {message}'),
        level=log_config.get('level', 'INFO'),
        rotation=log_config.get('rotation', '1 day'),
        retention=log_config.get('retention', '7 days')
    )


def run_single_scraper(scraper_name: str, use_proxy: bool = None, once: bool = False):
    """Ejecuta un scraper individual"""
    if scraper_name not in SCRAPERS:
        logger.error(f"Scraper no encontrado: {scraper_name}")
        logger.info(f"Scrapers disponibles: {', '.join(SCRAPERS.keys())}")
        return
    
    # Crear instancia del scraper
    scraper_class = SCRAPERS[scraper_name]
    scraper = scraper_class(use_proxy=use_proxy)
    
    try:
        if once:
            logger.info(f"Ejecutando {scraper_name} una sola vez...")
            scraper.run_once()
        else:
            logger.info(f"Iniciando bucle infinito para {scraper_name}...")
            scraper.run_forever()
            
    except KeyboardInterrupt:
        logger.info("Detenido por el usuario")
    except Exception as e:
        logger.error(f"Error ejecutando scraper: {e}")
    finally:
        logger.info(f"Scraper {scraper_name} finalizado")


def run_scraper_group(group_name: str, use_proxy: bool = None, once: bool = False):
    """Ejecuta un grupo de scrapers en paralelo"""
    if group_name not in SCRAPER_GROUPS:
        logger.error(f"Grupo no encontrado: {group_name}")
        logger.info(f"Grupos disponibles: {', '.join(SCRAPER_GROUPS.keys())}")
        return
    
    scrapers_to_run = SCRAPER_GROUPS[group_name]
    logger.info(f"Ejecutando grupo '{group_name}': {scrapers_to_run}")
    
    def run_scraper_worker(scraper_name):
        """Worker para ejecutar un scraper en thread"""
        try:
            scraper_class = SCRAPERS[scraper_name]
            scraper = scraper_class(use_proxy=use_proxy)
            
            if once:
                scraper.run_once()
            else:
                scraper.run_forever()
                
        except Exception as e:
            logger.error(f"Error en {scraper_name}: {e}")
    
    # Ejecutar scrapers en paralelo
    with ThreadPoolExecutor(max_workers=len(scrapers_to_run)) as executor:
        futures = {
            executor.submit(run_scraper_worker, scraper_name): scraper_name 
            for scraper_name in scrapers_to_run
        }
        
        try:
            for future in as_completed(futures):
                scraper_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error en {scraper_name}: {e}")
        except KeyboardInterrupt:
            logger.info("Deteniendo todos los scrapers...")
            executor.shutdown(wait=False)


def run_all_scrapers(use_proxy: bool = None, exclude: list = None):
    """Ejecuta todos los scrapers disponibles"""
    exclude = exclude or []
    scrapers_to_run = [name for name in SCRAPERS.keys() if name not in exclude]
    
    logger.info(f"Ejecutando {len(scrapers_to_run)} scrapers en paralelo")
    logger.info(f"Scrapers: {scrapers_to_run}")
    
    if exclude:
        logger.info(f"Excluidos: {exclude}")
    
    def run_scraper_worker(scraper_name):
        try:
            scraper_class = SCRAPERS[scraper_name]
            scraper = scraper_class(use_proxy=use_proxy)
            scraper.run_forever()
        except Exception as e:
            logger.error(f"Error en {scraper_name}: {e}")
    
    with ThreadPoolExecutor(max_workers=len(scrapers_to_run)) as executor:
        futures = {
            executor.submit(run_scraper_worker, scraper_name): scraper_name 
            for scraper_name in scrapers_to_run
        }
        
        try:
            for future in as_completed(futures):
                scraper_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error en {scraper_name}: {e}")
        except KeyboardInterrupt:
            logger.info("Deteniendo todos los scrapers...")
            executor.shutdown(wait=False)


def toggle_proxy_mode():
    """Alterna el modo de proxy globalmente"""
    config = get_config_manager()
    current_state = config.settings['proxy_settings']['enabled']
    new_state = not current_state
    
    config.set_proxy_enabled(new_state)
    
    logger.info(f"Modo proxy {'ACTIVADO' if new_state else 'DESACTIVADO'} globalmente")
    
    if new_state:
        proxy_list = config.get_proxy_list()
        if not proxy_list:
            logger.warning("¡No se encontró archivo proxy.txt!")
            logger.info("Crea un archivo proxy.txt en la raíz del proyecto con un proxy por línea")


def show_status():
    """Muestra el estado actual de la configuración"""
    config = get_config_manager()
    
    print("\n" + "="*60)
    print("ESTADO DE CONFIGURACIÓN - BOT-vCSGO-Beta v2.0")
    print("="*60)
    
    # Información general
    print(f"\n📋 Información General:")
    print(f"   Proyecto: {config.settings['project_name']}")
    print(f"   Versión: {config.settings['version']}")
    print(f"   Idioma: {config.settings['language']}")
    
    # Estado de proxy
    proxy_enabled = config.settings['proxy_settings']['enabled']
    print(f"\n🔄 Configuración de Proxy:")
    print(f"   Estado: {'ACTIVADO' if proxy_enabled else 'DESACTIVADO'}")
    if proxy_enabled:
        proxy_list = config.get_proxy_list()
        print(f"   Proxies cargados: {len(proxy_list)}")
        print(f"   Timeout: {config.settings['proxy_settings']['timeout']}s")
        print(f"   Reintentos: {config.settings['proxy_settings']['max_retries']}")
    
    # Scrapers disponibles por categoría
    print(f"\n🤖 Scrapers Disponibles ({len(SCRAPERS)}):")
    
    print(f"\n   💰 Trading ({len(SCRAPER_GROUPS['trading'])}):")
    for name in SCRAPER_GROUPS['trading']:
        scraper_config = config.get_scraper_config(name)
        interval = scraper_config.get('update_interval', 60)
        print(f"      - {name}: cada {interval}s")
    
    print(f"\n   🌐 Selenium ({len(SCRAPER_GROUPS['selenium'])}):")
    for name in SCRAPER_GROUPS['selenium']:
        scraper_config = config.get_scraper_config(name)
        interval = scraper_config.get('update_interval', 300)
        print(f"      - {name}: cada {interval}s")
    
    print(f"\n   🎮 Steam ({len(SCRAPER_GROUPS['steam'])}):")
    for name in SCRAPER_GROUPS['steam']:
        scraper_config = config.get_scraper_config(name)
        interval = scraper_config.get('update_interval', 3600)
        print(f"      - {name}: cada {interval}s")
    
    # Grupos disponibles
    print(f"\n📦 Grupos de Scrapers:")
    for group_name, scrapers in SCRAPER_GROUPS.items():
        print(f"   - {group_name}: {len(scrapers)} scrapers")
    
    # Umbrales de notificación
    print(f"\n📊 Umbrales de Rentabilidad (top 5):")
    thresholds = config.get_notification_thresholds()
    for platform, threshold in list(thresholds.items())[:5]:
        platform_name = platform.replace('profitability_', '')
        print(f"   - {platform_name}: {threshold}%")
    
    print("\n" + "="*60 + "\n")

def run_profitability_analysis():
    """Ejecuta el análisis de rentabilidad"""
    try:
        print("\n" + "="*60)
        print("ANALIZANDO RENTABILIDAD")
        print("="*60)
        
        service = ProfitabilityService()
        service.run()
        
        print("\nAnálisis completado. Ver resultados en JSON/rentabilidad.json")
        
    except Exception as e:
        logger.error(f"Error en análisis de rentabilidad: {e}")
        print(f"Error: {e}")

def main():
    """Función principal con argumentos mejorados"""
    parser = argparse.ArgumentParser(
        description='BOT-vCSGO-Beta v2.0 - Sistema de Scrapers Unificado',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos especiales:
  status                    Ver estado del sistema
  all                       Ejecutar todos los scrapers
  group <nombre>            Ejecutar grupo de scrapers
  toggle-proxy              Activar/desactivar proxy
  profitability             Analizar rentabilidad actual
  monitor                   Ejecutar scrapers + rentabilidad continuamente

Grupos disponibles:
  trading                   Todos los scrapers de trading
  selenium                  Scrapers que requieren Selenium
  steam                     Scrapers de Steam
  fast                      Scrapers rápidos (1 min)
  slow                      Scrapers lentos (5+ min)
  essential                 Scrapers esenciales
  profitable                Scrapers más rentables

Ejemplos:
  python run_scrapers.py status
  python run_scrapers.py waxpeer
  python run_scrapers.py profitability
  python run_scrapers.py monitor
  python run_scrapers.py group profitable --with-profitability
        """
    )
    
    # Argumento principal
    parser.add_argument(
        'target',
        nargs='?',
        default='status',
        help='Scraper, grupo o comando a ejecutar'
    )
    
    # Argumentos opcionales
    parser.add_argument(
        '--proxy',
        action='store_true',
        help='Forzar uso de proxy'
    )
    
    parser.add_argument(
        '--no-proxy',
        action='store_true',
        help='Forzar NO usar proxy'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Ejecutar solo una vez'
    )
    
    parser.add_argument(
        '--exclude',
        type=str,
        help='Scrapers a excluir (separados por coma)'
    )
    
    parser.add_argument(
        '--group',
        action='store_true',
        help='Ejecutar como grupo de scrapers'
    )
    parser.add_argument(
        '--with-profitability',
        action='store_true',
        help='Ejecutar análisis de rentabilidad después de los scrapers'
    )
    
    parser.add_argument(
        '--monitor-interval',
        type=int,
        default=300,
        help='Intervalo para el modo monitor en segundos (default: 300)'
    )    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging()
    
    # Determinar uso de proxy
    use_proxy = None
    if args.proxy:
        use_proxy = True
    elif args.no_proxy:
        use_proxy = False
    
    # Parsear exclusiones
    exclude = []
    if args.exclude:
        exclude = [s.strip() for s in args.exclude.split(',')]
    
    # Ejecutar comando
    if args.target == 'profitability':
        run_profitability_analysis()
        return
    if args.target == 'status':
        show_status()
    elif args.target == 'toggle-proxy':
        toggle_proxy_mode()
    elif args.target == 'all':
        run_all_scrapers(use_proxy, exclude)
    elif args.group or args.target.startswith('group'):
        # Manejar "group trading" o "--group trading"
        group_name = args.target
        if args.target.startswith('group'):
            group_name = args.target.split(' ', 1)[1] if ' ' in args.target else 'trading'
        run_scraper_group(group_name, use_proxy, args.once)
    elif args.target in SCRAPER_GROUPS:
        # Si el target es un grupo válido
        run_scraper_group(args.target, use_proxy, args.once)
    elif args.target in SCRAPERS:
        # Scraper individual
        run_single_scraper(args.target, use_proxy, args.once)
    else:
        print(f"❌ Comando no reconocido: {args.target}")
        print(f"Scrapers disponibles: {', '.join(list(SCRAPERS.keys())[:10])}...")
        print(f"Grupos disponibles: {', '.join(SCRAPER_GROUPS.keys())}")
        print("Usa 'python run_scrapers.py status' para ver todas las opciones")
    if args.target == 'monitor':
        print("\n" + "="*60)
        print("MODO MONITOR ACTIVADO")
        print("="*60)
        print(f"Intervalo: {args.monitor_interval} segundos")
        print("Presiona Ctrl+C para detener\n")
        
        try:
            while True:
                # Ejecutar scrapers esenciales
                for scraper_name in SCRAPER_GROUPS['essential']:
                    run_all_scrapers(scraper_name, use_proxy=None, once=True)
                
                # Esperar un poco para que se guarden los JSON
                time.sleep(5)
                
                # Ejecutar análisis de rentabilidad
                run_profitability_analysis()
                
                # Esperar intervalo
                print(f"\nPróximo ciclo en {args.monitor_interval} segundos...")
                time.sleep(args.monitor_interval)
                
        except KeyboardInterrupt:
            print("\nMonitor detenido")
        return
    if args.with_profitability:
        print("\nEsperando 5 segundos antes de analizar rentabilidad...")
        time.sleep(5)
        run_profitability_analysis()
if __name__ == "__main__":
    main()