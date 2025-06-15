# web_server.py - Servidor FastAPI para control de scrapers

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
import asyncio
import json
import subprocess
import threading
import queue
import time
from datetime import datetime
from pathlib import Path
import sys
from pydantic import BaseModel
from loguru import logger

sys.path.append(str(Path(__file__).parent))

from backend.core.config_manager import get_config_manager
from backend.services.database_service import get_database_service
from backend.services.profitability_service import ProfitabilityService
from backend.scrapers import *

# Modelos Pydantic
class ScraperConfig(BaseModel):
    name: str
    enabled: bool = True
    use_proxy: bool = False
    interval: int = 60
    max_retries: int = 5
    timeout: int = 10
    custom_headers: Optional[Dict[str, str]] = None
    custom_params: Optional[Dict[str, Any]] = None

class ScraperCommand(BaseModel):
    action: str  # start, stop, restart
    scraper_name: str
    config: Optional[ScraperConfig] = None

class SystemCommand(BaseModel):
    action: str  # start_monitor, stop_monitor, run_profitability
    params: Optional[Dict[str, Any]] = None

# Aplicación FastAPI
app = FastAPI(title="BOT-vCSGO-Beta Control Panel", version="2.0.0")

# CORS para permitir conexiones del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manager de scrapers
class ScraperManager:
    def __init__(self):
        self.scrapers = {}
        self.processes = {}
        self.configs = {}
        self.logs = {}
        self.websocket_clients = set()
        self.config_manager = get_config_manager()
        self.db_service = get_database_service()
        
        # Cargar configuraciones guardadas
        self.load_scraper_configs()
        
        # Cola de logs
        self.log_queue = queue.Queue()
        
        # Inicializar scrapers disponibles
        self.available_scrapers = {
            'waxpeer': 'WaxpeerScraper',
            'csdeals': 'CSDealsScraper',
            'empire': 'EmpireScraper',
            'skinport': 'SkinportScraper',
            'cstrade': 'CstradeScraper',
            'bitskins': 'BitskinsScraper',
            'marketcsgo': 'MarketCSGOScraper',
            'manncostore': 'ManncoStoreScraper',
            'tradeit': 'TradeitScraper',
            'skindeck': 'SkindeckScraper',
            'white': 'WhiteScraper',
            'lisskins': 'LisskinsScraper',
            'shadowpay': 'ShadowpayScraper',
            'skinout': 'SkinoutScraper',
            'rapidskins': 'RapidskinsScraper',
            'steammarket': 'SteamMarketScraper',
            'steamnames': 'SteamNamesScraper',
            'steamid': 'SteamIDScraper',
            'steamlisting': 'SteamListingScraper'
        }
    
    def load_scraper_configs(self):
        """Carga configuraciones guardadas de scrapers"""
        config_file = Path("config/scraper_configs.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.configs = json.load(f)
            except:
                self.configs = {}
    
    def save_scraper_configs(self):
        """Guarda configuraciones de scrapers"""
        config_file = Path("config/scraper_configs.json")
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(self.configs, f, indent=2)
    
    def start_scraper(self, scraper_name: str, config: Optional[ScraperConfig] = None):
        """Inicia un scraper con configuración específica"""
        if scraper_name in self.processes:
            raise HTTPException(status_code=400, detail=f"Scraper {scraper_name} ya está ejecutándose")
        
        # Guardar configuración si se proporciona
        if config:
            self.configs[scraper_name] = config.dict()
            self.save_scraper_configs()
        
        # Obtener configuración
        scraper_config = self.configs.get(scraper_name, {})
        
        def run_scraper():
            try:
                # Construir comando
                cmd = [sys.executable, "run_scrapers.py", scraper_name]
                
                if scraper_config.get('use_proxy'):
                    cmd.append('--proxy')
                
                # Ejecutar proceso
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                self.processes[scraper_name] = process
                
                # Leer salida línea por línea
                for line in iter(process.stdout.readline, ''):
                    if line:
                        log_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'scraper': scraper_name,
                            'message': line.strip(),
                            'level': self._detect_log_level(line)
                        }
                        
                        # Agregar a cola de logs
                        self.log_queue.put(log_entry)
                        
                        # Guardar en historial
                        if scraper_name not in self.logs:
                            self.logs[scraper_name] = []
                        self.logs[scraper_name].append(log_entry)
                        
                        # Mantener solo últimos 1000 logs por scraper
                        if len(self.logs[scraper_name]) > 1000:
                            self.logs[scraper_name] = self.logs[scraper_name][-1000:]
                
                process.wait()
                
            except Exception as e:
                logger.error(f"Error ejecutando {scraper_name}: {e}")
            finally:
                if scraper_name in self.processes:
                    del self.processes[scraper_name]
        
        # Ejecutar en thread
        thread = threading.Thread(target=run_scraper, daemon=True)
        thread.start()
        
        return {"status": "started", "scraper": scraper_name}
    
    def stop_scraper(self, scraper_name: str):
        """Detiene un scraper"""
        if scraper_name not in self.processes:
            raise HTTPException(status_code=400, detail=f"Scraper {scraper_name} no está ejecutándose")
        
        process = self.processes[scraper_name]
        process.terminate()
        
        # Esperar un poco y forzar si es necesario
        time.sleep(2)
        if process.poll() is None:
            process.kill()
        
        del self.processes[scraper_name]
        
        return {"status": "stopped", "scraper": scraper_name}
    
    def get_scraper_status(self, scraper_name: str):
        """Obtiene el estado de un scraper"""
        is_running = scraper_name in self.processes
        config = self.configs.get(scraper_name, {})
        
        # Obtener estadísticas de la base de datos
        db_stats = {}
        try:
            scrapers_status = self.db_service.get_scrapers_status()
            for status in scrapers_status:
                if status['name'] == scraper_name:
                    db_stats = status
                    break
        except:
            pass
        
        return {
            'name': scraper_name,
            'running': is_running,
            'config': config,
            'stats': db_stats,
            'logs': self.logs.get(scraper_name, [])[-50:]  # Últimos 50 logs
        }
    
    def get_all_scrapers_status(self):
        """Obtiene el estado de todos los scrapers"""
        status_list = []
        
        for scraper_name in self.available_scrapers:
            status_list.append(self.get_scraper_status(scraper_name))
        
        return status_list
    
    def _detect_log_level(self, line: str) -> str:
        """Detecta el nivel de log de una línea"""
        line_lower = line.lower()
        
        if 'error' in line_lower or 'exception' in line_lower:
            return 'ERROR'
        elif 'warning' in line_lower or 'warn' in line_lower:
            return 'WARNING'
        elif 'success' in line_lower or 'completado' in line_lower:
            return 'SUCCESS'
        elif 'info' in line_lower:
            return 'INFO'
        else:
            return 'DEBUG'
    
    async def broadcast_log(self, log_entry: dict):
        """Envía log a todos los clientes WebSocket conectados"""
        disconnected = set()
        
        for websocket in self.websocket_clients:
            try:
                await websocket.send_json({
                    'type': 'log',
                    'data': log_entry
                })
            except:
                disconnected.add(websocket)
        
        # Limpiar clientes desconectados
        self.websocket_clients -= disconnected

# Instancia global del manager
scraper_manager = ScraperManager()

# Rutas de la API
@app.get("/")
async def root():
    """Sirve la página principal"""
    return FileResponse('static/index.html')

@app.get("/api/scrapers")
async def get_scrapers():
    """Obtiene la lista de todos los scrapers y su estado"""
    return scraper_manager.get_all_scrapers_status()

@app.get("/api/scrapers/{scraper_name}")
async def get_scraper(scraper_name: str):
    """Obtiene el estado de un scraper específico"""
    if scraper_name not in scraper_manager.available_scrapers:
        raise HTTPException(status_code=404, detail="Scraper no encontrado")
    
    return scraper_manager.get_scraper_status(scraper_name)

@app.post("/api/scrapers/{scraper_name}/start")
async def start_scraper(scraper_name: str, config: Optional[ScraperConfig] = None):
    """Inicia un scraper"""
    if scraper_name not in scraper_manager.available_scrapers:
        raise HTTPException(status_code=404, detail="Scraper no encontrado")
    
    return scraper_manager.start_scraper(scraper_name, config)

@app.post("/api/scrapers/{scraper_name}/stop")
async def stop_scraper(scraper_name: str):
    """Detiene un scraper"""
    return scraper_manager.stop_scraper(scraper_name)

@app.post("/api/scrapers/{scraper_name}/restart")
async def restart_scraper(scraper_name: str):
    """Reinicia un scraper"""
    try:
        scraper_manager.stop_scraper(scraper_name)
    except:
        pass
    
    time.sleep(2)
    return scraper_manager.start_scraper(scraper_name)

@app.post("/api/scrapers/{scraper_name}/config")
async def update_scraper_config(scraper_name: str, config: ScraperConfig):
    """Actualiza la configuración de un scraper"""
    if scraper_name not in scraper_manager.available_scrapers:
        raise HTTPException(status_code=404, detail="Scraper no encontrado")
    
    scraper_manager.configs[scraper_name] = config.dict()
    scraper_manager.save_scraper_configs()
    
    return {"status": "updated", "config": config.dict()}

@app.get("/api/scrapers/{scraper_name}/logs")
async def get_scraper_logs(scraper_name: str, limit: int = 100):
    """Obtiene los logs de un scraper"""
    logs = scraper_manager.logs.get(scraper_name, [])
    return logs[-limit:]

@app.get("/api/profitability")
async def get_profitability():
    """Obtiene las oportunidades rentables actuales"""
    try:
        opportunities = scraper_manager.db_service.get_profitable_opportunities(limit=100)
        return opportunities
    except Exception as e:
        return []

@app.post("/api/profitability/analyze")
async def run_profitability_analysis():
    """Ejecuta análisis de rentabilidad"""
    try:
        service = ProfitabilityService()
        service.run()
        return {"status": "success", "message": "Análisis completado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Obtiene estadísticas del sistema"""
    try:
        session = scraper_manager.db_service.db_manager.get_session()
        from backend.database.models import Item, ProfitableOpportunity
        
        stats = {
            'total_items': session.query(Item).count(),
            'active_opportunities': session.query(ProfitableOpportunity).filter_by(is_active=True).count(),
            'running_scrapers': len(scraper_manager.processes),
            'total_scrapers': len(scraper_manager.available_scrapers)
        }
        
        session.close()
        return stats
        
    except Exception as e:
        return {
            'total_items': 0,
            'active_opportunities': 0,
            'running_scrapers': len(scraper_manager.processes),
            'total_scrapers': len(scraper_manager.available_scrapers)
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para logs en tiempo real"""
    await websocket.accept()
    scraper_manager.websocket_clients.add(websocket)
    
    try:
        # Enviar estado inicial
        await websocket.send_json({
            'type': 'initial_state',
            'data': {
                'scrapers': scraper_manager.get_all_scrapers_status(),
                'stats': await get_stats()
            }
        })
        
        # Mantener conexión y enviar logs
        while True:
            try:
                # Verificar si hay logs nuevos
                if not scraper_manager.log_queue.empty():
                    log_entry = scraper_manager.log_queue.get()
                    await scraper_manager.broadcast_log(log_entry)
                
                await asyncio.sleep(0.1)
                
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        scraper_manager.websocket_clients.discard(websocket)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    
    # Crear carpeta static si no existe
    Path("static").mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print("BOT-vCSGO-Beta - Panel de Control Web")
    print("="*60)
    print("Servidor iniciado en: http://localhost:8000")
    print("Presiona Ctrl+C para detener\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)