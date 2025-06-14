# backend/services/websocket_service.py

import asyncio
from pathlib import Path
import websockets
import json
from datetime import datetime
from typing import Set, Dict, Any
from loguru import logger
import threading
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.services.database_service import get_database_service
from backend.services.notification_service import get_notification_service


class WebSocketService:
    """Servicio de WebSocket para actualizaciones en tiempo real"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.db_service = get_database_service()
        self.notification_service = get_notification_service()
        self.logger = logger.bind(service="WebSocketService")
        self.server = None
        self.running = False
    
    async def register(self, websocket):
        """Registra un nuevo cliente"""
        self.clients.add(websocket)
        self.logger.info(f"Cliente conectado. Total: {len(self.clients)}")
        
        # Enviar estado inicial
        await self.send_initial_state(websocket)
    
    async def unregister(self, websocket):
        """Desregistra un cliente"""
        self.clients.remove(websocket)
        self.logger.info(f"Cliente desconectado. Total: {len(self.clients)}")
    
    async def send_initial_state(self, websocket):
        """Envía el estado inicial a un nuevo cliente"""
        try:
            # Obtener datos actuales
            opportunities = self.db_service.get_profitable_opportunities(limit=20)
            scrapers_status = self.db_service.get_scrapers_status()
            
            initial_data = {
                "type": "initial_state",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "opportunities": opportunities,
                    "scrapers": scrapers_status,
                    "stats": self.get_current_stats()
                }
            }
            
            await websocket.send(json.dumps(initial_data))
            
        except Exception as e:
            self.logger.error(f"Error enviando estado inicial: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Envía un mensaje a todos los clientes conectados"""
        if self.clients:
            message_json = json.dumps(message)
            
            # Crear lista de tareas de envío
            tasks = []
            for client in self.clients.copy():
                tasks.append(self.send_to_client(client, message_json))
            
            # Ejecutar todas las tareas
            await asyncio.gather(*tasks)
    
    async def send_to_client(self, client, message):
        """Envía mensaje a un cliente específico"""
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            await self.unregister(client)
        except Exception as e:
            self.logger.error(f"Error enviando a cliente: {e}")
    
    async def handle_client(self, websocket, path):
        """Maneja la conexión de un cliente"""
        await self.register(websocket)
        
        try:
            async for message in websocket:
                # Procesar mensajes del cliente
                try:
                    data = json.loads(message)
                    await self.process_client_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def process_client_message(self, websocket, data: Dict):
        """Procesa mensajes recibidos del cliente"""
        msg_type = data.get("type")
        
        if msg_type == "ping":
            # Responder a ping
            await websocket.send(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
            
        elif msg_type == "get_opportunities":
            # Enviar oportunidades actualizadas
            opportunities = self.db_service.get_profitable_opportunities(
                limit=data.get("limit", 50)
            )
            await websocket.send(json.dumps({
                "type": "opportunities_update",
                "data": opportunities
            }))
            
        elif msg_type == "get_stats":
            # Enviar estadísticas
            await websocket.send(json.dumps({
                "type": "stats_update",
                "data": self.get_current_stats()
            }))
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Obtiene las estadísticas actuales del sistema"""
        try:
            session = self.db_service.db_manager.get_session()
            from backend.database.models import Item, ProfitableOpportunity
            
            total_items = session.query(Item).count()
            active_opportunities = session.query(ProfitableOpportunity).filter_by(
                is_active=True
            ).count()
            
            best_opp = session.query(ProfitableOpportunity).filter_by(
                is_active=True
            ).order_by(ProfitableOpportunity.profitability.desc()).first()
            
            session.close()
            
            return {
                "total_items": total_items,
                "active_opportunities": active_opportunities,
                "best_profit_percentage": best_opp.profitability * 100 if best_opp else 0,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    async def notify_opportunity(self, opportunity: Dict):
        """Notifica una nueva oportunidad a todos los clientes"""
        await self.broadcast({
            "type": "new_opportunity",
            "timestamp": datetime.now().isoformat(),
            "data": opportunity
        })
    
    async def notify_scraper_update(self, scraper_name: str, status: str):
        """Notifica actualización de estado de un scraper"""
        await self.broadcast({
            "type": "scraper_update",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "scraper": scraper_name,
                "status": status
            }
        })
    
    async def start_server(self):
        """Inicia el servidor WebSocket"""
        self.logger.info(f"Iniciando servidor WebSocket en ws://{self.host}:{self.port}")
        
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        self.running = True
        
        # Mantener el servidor ejecutándose
        await asyncio.Future()  # run forever
    
    def start(self):
        """Inicia el servidor en un thread separado"""
        def run_server():
            asyncio.new_event_loop().run_until_complete(self.start_server())
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        self.logger.info("Servidor WebSocket iniciado en background")
    
    def stop(self):
        """Detiene el servidor"""
        self.running = False
        if self.server:
            self.server.close()
        self.logger.info("Servidor WebSocket detenido")


# Singleton
_websocket_service = None

def get_websocket_service():
    """Obtiene la instancia singleton del WebSocketService"""
    global _websocket_service
    if _websocket_service is None:
        _websocket_service = WebSocketService()
    return _websocket_service


# Script para ejecutar el servidor standalone
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    service = WebSocketService()
    
    print("\n" + "="*60)
    print("SERVIDOR WEBSOCKET - BOT-vCSGO-Beta")
    print("="*60)
    print(f"Escuchando en: ws://localhost:8765")
    print("Presiona Ctrl+C para detener\n")
    
    try:
        asyncio.run(service.start_server())
    except KeyboardInterrupt:
        print("\nServidor detenido")