from os import getenv

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

import app.data.custom.cache_past_date  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.custom.validate_data  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.naver.current_index.collector  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.naver.current_korea_stock.collector  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.current_exchange_rate  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.current_usa_stock  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.dividend  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.index  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.stock  # noqa: F401 > task 위치를 찾는데 필요합니다.
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

if ENVIRONMENT == EnvironmentType.LOCAL.value or ENVIRONMENT == EnvironmentType.TEST.value:
    REDIS_HOST = getenv("LOCAL_REDIS_HOST", None)
elif ENVIRONMENT == EnvironmentType.DEV.value:
    REDIS_HOST = getenv("DEV_REDIS_HOST", None)
elif ENVIRONMENT == EnvironmentType.PROD.value:
    REDIS_HOST = getenv("PROD_REDIS_HOST", None)

REDIS_PORT = getenv("REDIS_PORT", None)

celery_task = Celery(
    "celery_schedule", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}", backend=f"redis://{REDIS_HOST}:{REDIS_PORT}"
)

celery_task.conf.update(
    {
        "worker_hijack_root_logger": False,
        "broker_connection_retry_on_startup": True,
        "beat_schedule_filename": "/home/ubuntu/celerybeat-schedule.db",
        "timezone": "Asia/Seoul",
        "enable_utc": False,
    }
)

if ENVIRONMENT == EnvironmentType.PROD.value:
    celery_task.conf.beat_schedule = {
        "cache_past_date": {
            "task": "app.data.custom.cache_past_date.main",
            "schedule": crontab(hour=8, minute=0),
        },
        "dividend": {
            "task": "app.data.yahoo.dividend.main",
            "schedule": crontab(hour=1, minute=0),
        },
        "index": {
            "task": "app.data.yahoo.index.main",
            "schedule": crontab(hour=1, minute=30),
        },
        "stock": {
            "task": "app.data.yahoo.stock.main",
            "schedule": crontab(hour=[8, 18], minute=0),
        },
        "validate_data": {
            "task": "app.data.custom.validate_data.main",
            "schedule": crontab(hour=23, minute=0, day_of_week="1-6"),
        },
        "current_exchange_rate": {
            "task": "app.data.yahoo.current_exchange_rate.main",
            "schedule": crontab(minute=10),
        },
        "current_usa_stock": {
            "task": "app.data.yahoo.current_usa_stock.main",
            "schedule": crontab(minute=15),
        },
        "current_korea_stock": {
            "task": "app.data.naver.current_korea_stock.collector.main",
            "schedule": crontab(minute=20),
        },
        "current_index": {
            "task": "app.data.naver.current_index.collector.main",
            "schedule": crontab(minute=25),
        },
    }
elif ENVIRONMENT == EnvironmentType.DEV.value:
    celery_task.conf.beat_schedule = {
        "cache_past_date": {
            "task": "app.data.custom.cache_past_date.main",
            "schedule": crontab(hour=8, minute=0),
        },
        "dividend": {
            "task": "app.data.yahoo.dividend.main",
            "schedule": crontab(hour=2, minute=30),
        },
        "index": {
            "task": "app.data.yahoo.index.main",
            "schedule": crontab(hour=3, minute=0),
        },
        "stock": {
            "task": "app.data.yahoo.stock.main",
            "schedule": crontab(hour=[9, 17], minute=0),
        },
        "current_exchange_rate": {
            "task": "app.data.yahoo.current_exchange_rate.main",
            "schedule": crontab(minute=30),
        },
        "current_usa_stock": {
            "task": "app.data.yahoo.current_usa_stock.main",
            "schedule": crontab(minute=35),
        },
        "current_korea_stock": {
            "task": "app.data.naver.current_korea_stock.collector.main",
            "schedule": crontab(minute=40),
        },
        "current_index": {
            "task": "app.data.naver.current_index.collector.main",
            "schedule": crontab(minute=45),
        },
    }
