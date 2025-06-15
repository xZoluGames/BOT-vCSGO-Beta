# backend/services/telegram_service.py
import telegram
from telegram import Bot
from backend.core.config_manager import get_config_manager
from backend.services.profitability_service import ProfitableItem

class TelegramNotifier:
    def __init__(self):
        config = get_config_manager()
        self.bot = Bot(token=config.get_telegram_token())
        self.chat_id = config.get_telegram_chat_id()
    
    async def send_opportunity(self, item: ProfitableItem):
        message = f"""
💰 *Nueva Oportunidad Detectada!*
        
📦 Item: {item.name}
💳 Comprar en: {item.buy_platform} - ${item.buy_price:.2f}
💵 Vender en: Steam - ${item.steam_price:.2f}
📈 Rentabilidad: {item.rentabilidad_percentage:.1f}%
💰 Ganancia: ${item.profit:.2f}

🔗 [Comprar]({item.buy_url}) | [Steam]({item.steam_link})
"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode='Markdown'
        )