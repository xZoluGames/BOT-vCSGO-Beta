# backend/core/rate_limiter.py
from functools import wraps
import time

class RateLimiter:
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.clock = {}
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            key = f"{func.__name__}"
            
            if key in self.clock:
                elapsed = now - self.clock[key]['start']
                if elapsed < self.period:
                    if self.clock[key]['calls'] >= self.calls:
                        sleep_time = self.period - elapsed
                        time.sleep(sleep_time)
                        self.clock[key] = {'start': time.time(), 'calls': 1}
                    else:
                        self.clock[key]['calls'] += 1
                else:
                    self.clock[key] = {'start': now, 'calls': 1}
            else:
                self.clock[key] = {'start': now, 'calls': 1}
            
            return func(*args, **kwargs)
        return wrapper

# Uso
@RateLimiter(calls=10, period=60)  # 10 llamadas por minuto
def fetch_api_data():
    pass