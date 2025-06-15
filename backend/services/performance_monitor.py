# backend/services/performance_monitor.py
import time
import psutil
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


class PerformanceMonitor:
    """Monitor de rendimiento para scrapers"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
        self.log_file = Path("logs/performance.json")
        self.log_file.parent.mkdir(exist_ok=True)
    
    def start_monitoring(self, scraper_name: str):
        """Inicia el monitoreo de un scraper"""
        self.start_times[scraper_name] = {
            'start_time': time.time(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
        }
    
    def end_monitoring(self, scraper_name: str, items_fetched: int = 0):
        """Finaliza el monitoreo y guarda métricas"""
        if scraper_name not in self.start_times:
            return
        
        start_data = self.start_times[scraper_name]
        duration = time.time() - start_data['start_time']
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'scraper': scraper_name,
            'duration_seconds': round(duration, 2),
            'items_fetched': items_fetched,
            'items_per_second': round(items_fetched / duration, 2) if duration > 0 else 0,
            'cpu_usage': psutil.cpu_percent() - start_data['cpu_percent'],
            'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
            'memory_delta_mb': (psutil.Process().memory_info().rss / 1024 / 1024) - start_data['memory_mb']
        }
        
        self.metrics[scraper_name].append(metrics)
        self._save_metrics()
        
        del self.start_times[scraper_name]
        
        return metrics
    
    def _save_metrics(self):
        """Guarda métricas en archivo"""
        try:
            # Convertir defaultdict a dict normal para JSON
            data = dict(self.metrics)
            
            # Mantener solo las últimas 100 métricas por scraper
            for scraper in data:
                if len(data[scraper]) > 100:
                    data[scraper] = data[scraper][-100:]
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error guardando métricas: {e}")
    
    def get_average_metrics(self, scraper_name: str) -> Dict:
        """Obtiene métricas promedio de un scraper"""
        if scraper_name not in self.metrics:
            return {}
        
        metrics_list = self.metrics[scraper_name]
        if not metrics_list:
            return {}
        
        return {
            'avg_duration': sum(m['duration_seconds'] for m in metrics_list) / len(metrics_list),
            'avg_items_per_second': sum(m['items_per_second'] for m in metrics_list) / len(metrics_list),
            'avg_memory_mb': sum(m['memory_mb'] for m in metrics_list) / len(metrics_list),
            'total_runs': len(metrics_list)
        }
    
    def get_performance_report(self) -> Dict:
        """Genera un reporte de rendimiento general"""
        report = {}
        
        for scraper_name in self.metrics:
            avg_metrics = self.get_average_metrics(scraper_name)
            if avg_metrics:
                report[scraper_name] = avg_metrics
        
        return report


# Singleton
_monitor = None

def get_performance_monitor():
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor
