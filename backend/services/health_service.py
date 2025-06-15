# backend/services/health_service.py
class HealthMonitor:
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'scrapers': self.check_scrapers,
            'disk_space': self.check_disk_space,
            'memory': self.check_memory
        }
    
    async def run_health_check(self):
        results = {}
        for name, check in self.checks.items():
            try:
                results[name] = await check()
            except Exception as e:
                results[name] = {'status': 'error', 'message': str(e)}
        
        return results