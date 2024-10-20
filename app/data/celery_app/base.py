from os import getenv

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)
if ENVIRONMENT == EnvironmentType.DEV:
    REDIS_HOST = getenv("LOCAL_REDIS_HOST", None)
else:
    REDIS_HOST = getenv("REDIS_HOST", None)

REDIS_PORT = getenv("REDIS_PORT", None)

celery_task = Celery(
    "celery_schedule",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}",
    include=[
        "app.data.tip.run",
        "app.data.yahoo.dividend",
        "app.data.yahoo.exchange_rate",
        "app.data.yahoo.index",
        "app.data.yahoo.stock",
        "app.data.investing.rich_portfolio",
        "app.data.naver.realtime_index_korea",
        "app.data.naver.realtime_index_world",
        "app.data.yahoo.realtime_stock.realtime_stock_run",
    ],
)

celery_task.conf.beat_schedule = {
    "tip": {
        "task": "app.data.tip.run.main",
        "schedule": crontab(hour=3, minute=0),
    },
    "dividend": {
        "task": "app.data.yahoo.dividend.main",
        "schedule": crontab(hour=3, minute=0),
    },
    "index": {
        "task": "app.data.yahoo.index.main",
        "schedule": crontab(hour=3, minute=0),
    },
    "stock": {
        "task": "app.data.yahoo.stock.main",
        "schedule": crontab(hour=3, minute=0),
    },
    "rich_portfolio": {
        "task": "app.data.investing.rich_portfolio.main",
        "schedule": crontab(hour=3, minute=0),
    },
    "exchange_rate": {
        "task": "app.data.yahoo.exchange_rate.main",
        "schedule": crontab(minute=0, hour=0),
        "options": {"run_once": True},
    },
    "realtime_index_korea_everyday": {
        "task": "app.data.naver.realtime_index_korea.main",
        "schedule": crontab(minute=0, hour=0),
        "options": {"run_once": True},
    },
    "realtime_index_world_everyday": {
        "task": "app.data.naver.realtime_index_world.main",
        "schedule": crontab(minute=0, hour=0),
        "options": {"run_once": True},
    },
    "realtime_stock_run_everyday": {
        "task": "app.data.yahoo.realtime_stock_run.main",
        "schedule": crontab(minute=0, hour=0),
        "options": {"run_once": True},
    },
}
