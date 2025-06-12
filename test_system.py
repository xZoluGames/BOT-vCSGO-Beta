#!/usr/bin/env python3
# test_system.py - Script de prueba rápida

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

try:
    from backend.core.config_manager import get_config_manager
    print("✓ ConfigManager importado correctamente")
    
    config = get_config_manager()
    print(f"✓ Proyecto: {config.settings['project_name']}")
    print(f"✓ Versión: {config.settings['version']}")
    print(f"✓ Proxies: {'Activados' if config.settings['proxy_settings']['enabled'] else 'Desactivados'}")
    
    from backend.core.proxy_manager import ProxyManager
    print("✓ ProxyManager importado correctamente")
    
    print("\n✅ Sistema configurado correctamente!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Por favor, verifica la instalación")
