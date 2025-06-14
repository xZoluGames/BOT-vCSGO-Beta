# backend/database/models.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from pathlib import Path

Base = declarative_base()

class Item(Base):
    """Modelo para items de CS:GO"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    steam_price = Column(Float, nullable=True)
    profitability = Column(Float, nullable=True)
    url = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_available = Column(Boolean, default=True)
    
    # Índice único para evitar duplicados
    __table_args__ = (
        UniqueConstraint('name', 'platform', name='_name_platform_uc'),
        Index('idx_profitability', 'profitability'),
        Index('idx_last_updated', 'last_updated'),
    )
    
    def __repr__(self):
        return f"<Item(name='{self.name}', platform='{self.platform}', price={self.price})>"


class PriceHistory(Base):
    """Modelo para histórico de precios"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Índices para consultas rápidas
    __table_args__ = (
        Index('idx_item_platform_time', 'item_name', 'platform', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<PriceHistory(item='{self.item_name}', platform='{self.platform}', price={self.price}, time={self.timestamp})>"


class ProfitableOpportunity(Base):
    """Modelo para oportunidades rentables"""
    __tablename__ = "profitable_opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False, index=True)
    buy_platform = Column(String, nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_url = Column(String)
    steam_price = Column(Float, nullable=False)
    net_steam_price = Column(Float, nullable=False)
    profitability = Column(Float, nullable=False, index=True)
    profit_amount = Column(Float, nullable=False)
    found_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Opportunity(item='{self.item_name}', profit={self.profitability*100:.2f}%)>"


class ScraperStatus(Base):
    """Modelo para estado de scrapers"""
    __tablename__ = "scraper_status"
    
    id = Column(Integer, primary_key=True, index=True)
    scraper_name = Column(String, unique=True, nullable=False)
    status = Column(String, default='idle')  # idle, running, error
    last_run = Column(DateTime)
    last_success = Column(DateTime)
    items_found = Column(Integer, default=0)
    error_message = Column(String)
    run_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<ScraperStatus(name='{self.scraper_name}', status='{self.status}')>"


# Clase para manejar la base de datos
class DatabaseManager:
    def __init__(self, db_url=None):
        if db_url is None:
            # Por defecto usar SQLite
            db_path = Path("data/csgo_arbitrage.db")
            db_path.parent.mkdir(exist_ok=True)
            db_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Crear tablas si no existen
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Obtiene una nueva sesión de base de datos"""
        return self.SessionLocal()
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        self.engine.dispose()


# Singleton para el manager de base de datos
_db_manager = None

def get_database_manager():
    """Obtiene la instancia singleton del DatabaseManager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager