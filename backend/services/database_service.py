# backend/services/database_service.py

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from loguru import logger
import json

from backend.database.models import (
    Item, PriceHistory, ProfitableOpportunity, 
    ScraperStatus, get_database_manager
)


class DatabaseService:
    """Servicio para operaciones de base de datos"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.logger = logger.bind(service="DatabaseService")
    
    def save_scraper_data(self, platform: str, items: List[Dict]):
        """
        Guarda los datos de un scraper en la base de datos
        
        Args:
            platform: Nombre de la plataforma
            items: Lista de items con estructura {'Item': str, 'Price': float}
        """
        session = self.db_manager.get_session()
        
        try:
            # Actualizar estado del scraper
            scraper_status = session.query(ScraperStatus).filter_by(
                scraper_name=platform
            ).first()
            
            if not scraper_status:
                scraper_status = ScraperStatus(scraper_name=platform)
                session.add(scraper_status)
            
            scraper_status.status = 'running'
            scraper_status.last_run = datetime.utcnow()
            
            items_saved = 0
            
            for item_data in items:
                item_name = item_data.get('Item', '')
                price = float(item_data.get('Price', 0))
                
                if not item_name or price == 0:
                    continue
                
                # Buscar o crear el item
                item = session.query(Item).filter_by(
                    name=item_name,
                    platform=platform
                ).first()
                
                if item:
                    # Actualizar precio existente
                    if item.price != price:
                        # Guardar en histórico
                        history = PriceHistory(
                            item_name=item_name,
                            platform=platform,
                            price=price
                        )
                        session.add(history)
                    
                    item.price = price
                    item.last_updated = datetime.utcnow()
                    item.is_available = True
                else:
                    # Crear nuevo item
                    item = Item(
                        name=item_name,
                        platform=platform,
                        price=price,
                        url=item_data.get('url', '')
                    )
                    session.add(item)
                    
                    # También agregar al histórico
                    history = PriceHistory(
                        item_name=item_name,
                        platform=platform,
                        price=price
                    )
                    session.add(history)
                
                items_saved += 1
            
            # Marcar items no encontrados como no disponibles
            session.query(Item).filter(
                Item.platform == platform,
                Item.last_updated < datetime.utcnow() - timedelta(minutes=30)
            ).update({'is_available': False})
            
            # Actualizar estado del scraper
            scraper_status.status = 'idle'
            scraper_status.last_success = datetime.utcnow()
            scraper_status.items_found = items_saved
            scraper_status.run_count += 1
            scraper_status.error_message = None
            
            session.commit()
            
            self.logger.info(f"Guardados {items_saved} items de {platform}")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error guardando datos de {platform}: {e}")
            
            # Actualizar estado de error
            if scraper_status:
                scraper_status.status = 'error'
                scraper_status.error_message = str(e)
                session.commit()
            
        finally:
            session.close()
    
    def save_profitable_opportunities(self, opportunities: List[Dict]):
        """Guarda las oportunidades rentables en la base de datos"""
        session = self.db_manager.get_session()
        
        try:
            # Marcar todas las oportunidades anteriores como inactivas
            session.query(ProfitableOpportunity).update({'is_active': False})
            
            for opp in opportunities:
                opportunity = ProfitableOpportunity(
                    item_name=opp['name'],
                    buy_platform=opp['platform'],
                    buy_price=opp['buy_price'],
                    buy_url=opp['link'],
                    steam_price=opp['steam_price'],
                    net_steam_price=opp['net_steam_price'],
                    profitability=opp['rentabilidad'],
                    profit_amount=opp['net_steam_price'] - opp['buy_price']
                )
                session.add(opportunity)
            
            session.commit()
            self.logger.info(f"Guardadas {len(opportunities)} oportunidades rentables")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error guardando oportunidades: {e}")
        finally:
            session.close()
    
    def get_profitable_opportunities(self, min_profit: float = 0.05, limit: int = 100):
        """
        Obtiene las oportunidades rentables activas
        
        Args:
            min_profit: Rentabilidad mínima (0.05 = 5%)
            limit: Número máximo de resultados
        """
        session = self.db_manager.get_session()
        
        try:
            opportunities = session.query(ProfitableOpportunity).filter(
                ProfitableOpportunity.is_active == True,
                ProfitableOpportunity.profitability >= min_profit
            ).order_by(
                ProfitableOpportunity.profitability.desc()
            ).limit(limit).all()
            
            return [
                {
                    'name': opp.item_name,
                    'buy_platform': opp.buy_platform,
                    'buy_price': opp.buy_price,
                    'buy_url': opp.buy_url,
                    'steam_price': opp.steam_price,
                    'profit_percentage': opp.profitability * 100,
                    'profit_amount': opp.profit_amount,
                    'found_at': opp.found_at
                }
                for opp in opportunities
            ]
            
        finally:
            session.close()
    
    def get_price_history(self, item_name: str, platform: Optional[str] = None, days: int = 7):
        """Obtiene el histórico de precios de un item"""
        session = self.db_manager.get_session()
        
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            query = session.query(PriceHistory).filter(
                PriceHistory.item_name == item_name,
                PriceHistory.timestamp >= since
            )
            
            if platform:
                query = query.filter(PriceHistory.platform == platform)
            
            history = query.order_by(PriceHistory.timestamp).all()
            
            return [
                {
                    'platform': h.platform,
                    'price': h.price,
                    'timestamp': h.timestamp.isoformat()
                }
                for h in history
            ]
            
        finally:
            session.close()
    
    def get_price_trends(self, item_name: str, platform: str, days: int = 7):
        """Calcula las tendencias de precio de un item"""
        session = self.db_manager.get_session()
        
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Obtener precios históricos
            prices = session.query(
                PriceHistory.price,
                PriceHistory.timestamp
            ).filter(
                PriceHistory.item_name == item_name,
                PriceHistory.platform == platform,
                PriceHistory.timestamp >= since
            ).order_by(PriceHistory.timestamp).all()
            
            if len(prices) < 2:
                return None
            
            # Calcular estadísticas
            price_values = [p.price for p in prices]
            
            current_price = price_values[-1]
            min_price = min(price_values)
            max_price = max(price_values)
            avg_price = sum(price_values) / len(price_values)
            
            # Calcular tendencia (positiva/negativa)
            first_half_avg = sum(price_values[:len(price_values)//2]) / (len(price_values)//2)
            second_half_avg = sum(price_values[len(price_values)//2:]) / (len(price_values) - len(price_values)//2)
            
            trend = "up" if second_half_avg > first_half_avg else "down"
            trend_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100
            
            return {
                'current_price': current_price,
                'min_price': min_price,
                'max_price': max_price,
                'avg_price': avg_price,
                'trend': trend,
                'trend_percentage': trend_percentage,
                'price_count': len(prices)
            }
            
        finally:
            session.close()
    
    def get_scrapers_status(self):
        """Obtiene el estado de todos los scrapers"""
        session = self.db_manager.get_session()
        
        try:
            scrapers = session.query(ScraperStatus).all()
            
            return [
                {
                    'name': s.scraper_name,
                    'status': s.status,
                    'last_run': s.last_run.isoformat() if s.last_run else None,
                    'last_success': s.last_success.isoformat() if s.last_success else None,
                    'items_found': s.items_found,
                    'run_count': s.run_count,
                    'error': s.error_message
                }
                for s in scrapers
            ]
            
        finally:
            session.close()
    
    def cleanup_old_data(self, days: int = 30):
        """Limpia datos antiguos de la base de datos"""
        session = self.db_manager.get_session()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Eliminar histórico antiguo
            deleted = session.query(PriceHistory).filter(
                PriceHistory.timestamp < cutoff_date
            ).delete()
            
            # Eliminar oportunidades antiguas inactivas
            deleted_opps = session.query(ProfitableOpportunity).filter(
                ProfitableOpportunity.found_at < cutoff_date,
                ProfitableOpportunity.is_active == False
            ).delete()
            
            session.commit()
            
            self.logger.info(
                f"Limpieza completada: {deleted} registros de histórico, "
                f"{deleted_opps} oportunidades antiguas eliminadas"
            )
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error en limpieza: {e}")
        finally:
            session.close()


# Singleton para el servicio de base de datos
_db_service = None

def get_database_service():
    """Obtiene la instancia singleton del DatabaseService"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service