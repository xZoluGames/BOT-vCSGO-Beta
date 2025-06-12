# backend/services/notification_service.py

import asyncio
import smtplib
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
from dataclasses import dataclass
import logging

@dataclass
class Notification:
    """Estructura de una notificación"""
    title: str
    message: str
    type: str  # 'opportunity', 'alert', 'info'
    data: Dict[str, Any]
    priority: int = 1  # 1-5, donde 5 es la más alta
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class NotificationChannel(ABC):
    """Clase base para canales de notificación"""
    
    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Envía una notificación por el canal"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Verifica si el canal está configurado"""
        pass

class WebSocketChannel(NotificationChannel):
    """Canal de notificación por WebSocket"""
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def send(self, notification: Notification) -> bool:
        try:
            message = {
                "type": "notification",
                "data": {
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.type,
                    "priority": notification.priority,
                    "timestamp": notification.timestamp.isoformat(),
                    "data": notification.data
                }
            }
            
            await self.connection_manager.broadcast(json.dumps(message))
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación WebSocket: {e}")
            return False
            
    def is_configured(self) -> bool:
        return self.connection_manager is not None

class TelegramChannel(NotificationChannel):
    """Canal de notificación por Telegram"""
    
    def __init__(self, bot_token: str, chat_ids: List[str]):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def send(self, notification: Notification) -> bool:
        if not self.is_configured():
            return False
            
        try:
            # Formatear mensaje para Telegram
            message = self._format_telegram_message(notification)
            
            # Enviar a todos los chat IDs configurados
            async with aiohttp.ClientSession() as session:
                for chat_id in self.chat_ids:
                    url = f"{self.base_url}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True
                    }
                    
                    async with session.post(url, json=payload) as response:
                        if response.status != 200:
                            self.logger.error(f"Error enviando a Telegram: {await response.text()}")
                            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación Telegram: {e}")
            return False
            
    def _format_telegram_message(self, notification: Notification) -> str:
        """Formatea el mensaje para Telegram con HTML"""
        priority_emojis = {1: "ℹ️", 2: "📢", 3: "⚡", 4: "🔥", 5: "🚨"}
        emoji = priority_emojis.get(notification.priority, "📌")
        
        message = f"{emoji} <b>{notification.title}</b>\n\n"
        message += f"{notification.message}\n\n"
        
        if notification.type == "opportunity" and notification.data:
            data = notification.data
            message += f"💰 <b>Rentabilidad:</b> {data.get('profitability', 0):.2f}%\n"
            message += f"🛒 <b>Comprar en:</b> {data.get('platform', 'N/A')} - ${data.get('buy_price', 0):.2f}\n"
            message += f"💵 <b>Vender en:</b> Steam - ${data.get('steam_price', 0):.2f}\n"
            message += f"📈 <b>Ganancia:</b> ${data.get('profit', 0):.2f}\n\n"
            
            if data.get('url'):
                message += f"🔗 <a href='{data['url']}'>Ver en {data.get('platform', 'plataforma')}</a>"
                
        return message
        
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_ids)

class DiscordChannel(NotificationChannel):
    """Canal de notificación por Discord"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def send(self, notification: Notification) -> bool:
        if not self.is_configured():
            return False
            
        try:
            # Crear embed de Discord
            embed = self._create_discord_embed(notification)
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "embeds": [embed],
                    "username": "CS:GO Arbitrage Bot"
                }
                
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 204
                    
        except Exception as e:
            self.logger.error(f"Error enviando notificación Discord: {e}")
            return False
            
    def _create_discord_embed(self, notification: Notification) -> Dict:
        """Crea un embed de Discord"""
        colors = {
            "opportunity": 0x00ff00,  # Verde
            "alert": 0xff0000,        # Rojo
            "info": 0x0099ff          # Azul
        }
        
        embed = {
            "title": notification.title,
            "description": notification.message,
            "color": colors.get(notification.type, 0x808080),
            "timestamp": notification.timestamp.isoformat(),
            "fields": []
        }
        
        if notification.type == "opportunity" and notification.data:
            data = notification.data
            embed["fields"] = [
                {
                    "name": "💰 Rentabilidad",
                    "value": f"{data.get('profitability', 0):.2f}%",
                    "inline": True
                },
                {
                    "name": "🛒 Comprar en",
                    "value": f"{data.get('platform', 'N/A')} - ${data.get('buy_price', 0):.2f}",
                    "inline": True
                },
                {
                    "name": "💵 Vender en",
                    "value": f"Steam - ${data.get('steam_price', 0):.2f}",
                    "inline": True
                },
                {
                    "name": "📈 Ganancia Potencial",
                    "value": f"${data.get('profit', 0):.2f}",
                    "inline": True
                }
            ]
            
            if data.get('url'):
                embed["url"] = data['url']
                
        return embed
        
    def is_configured(self) -> bool:
        return bool(self.webhook_url)

class EmailChannel(NotificationChannel):
    """Canal de notificación por Email"""
    
    def __init__(self, smtp_config: Dict[str, Any], recipients: List[str]):
        self.smtp_config = smtp_config
        self.recipients = recipients
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def send(self, notification: Notification) -> bool:
        if not self.is_configured():
            return False
            
        try:
            # Ejecutar en thread pool para no bloquear
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._send_email, notification)
            
        except Exception as e:
            self.logger.error(f"Error enviando notificación Email: {e}")
            return False
            
    def _send_email(self, notification: Notification) -> bool:
        """Envía el email (síncrono)"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = notification.title
        msg['From'] = self.smtp_config['from_email']
        msg['To'] = ', '.join(self.recipients)
        
        # Crear versión HTML del email
        html_content = self._create_email_html(notification)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Enviar email
        with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
            if self.smtp_config.get('use_tls'):
                server.starttls()
            if self.smtp_config.get('username'):
                server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
            
        return True
        
    def _create_email_html(self, notification: Notification) -> str:
        """Crea el contenido HTML del email"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .opportunity {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .stat {{ text-align: center; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{notification.title}</h1>
                </div>
                <div class="content">
                    <p>{notification.message}</p>
        """
        
        if notification.type == "opportunity" and notification.data:
            data = notification.data
            html += f"""
                    <div class="opportunity">
                        <h2>Detalles de la Oportunidad</h2>
                        <div class="stats">
                            <div class="stat">
                                <h3>{data.get('profitability', 0):.2f}%</h3>
                                <p>Rentabilidad</p>
                            </div>
                            <div class="stat">
                                <h3>${data.get('buy_price', 0):.2f}</h3>
                                <p>Precio Compra ({data.get('platform', 'N/A')})</p>
                            </div>
                            <div class="stat">
                                <h3>${data.get('steam_price', 0):.2f}</h3>
                                <p>Precio Steam</p>
                            </div>
                            <div class="stat">
                                <h3>${data.get('profit', 0):.2f}</h3>
                                <p>Ganancia</p>
                            </div>
                        </div>
                        {f'<a href="{data["url"]}" class="button">Ver en {data.get("platform", "plataforma")}</a>' if data.get('url') else ''}
                    </div>
            """
            
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    def is_configured(self) -> bool:
        return bool(self.smtp_config and self.recipients)

class NotificationService:
    """Servicio principal de notificaciones"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.channels: List[NotificationChannel] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_channels()
        
    def _setup_channels(self):
        """Configura los canales disponibles"""
        
        # WebSocket (siempre disponible si hay connection_manager)
        if self.config.get('websocket_manager'):
            self.channels.append(WebSocketChannel(self.config['websocket_manager']))
            
        # Telegram
        telegram_config = self.config.get('telegram', {})
        if telegram_config.get('bot_token'):
            self.channels.append(TelegramChannel(
                telegram_config['bot_token'],
                telegram_config.get('chat_ids', [])
            ))
            
        # Discord
        discord_config = self.config.get('discord', {})
        if discord_config.get('webhook_url'):
            self.channels.append(DiscordChannel(discord_config['webhook_url']))
            
        # Email
        email_config = self.config.get('email', {})
        if email_config.get('smtp'):
            self.channels.append(EmailChannel(
                email_config['smtp'],
                email_config.get('recipients', [])
            ))
            
        self.logger.info(f"Canales configurados: {len(self.channels)}")
        
    async def send_notification(self, 
                              title: str, 
                              message: str, 
                              type: str = "info",
                              data: Dict[str, Any] = None,
                              priority: int = 1,
                              channels: List[str] = None) -> bool:
        """
        Envía una notificación por los canales configurados
        
        Args:
            title: Título de la notificación
            message: Mensaje principal
            type: Tipo de notificación ('opportunity', 'alert', 'info')
            data: Datos adicionales
            priority: Prioridad (1-5)
            channels: Lista de canales específicos (None = todos)
        """
        
        notification = Notification(
            title=title,
            message=message,
            type=type,
            data=data or {},
            priority=priority
        )
        
        # Filtrar por prioridad mínima
        min_priority = self.config.get('min_priority', 1)
        if notification.priority < min_priority:
            self.logger.debug(f"Notificación ignorada por baja prioridad: {priority} < {min_priority}")
            return False
            
        # Enviar por todos los canales configurados
        results = []
        for channel in self.channels:
            if channels and channel.__class__.__name__ not in channels:
                continue
                
            try:
                result = await channel.send(notification)
                results.append(result)
                if not result:
                    self.logger.warning(f"Fallo al enviar por {channel.__class__.__name__}")
            except Exception as e:
                self.logger.error(f"Error en canal {channel.__class__.__name__}: {e}")
                results.append(False)
                
        return any(results)  # True si al menos un canal tuvo éxito
        
    async def send_opportunity_notification(self, opportunity: Dict[str, Any]) -> bool:
        """Envía una notificación de oportunidad de arbitraje"""
        
        title = f"🎯 Nueva Oportunidad: {opportunity['item_name']}"
        message = f"Rentabilidad del {opportunity['profitability_percentage']:.2f}% detectada"
        
        # Determinar prioridad basada en rentabilidad
        profitability = opportunity['profitability_percentage']
        if profitability >= 20:
            priority = 5
        elif profitability >= 15:
            priority = 4
        elif profitability >= 10:
            priority = 3
        elif profitability >= 5:
            priority = 2
        else:
            priority = 1
            
        data = {
            'item_name': opportunity['item_name'],
            'platform': opportunity['buy_platform'],
            'buy_price': opportunity['buy_price'],
            'steam_price': opportunity['steam_price'],
            'profitability': opportunity['profitability_percentage'],
            'profit': opportunity['potential_profit'],
            'url': opportunity.get('buy_url')
        }
        
        return await self.send_notification(
            title=title,
            message=message,
            type="opportunity",
            data=data,
            priority=priority
        )

# Configuración de ejemplo
if __name__ == "__main__":
    config = {
        'telegram': {
            'bot_token': 'YOUR_BOT_TOKEN',
            'chat_ids': ['YOUR_CHAT_ID']
        },
        'discord': {
            'webhook_url': 'YOUR_WEBHOOK_URL'
        },
        'email': {
            'smtp': {
                'host': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'username': 'your_email@gmail.com',
                'password': 'your_app_password',
                'from_email': 'CS:GO Bot <your_email@gmail.com>'
            },
            'recipients': ['recipient@example.com']
        },
        'min_priority': 2
    }
    
    # Ejemplo de uso
    async def test():
        service = NotificationService(config)
        
        await service.send_opportunity_notification({
            'item_name': 'AK-47 | Redline (Field-Tested)',
            'buy_platform': 'Waxpeer',
            'buy_price': 25.50,
            'steam_price': 32.00,
            'profitability_percentage': 15.5,
            'potential_profit': 4.50,
            'buy_url': 'https://waxpeer.com/...'
        })
        
    asyncio.run(test())