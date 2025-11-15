from celery import Celery
from .beat_schedule import beat_schedule
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("trading_bot", broker=REDIS_URL, backend=REDIS_URL)
app.autodiscover_tasks(["trading_bot.tasks"])
app.conf.beat_schedule = beat_schedule
app.conf.timezone = "UTC"
