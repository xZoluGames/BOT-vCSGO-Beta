# backend/core/retry_manager.py
from tenacity import retry, stop_after_attempt, wait_exponential

class RetryManager:
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def safe_request(func, *args, **kwargs):
        return func(*args, **kwargs)