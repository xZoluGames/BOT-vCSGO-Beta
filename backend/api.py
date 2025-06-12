# backend/api.py

from fastapi import FastAPI, HTTPException, WebSocket, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import json
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Configuración de base de datos
DATABASE_URL = "sqlite:///./csgo_arbitrage.db"  # Cambiar a PostgreSQL en producción
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelos de base de datos
class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    platform = Column(String, index=True)
    price = Column(Float)
    steam_price = Column(Float, nullable=True)
    profitability = Column(Float, nullable=True)
    url = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_profitable = Column(Boolean, default=False)

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, index=True)
    platform = Column(String)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Modelos Pydantic
class ItemResponse(BaseModel):
    id: int
    name: str
    platform: str
    price: float
    steam_price: Optional[float]
    profitability: Optional[float]
    url: str
    last_updated: datetime
    is_profitable: bool
    
    class Config:
        from_attributes = True

class ProfitableOpportunity(BaseModel):
    item_name: str
    buy_platform: str
    buy_price: float
    buy_url: str
    steam_price: float
    net_steam_price: float
    profitability_percentage: float
    potential_profit: float

class ScraperStatus(BaseModel):
    name: str
    status: str
    last_run: Optional[datetime]
    items_count: int
    error: Optional[str]

class FilterParams(BaseModel):
    min_profitability: Optional[float] = 0
    max_price: Optional[float] = None
    platforms: Optional[List[str]] = None
    search_term: Optional[str] = None

# Manager de WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Servicios
class ArbitrageService:
    @staticmethod
    def calculate_profitability(buy_price: float, sell_price: float) -> tuple[float, float]:
        """Calcula la rentabilidad considerando las comisiones de Steam"""
        # Implementar tu lógica de subtract_fee aquí
        steam_fee = sell_price * 0.13  # 13% de comisión de Steam aproximadamente
        net_sell_price = sell_price - steam_fee
        
        if buy_price == 0:
            return 0, net_sell_price
            
        profit = net_sell_price - buy_price
        profitability_percentage = (profit / buy_price) * 100
        
        return profitability_percentage, net_sell_price
    
    @staticmethod
    def find_opportunities(db: Session, filters: FilterParams) -> List[ProfitableOpportunity]:
        """Busca oportunidades de arbitraje rentables"""
        opportunities = []
        
        # Obtener todos los items de Steam
        steam_items = db.query(Item).filter(Item.platform == "Steam").all()
        steam_prices = {item.name: item.price for item in steam_items}
        
        # Buscar en otras plataformas
        query = db.query(Item).filter(Item.platform != "Steam")
        
        if filters.platforms:
            query = query.filter(Item.platform.in_(filters.platforms))
        if filters.max_price:
            query = query.filter(Item.price <= filters.max_price)
        if filters.search_term:
            query = query.filter(Item.name.contains(filters.search_term))
            
        items = query.all()
        
        for item in items:
            if item.name in steam_prices:
                steam_price = steam_prices[item.name]
                profitability, net_price = ArbitrageService.calculate_profitability(
                    item.price, steam_price
                )
                
                if profitability >= filters.min_profitability:
                    opportunities.append(ProfitableOpportunity(
                        item_name=item.name,
                        buy_platform=item.platform,
                        buy_price=item.price,
                        buy_url=item.url,
                        steam_price=steam_price,
                        net_steam_price=net_price,
                        profitability_percentage=profitability,
                        potential_profit=net_price - item.price
                    ))
                    
        # Ordenar por rentabilidad
        opportunities.sort(key=lambda x: x.profitability_percentage, reverse=True)
        return opportunities

# Tareas en segundo plano
scrapers_status = {}

async def run_scrapers_background():
    """Ejecuta los scrapers en segundo plano"""
    while True:
        try:
            # Aquí ejecutarías tus scrapers
            # Por ahora simularemos actualizaciones
            await asyncio.sleep(60)
            
            # Enviar actualización por WebSocket
            status_update = {
                "type": "scraper_update",
                "data": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Scrapers ejecutados exitosamente"
                }
            }
            await manager.broadcast(json.dumps(status_update))
            
        except Exception as e:
            print(f"Error en scrapers: {e}")

# Configuración de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(run_scrapers_background())
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="CS:GO Arbitrage API",
    description="API para monitoreo de precios y arbitraje de items de CS:GO",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.get("/")
async def root():
    return {"message": "CS:GO Arbitrage API v2.0"}

@app.get("/api/opportunities", response_model=List[ProfitableOpportunity])
async def get_opportunities(
    min_profitability: float = 0,
    max_price: Optional[float] = None,
    platforms: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Obtiene las oportunidades de arbitraje rentables"""
    filters = FilterParams(
        min_profitability=min_profitability,
        max_price=max_price,
        platforms=platforms.split(",") if platforms else None,
        search_term=search
    )
    
    return ArbitrageService.find_opportunities(db, filters)

@app.get("/api/items", response_model=List[ItemResponse])
async def get_items(
    platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Obtiene lista de items con paginación"""
    query = db.query(Item)
    
    if platform:
        query = query.filter(Item.platform == platform)
        
    items = query.offset(offset).limit(limit).all()
    return items

@app.get("/api/item/{item_name}/history")
async def get_item_history(
    item_name: str,
    platform: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Obtiene el historial de precios de un item"""
    since = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(PriceHistory).filter(
        PriceHistory.item_name == item_name,
        PriceHistory.timestamp >= since
    )
    
    if platform:
        query = query.filter(PriceHistory.platform == platform)
        
    history = query.order_by(PriceHistory.timestamp).all()
    
    return {
        "item_name": item_name,
        "history": [
            {
                "platform": h.platform,
                "price": h.price,
                "timestamp": h.timestamp
            }
            for h in history
        ]
    }

@app.get("/api/scrapers/status", response_model=List[ScraperStatus])
async def get_scrapers_status():
    """Obtiene el estado de todos los scrapers"""
    # En producción, esto vendría de una base de datos o Redis
    return [
        ScraperStatus(
            name="Steam",
            status="running",
            last_run=datetime.utcnow(),
            items_count=15420,
            error=None
        ),
        ScraperStatus(
            name="Waxpeer",
            status="running",
            last_run=datetime.utcnow() - timedelta(minutes=5),
            items_count=8932,
            error=None
        ),
        # Agregar más scrapers...
    ]

@app.post("/api/scrapers/{scraper_name}/start")
async def start_scraper(scraper_name: str, background_tasks: BackgroundTasks):
    """Inicia un scraper específico"""
    # Aquí iniciarías el scraper correspondiente
    background_tasks.add_task(lambda: print(f"Iniciando {scraper_name}"))
    return {"message": f"Scraper {scraper_name} iniciado"}

@app.post("/api/scrapers/{scraper_name}/stop")
async def stop_scraper(scraper_name: str):
    """Detiene un scraper específico"""
    return {"message": f"Scraper {scraper_name} detenido"}

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Obtiene estadísticas generales"""
    total_items = db.query(Item).count()
    profitable_items = db.query(Item).filter(Item.is_profitable == True).count()
    platforms_count = db.query(Item.platform).distinct().count()
    
    # Mejor oportunidad actual
    opportunities = ArbitrageService.find_opportunities(db, FilterParams())
    best_opportunity = opportunities[0] if opportunities else None
    
    return {
        "total_items": total_items,
        "profitable_items": profitable_items,
        "platforms_count": platforms_count,
        "best_opportunity": best_opportunity,
        "last_update": datetime.utcnow()
    }

# WebSocket para actualizaciones en tiempo real
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Mantener la conexión abierta
            data = await websocket.receive_text()
            
            # Aquí podrías procesar comandos del cliente
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Endpoints de configuración
@app.get("/api/config")
async def get_config():
    """Obtiene la configuración actual"""
    # Cargar desde archivos de configuración
    return {
        "min_profitability_thresholds": {
            "waxpeer": 0.5,
            "csdeals": 0.5,
            "empire": 1.2,
            # etc...
        },
        "update_intervals": {
            "steam": 3600,
            "other_platforms": 60
        }
    }

@app.put("/api/config")
async def update_config(config: Dict):
    """Actualiza la configuración"""
    # Guardar en archivos de configuración
    return {"message": "Configuración actualizada"}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}