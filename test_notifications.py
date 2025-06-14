#!/usr/bin/env python3
# test_notifications.py - Prueba el sistema de notificaciones

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from backend.services.notification_service import get_notification_service
import time


def test_notifications():
    """Prueba diferentes tipos de notificaciones"""
    print("\n" + "="*60)
    print("PRUEBA DEL SISTEMA DE NOTIFICACIONES")
    print("="*60)
    
    service = get_notification_service()
    
    # Prueba 1: Notificación INFO
    print("\n1. Probando notificación INFO...")
    service.send(
        title="ℹ️ SISTEMA INICIADO",
        message="El sistema de notificaciones está funcionando correctamente",
        level="INFO"
    )
    time.sleep(1)
    
    # Prueba 2: Notificación WARNING
    print("\n2. Probando notificación WARNING...")
    service.notify_scraper_error(
        scraper_name="Waxpeer",
        error="Timeout al conectar con la API"
    )
    time.sleep(1)
    
    # Prueba 3: Notificación OPPORTUNITY
    print("\n3. Probando notificación OPPORTUNITY...")
    service.notify_opportunity(
        item_name="★ Karambit | Doppler (Factory New)",
        buy_platform="Waxpeer",
        buy_price=1250.00,
        profit_percentage=15.5,
        profit_amount=193.75
    )
    time.sleep(1)
    
    # Prueba 4: Resumen
    print("\n4. Probando notificación de resumen...")
    service.notify_summary(
        opportunities_count=25,
        best_profit=18.5,
        total_scrapers=10
    )
    
    # Mostrar notificaciones recientes
    print("\n5. Notificaciones recientes guardadas:")
    recent = service.get_recent_notifications(limit=5)
    for notif in recent:
        print(f"   - [{notif['level']}] {notif['title']}")
    
    print("\n✅ Prueba completada!")
    print(f"Las notificaciones se guardaron en: logs/notifications.json")


if __name__ == "__main__":
    test_notifications()