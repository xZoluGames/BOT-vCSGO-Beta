# backend/trading/auto_trader.py
from venv import logger
from backend.services.profitability_service import ProfitableItem


class AutoTrader:
    def __init__(self):
        self.min_profit = 0.15  # 15% mínimo
        self.max_investment = 1000  # $1000 máximo por item
        self.platforms = self._init_platform_apis()
    
    async def execute_trade(self, opportunity: ProfitableItem):
        """Ejecuta una compra automática si cumple criterios"""
        if opportunity.rentabilidad_percentage < self.min_profit * 100:
            return
        
        if opportunity.buy_price > self.max_investment:
            return
        
        # Verificar fondos disponibles
        balance = await self.get_platform_balance(opportunity.buy_platform)
        if balance < opportunity.buy_price:
            return
        
        # Ejecutar compra
        try:
            order = await self.platforms[opportunity.buy_platform].buy_item(
                item_name=opportunity.name,
                max_price=opportunity.buy_price * 1.02  # 2% margen
            )
            
            # Registrar en base de datos
            await self.log_trade(order)
            
            # Notificar
            await self.notify_trade_executed(order)
            
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")