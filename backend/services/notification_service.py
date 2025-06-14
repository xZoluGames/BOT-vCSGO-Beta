# backend/services/notification_service.py


import json
import time
import platform
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
import winsound  # Solo Windows

from backend.core.config_manager import get_config_manager
from backend.core.translator import get_translator


@dataclass
class Notification:
    """Representa una notificación"""
    title: str
    message: str
    level: str = "INFO"  # INFO, WARNING, OPPORTUNITY
    data: Optional[Dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class NotificationService:
    """Servicio de notificaciones simple"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.translator = get_translator('notifications', self.config_manager.get_language_config())
        self.logger = logger.bind(service="NotificationService")
        
        # Cargar configuración
        self.enabled = self.config_manager.settings.get('notifications', {}).get('enabled', True)
        self.sound_enabled = self.config_manager.settings.get('notifications', {}).get('sound', True)
        self.min_profit_alert = self.config_manager.settings.get('notifications', {}).get('min_profit_percentage', 10.0)
        
        # Archivo de log de notificaciones
        self.notifications_file = Path("logs/notifications.json")
        self.notifications_file.parent.mkdir(exist_ok=True)
        
        # Cache para evitar notificaciones duplicadas
        self._sent_notifications = set()
        self._last_cleanup = time.time()
    
    def _play_sound(self, sound_type: str = "alert"):
        """Reproduce un sonido de alerta"""
        if not self.sound_enabled or platform.system() != 'Windows':
            return
            
        try:
            if sound_type == "opportunity":
                winsound.Beep(3000, 200)  # Tono alto para oportunidades
                time.sleep(0.1)
                winsound.Beep(3000, 200)
            else:
                winsound.Beep(2000, 150)  # Tono normal
        except:
            pass  # Silenciar errores de sonido
    
    def _save_to_file(self, notification: Notification):
        """Guarda la notificación en archivo"""
        try:
            # Leer notificaciones existentes
            notifications = []
            if self.notifications_file.exists():
                with open(self.notifications_file, 'r', encoding='utf-8') as f:
                    notifications = json.load(f)
            
            # Agregar nueva notificación
            notifications.append({
                'timestamp': notification.timestamp.isoformat(),
                'level': notification.level,
                'title': notification.title,
                'message': notification.message,
                'data': notification.data
            })
            
            # Mantener solo las últimas 1000 notificaciones
            if len(notifications) > 1000:
                notifications = notifications[-1000:]
            
            # Guardar
            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                json.dump(notifications, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando notificación: {e}")
    
    def _clean_cache(self):
        """Limpia el cache de notificaciones enviadas cada hora"""
        current_time = time.time()
        if current_time - self._last_cleanup > 3600:  # 1 hora
            self._sent_notifications.clear()
            self._last_cleanup = current_time
    
    def send(self, title: str, message: str, level: str = "INFO", data: Optional[Dict] = None):
        """Envía una notificación"""
        if not self.enabled:
            return
        
        # Limpiar cache periódicamente
        self._clean_cache()
        
        # Crear notificación
        notification = Notification(
            title=title,
            message=message,
            level=level,
            data=data
        )
        
        # Verificar si ya se envió (evitar spam)
        notification_key = f"{title}:{message}"
        if notification_key in self._sent_notifications and level != "OPPORTUNITY":
            return
        
        # Marcar como enviada
        self._sent_notifications.add(notification_key)
        
        # Mostrar en consola con formato
        self._print_notification(notification)
        
        # Reproducir sonido si corresponde
        if level == "OPPORTUNITY":
            self._play_sound("opportunity")
        elif level == "WARNING":
            self._play_sound("alert")
        
        # Guardar en archivo
        self._save_to_file(notification)
    
    def _print_notification(self, notification: Notification):
        """Imprime la notificación en consola con formato"""
        # Colores según nivel
        colors = {
            "INFO": "\033[94m",      # Azul
            "WARNING": "\033[93m",   # Amarillo
            "OPPORTUNITY": "\033[92m" # Verde
        }
        reset = "\033[0m"
        color = colors.get(notification.level, "")
        
        # Formato de notificación
        print(f"\n{color}{'='*60}")
        print(f"🔔 {notification.title}")
        print(f"{'='*60}{reset}")
        print(f"📅 {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📝 {notification.message}")
        
        if notification.data:
            print(f"\n📊 Detalles:")
            for key, value in notification.data.items():
                print(f"   • {key}: {value}")
        
        print(f"{color}{'='*60}{reset}\n")
    
    def notify_opportunity(self, item_name: str, buy_platform: str, buy_price: float, 
                          profit_percentage: float, profit_amount: float):
        """Notifica una oportunidad rentable"""
        if profit_percentage < self.min_profit_alert:
            return
        
        title = f"💰 OPORTUNIDAD RENTABLE: {profit_percentage:.1f}%"
        message = f"{item_name} - Comprar en {buy_platform} por ${buy_price:.2f}"
        
        data = {
            "Item": item_name,
            "Plataforma": buy_platform,
            "Precio Compra": f"${buy_price:.2f}",
            "Rentabilidad": f"{profit_percentage:.1f}%",
            "Ganancia": f"${profit_amount:.2f}"
        }
        
        self.send(title, message, "OPPORTUNITY", data)
    
    def notify_scraper_error(self, scraper_name: str, error: str):
        """Notifica un error en un scraper"""
        title = f"⚠️ ERROR EN SCRAPER: {scraper_name}"
        message = f"Error: {error}"
        
        self.send(title, message, "WARNING", {"Scraper": scraper_name, "Error": error})
    
    def notify_summary(self, opportunities_count: int, best_profit: float, total_scrapers: int):
        """Notifica un resumen de análisis"""
        title = "📈 RESUMEN DE ANÁLISIS"
        message = f"Encontradas {opportunities_count} oportunidades rentables"
        
        data = {
            "Oportunidades": opportunities_count,
            "Mejor Rentabilidad": f"{best_profit:.1f}%",
            "Scrapers Activos": total_scrapers
        }
        
        self.send(title, message, "INFO", data)
    
    def get_recent_notifications(self, limit: int = 50) -> List[Dict]:
        """Obtiene las notificaciones recientes"""
        try:
            if self.notifications_file.exists():
                with open(self.notifications_file, 'r', encoding='utf-8') as f:
                    notifications = json.load(f)
                    return notifications[-limit:]
            return []
        except Exception as e:
            self.logger.error(f"Error leyendo notificaciones: {e}")
            return []


# Singleton
_notification_service = None

def get_notification_service():
    """Obtiene la instancia singleton del NotificationService"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service