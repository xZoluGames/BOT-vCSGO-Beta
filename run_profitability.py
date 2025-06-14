#!/usr/bin/env python3
# run_profitability.py - Monitor de Rentabilidad para BOT-vCSGO-Beta

import sys
import time
import argparse
from pathlib import Path
from loguru import logger

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from backend.services.profitability_service import ProfitabilityService, run_profitability_monitor
from backend.core.config_manager import get_config_manager


def main():
    """Función principal del monitor de rentabilidad"""
    parser = argparse.ArgumentParser(
        description='Monitor de Rentabilidad - BOT-vCSGO-Beta v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Ejecutar solo una vez y salir'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Intervalo de actualización en segundos (default: 60)'
    )
    
    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Mostrar todas las oportunidades, no solo el top 10'
    )
    
    args = parser.parse_args()
    
    # Configurar logger
    logger.add(
        "logs/profitability_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    print("\n" + "="*60)
    print("MONITOR DE RENTABILIDAD - BOT-vCSGO-Beta v2.0")
    print("="*60)
    print("\nBuscando oportunidades de arbitraje...")
    print("Presiona Ctrl+C para detener\n")
    
    # Crear servicio
    service = ProfitabilityService()
    
    try:
        if args.once:
            # Ejecutar una sola vez
            service.run()
        else:
            # Ejecutar continuamente
            while True:
                service.run()
                
                print(f"\nPróxima actualización en {args.interval} segundos...")
                print("Presiona Ctrl+C para detener")
                
                time.sleep(args.interval)
                
    except KeyboardInterrupt:
        print("\n\nMonitor detenido por el usuario")
        logger.info("Monitor de rentabilidad detenido")
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()