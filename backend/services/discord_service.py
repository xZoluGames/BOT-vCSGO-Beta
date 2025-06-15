# backend/services/discord_service.py
import aiohttp

from backend.services.profitability_service import ProfitableItem

class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_opportunity(self, item: ProfitableItem):
        embed = {
            "title": f"💰 Oportunidad: {item.rentabilidad_percentage:.1f}%",
            "description": item.name,
            "color": 0x00ff00,
            "fields": [
                {"name": "Comprar en", "value": f"{item.buy_platform}\n${item.buy_price:.2f}", "inline": True},
                {"name": "Vender en", "value": f"Steam\n${item.steam_price:.2f}", "inline": True},
                {"name": "Ganancia", "value": f"${item.profit:.2f}", "inline": True}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_url, json={"embeds": [embed]})