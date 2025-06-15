# backend/tasks.py
from celery import Celery
from backend.scrapers import *
from run_scrapers import SCRAPERS

app = Celery('bot-csgo', broker='redis://localhost:6379')

@app.task
def run_scraper_task(scraper_name: str):
    """Ejecuta un scraper de forma asíncrona"""
    scraper_class = SCRAPERS.get(scraper_name)
    if scraper_class:
        scraper = scraper_class()
        return scraper.run_once()