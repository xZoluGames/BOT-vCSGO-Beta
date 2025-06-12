# run_scrapers.py (en la raíz del proyecto)

import sys
import argparse
from pathlib import Path
from loguru import logger

# Agregar backend al path
sys.path.append(str(Path(__file__).parent))

from backend.core.config_manager import get_config_manager
from backend.scrapers.waxpeer_scraper import WaxpeerScraper
# Importar otros scrapers cuando los migres
# from backend.scrapers.csdeals_scraper import CSdealsScraper
# from backend.scrapers.empire_scraper import EmpireScraper


# Diccionario de scrapers disponibles
SCRAPERS = {
    'waxpeer': WaxpeerScraper,
    # 'csdeals': CSdealsScraper,
    # 'empire': EmpireScraper,
    # Agregar más scrapers conforme los migres
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
    """
    Ejecuta un scraper individual
    
    Args:
        scraper_name: Nombre del scraper a ejecutar
        use_proxy: Forzar uso de proxy (None = usar config)
        once: Si ejecutar solo una vez en lugar de bucle infinito
    """
    if scraper_name not in SCRAPERS:
        logger.error(f"Scraper no encontrado: {scraper_name}")
        logger.info(f"Scrapers disponibles: {', '.join(SCRAPERS.keys())}")
        return
    
    # Crear instancia del scraper
    scraper_class = SCRAPERS[scraper_name]
    scraper = scraper_class(use_proxy=use_proxy)
    
    try:
        if once:
            # Ejecutar solo una vez
            logger.info(f"Ejecutando {scraper_name} una sola vez...")
            scraper.run_once()
        else:
            # Ejecutar en bucle infinito
            logger.info(f"Iniciando bucle infinito para {scraper_name}...")
            scraper.run_forever()
            
    except KeyboardInterrupt:
        logger.info("Detenido por el usuario")
    except Exception as e:
        logger.error(f"Error ejecutando scraper: {e}")
    finally:
        logger.info(f"Scraper {scraper_name} finalizado")


def run_all_scrapers(use_proxy: bool = None):
    """
    Ejecuta todos los scrapers en paralelo (próximamente)
    Por ahora solo muestra información
    """
    logger.info("Ejecución de todos los scrapers aún no implementada")
    logger.info("Por favor, ejecuta cada scraper individualmente")
    logger.info(f"Scrapers disponibles: {', '.join(SCRAPERS.keys())}")


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
    
    print("\n" + "="*50)
    print("ESTADO DE CONFIGURACIÓN - BOT-vCSGO-Beta")
    print("="*50)
    
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
    
    # Scrapers disponibles
    print(f"\n🤖 Scrapers Disponibles ({len(SCRAPERS)}):")
    for name in SCRAPERS:
        scraper_config = config.get_scraper_config(name)
        interval = scraper_config.get('update_interval', 60)
        print(f"   - {name}: actualización cada {interval}s")
    
    # Umbrales de notificación
    print(f"\n📊 Umbrales de Rentabilidad:")
    thresholds = config.get_notification_thresholds()
    for platform, threshold in list(thresholds.items())[:5]:  # Mostrar solo 5
        platform_name = platform.replace('profitability_', '')
        print(f"   - {platform_name}: {threshold}%")
    
    print("\n" + "="*50 + "\n")


def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='BOT-vCSGO-Beta - Sistema de Scrapers Unificado',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run_scrapers.py status                    # Ver estado actual
  python run_scrapers.py waxpeer                   # Ejecutar Waxpeer con config global
  python run_scrapers.py waxpeer --proxy          # Ejecutar Waxpeer con proxy
  python run_scrapers.py waxpeer --no-proxy       # Ejecutar Waxpeer sin proxy
  python run_scrapers.py waxpeer --once           # Ejecutar Waxpeer una sola vez
  python run_scrapers.py toggle-proxy             # Activar/desactivar proxy globalmente
        """
    )
    
    # Argumentos principales
    parser.add_argument(
        'scraper',
        nargs='?',
        choices=['status', 'all', 'toggle-proxy'] + list(SCRAPERS.keys()),
        default='status',
        help='Scraper a ejecutar o comando especial'
    )
    
    # Argumentos opcionales
    parser.add_argument(
        '--proxy',
        action='store_true',
        help='Forzar uso de proxy (ignora configuración global)'
    )
    
    parser.add_argument(
        '--no-proxy',
        action='store_true',
        help='Forzar NO usar proxy (ignora configuración global)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Ejecutar solo una vez en lugar de bucle infinito'
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
    
    # Ejecutar comando
    if args.scraper == 'status':
        show_status()
    elif args.scraper == 'toggle-proxy':
        toggle_proxy_mode()
    elif args.scraper == 'all':
        run_all_scrapers(use_proxy)
    else:
        run_single_scraper(args.scraper, use_proxy, args.once)


if __name__ == "__main__":
    main()