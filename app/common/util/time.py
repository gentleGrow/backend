import calendar
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def make_minute_to_milisecond_timestamp(minute: int) -> int:
    return minute * 60 * 1000


def get_current_unix_timestamp() -> int:
    return int(time.time() * 1000)


def get_date_past_day(days: int):
    seoul_tz = ZoneInfo("Asia/Seoul")
    now_in_seoul = datetime.now(seoul_tz)
    return now_in_seoul.date() - timedelta(days=days)


def check_weekend() -> bool:
    today = datetime.today().weekday()
    return today >= 5

def check_date_weekend(current_date:date) -> bool:
    return current_date.weekday() >= 5


def get_now_date() -> date:
    seoul_tz = ZoneInfo("Asia/Seoul")
    now_in_seoul = datetime.now(seoul_tz)
    return now_in_seoul.date()


def transform_timestamp_datetime(timestamp: int) -> datetime:
    seoul_tz = ZoneInfo("Asia/Seoul")

    if timestamp > 10**10:
        timestamp //= 1000

    utc_datetime = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC"))
    return utc_datetime.astimezone(seoul_tz)


def get_now_datetime() -> datetime:
    seoul_tz = ZoneInfo("Asia/Seoul")
    return datetime.now(seoul_tz).replace(second=0, microsecond=0)


def start_timestamp(year: int, month: int) -> int:
    date = datetime(year, month, 1, 0, 0)
    return int(time.mktime(date.timetuple()))


def end_timestamp(year: int, month: int) -> int:
    last_day = calendar.monthrange(year, month)[1]
    date = datetime(year, month, last_day, 23, 59)
    return int(time.mktime(date.timetuple()))
