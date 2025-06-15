# backend/services/cache_service.py
import redis
import json
from typing import Optional, Any
from datetime import timedelta

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[Any]:
        data = self.redis_client.get(key)
        return json.loads(data) if data else None
    
    def set(self, key: str, value: Any, expire: int = 300):
        self.redis_client.setex(
            key,
            timedelta(seconds=expire),
            json.dumps(value)
        )