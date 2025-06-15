# backend/services/alert_service.py
import datetime

from backend.services.profitability_service import ProfitableItem


class SmartAlertService:
    def __init__(self):
        self.user_preferences = {}
        self.alert_history = {}
    
    def should_alert(self, user_id: str, opportunity: ProfitableItem) -> bool:
        """Determina si enviar alerta basado en preferencias del usuario"""
        prefs = self.user_preferences.get(user_id, {})
        
        # Verificar criterios
        if opportunity.rentabilidad_percentage < prefs.get('min_profit', 10):
            return False
        
        if opportunity.buy_price > prefs.get('max_price', float('inf')):
            return False
        
        # Evitar spam - máximo 1 alerta por item cada 30 minutos
        last_alert = self.alert_history.get(f"{user_id}:{opportunity.name}")
        if last_alert and (datetime.now() - last_alert).seconds < 1800:
            return False
        
        # Filtros por categoría de item
        if prefs.get('categories'):
            if not any(cat in opportunity.name for cat in prefs['categories']):
                return False
        
        return True