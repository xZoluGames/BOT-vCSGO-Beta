# BOT-vCSGO-Beta v2.0

Sistema unificado de scrapers para arbitraje de items de CS:GO

## 🚀 Instalación Rápida

### 1. Clonar/Copiar el proyecto
```bash
# Si tienes git
git clone <tu-repositorio>
cd BOT-vCSGO-Beta

# O simplemente copia los archivos a una carpeta
```

### 2. Crear entorno virtual (recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar proxies (opcional)
Crea un archivo `proxy.txt` en la raíz del proyecto con un proxy por línea:
```
http://usuario:password@ip:puerto
http://ip:puerto
socks5://ip:puerto
```

## 🎯 Uso Básico

### Ver estado del sistema
```bash
python run_scrapers.py status
```

### Ejecutar un scraper
```bash
# Usar configuración global (proxy on/off según config)
python run_scrapers.py waxpeer

# Forzar uso de proxy
python run_scrapers.py waxpeer --proxy

# Forzar NO usar proxy
python run_scrapers.py waxpeer --no-proxy

# Ejecutar solo una vez (para pruebas)
python run_scrapers.py waxpeer --once
```

### Activar/Desactivar proxies globalmente
```bash
python run_scrapers.py toggle-proxy
```

## 🔄 Migración desde la Versión Antigua

### Paso 1: Migrar tus scrapers

Para cada par de archivos `Platform_noproxy.py` y `Platform_vproxy.py`, crea un único archivo en `backend/scrapers/platform_scraper.py`:

```python
# backend/scrapers/csdeals_scraper.py
from backend.core.base_scraper import BaseScraper

class CSDealsScraper(BaseScraper):
    def __init__(self, use_proxy=None):
        super().__init__('CSDeals', use_proxy)
        self.api_url = "https://cs.deals/API/IPricing/GetLowestPrices/v1?appid=730"
    
    def fetch_data(self):
        response = self.make_request(self.api_url)
        if response:
            return self.parse_response(response)
        return []
    
    def parse_response(self, response):
        # Tu lógica de parsing aquí
        data = response.json()
        items = []
        # ... procesar datos ...
        return items
```

### Paso 2: Copiar tus archivos de configuración

```bash
# Copiar configuraciones existentes
cp Configs/Language.json config/
cp Configs/Notifications.json config/notifications/thresholds.json
cp Configs/Api.json config/api_keys.json  # ⚠️ No subir a git!
```

### Paso 3: Actualizar el diccionario de scrapers

En `run_scrapers.py`, agregar tus scrapers migrados:

```python
from backend.scrapers.csdeals_scraper import CSDealsScraper
from backend.scrapers.empire_scraper import EmpireScraper

SCRAPERS = {
    'waxpeer': WaxpeerScraper,
    'csdeals': CSDealsScraper,    # Agregar
    'empire': EmpireScraper,       # Agregar
    # ... más scrapers
}
```

## 📁 Estructura del Proyecto

```
BOT-vCSGO-Beta/
├── backend/
│   ├── core/               # Sistema base
│   │   ├── base_scraper.py    # Clase base (elimina duplicación)
│   │   ├── config_manager.py  # Gestión de configuración
│   │   └── proxy_manager.py   # Gestión de proxies
│   │
│   └── scrapers/           # Tus scrapers
│       ├── waxpeer_scraper.py
│       ├── csdeals_scraper.py
│       └── ...
│
├── config/                 # Configuraciones
│   ├── settings.json          # Config principal
│   ├── scrapers/
│   │   └── platforms.json     # Config por plataforma
│   └── notifications/
│       └── thresholds.json    # Umbrales de notificación
│
├── JSON/                   # Salida de datos (generado)
├── logs/                   # Archivos de log (generado)
│
├── run_scrapers.py         # Script principal
├── requirements.txt        # Dependencias
├── proxy.txt              # Lista de proxies (crear)
└── README.md              # Este archivo
```

## ⚙️ Configuración Avanzada

### Cambiar intervalos de actualización

Editar `config/scrapers/platforms.json`:

```json
{
    "waxpeer": {
        "update_interval": 60,  // segundos
        "api_url": "https://..."
    }
}
```

### Cambiar umbrales de rentabilidad

Editar `config/notifications/thresholds.json`:

```json
{
    "profitability_waxpeer": 0.5,
    "profitability_empire": 1.2
}
```

### Variables de entorno (recomendado para API keys)

Crear archivo `.env`:
```
WAXPEER_API_KEY=tu-api-key
EMPIRE_API_KEY=tu-api-key
```

## 🐛 Solución de Problemas

### "No module named 'backend'"
```bash
# Asegúrate de ejecutar desde la raíz del proyecto
cd BOT-vCSGO-Beta
python run_scrapers.py status
```

### "No se encontró proxy.txt"
- El archivo proxy.txt es opcional
- Si quieres usar proxies, créalo en la raíz del proyecto
- Un proxy por línea

### "Error al conectar"
- Verifica tu conexión a internet
- Si usas proxy, verifica que funcionen
- Algunos sitios pueden bloquear requests frecuentes

## 🚦 Próximos Pasos

1. **Migrar todos tus scrapers** al nuevo formato
2. **Configurar la base de datos** (próximamente)
3. **Agregar interfaz web** (próximamente)
4. **Sistema de notificaciones** (próximamente)

## 📝 Notas de la Migración

### Ventajas del nuevo sistema:
- ✅ Un solo archivo por plataforma (no más _proxy y _noproxy)
- ✅ Configuración centralizada
- ✅ Gestión inteligente de proxies
- ✅ Mejor manejo de errores
- ✅ Logs estructurados
- ✅ Fácil de mantener y extender

### Lo que se mantiene igual:
- 📁 Los archivos JSON de salida tienen el mismo formato
- 🔄 La lógica de negocio es la misma
- 📊 Los cálculos de rentabilidad no cambian

## 🤝 Contribuir

1. Migra un scraper
2. Prueba que funcione
3. Documenta cualquier problema
4. Comparte mejoras

---

**Versión**: 2.0.0  
**Autor**: ZoluGames  
**Licencia**: MIT