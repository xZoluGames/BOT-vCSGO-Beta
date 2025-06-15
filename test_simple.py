# test_simple.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

try:
    print("Probando imports...")
    from backend.core.config_manager import get_config_manager
    config = get_config_manager()
    print(f"✓ Sistema: {config.settings['project_name']} v{config.settings['version']}")
    print(f"✓ Proxies: {'Activados' if config.settings['proxy_settings']['enabled'] else 'Desactivados'}")
    print("\n✅ Sistema funcionando correctamente!")
except Exception as e:
    print(f"❌ Error: {e}")
