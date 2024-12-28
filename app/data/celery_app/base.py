from os import getenv

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

import app.data.custom.remove_realtime_data  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.custom.validate_data  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.polygon.usa_realtime_stock  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.dividend  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.index  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.realtime_stock.realtime_stock_app  # noqa: F401 > task 위치를 찾는데 필요합니다.
import app.data.yahoo.stock  # noqa: F401 > task 위치를 찾는데 필요합니다.
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)
if ENVIRONMENT == EnvironmentType.DEV:
    REDIS_HOST = getenv("LOCAL_REDIS_HOST", None)
else:
    REDIS_HOST = getenv("REDIS_HOST", None)

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


celery_task.conf.beat_schedule = {
    "dividend": {
        "task": "app.data.yahoo.dividend.main",
        "schedule": crontab(hour=1, minute=0),
    },
    "index": {
        "task": "app.data.yahoo.index.main",
        "schedule": crontab(minute=0),
    },
    "stock": {
        "task": "app.data.yahoo.stock.main",
        "schedule": crontab(minute=0),
    },
    "usa_realtime_stock": {
        "task": "app.data.polygon.usa_realtime_stock.main",
        "schedule": crontab(minute=0),
    },
    "remove_minutely": {
        "task": "app.data.custom.remove_realtime_data.main",
        "schedule": crontab(hour=4, minute=0),
    },
    "validate_data": {
        "task": "app.data.custom.validate_data.main",
        "schedule": crontab(hour=23, minute=0, day_of_week="1-6"),
    },
}
