import asyncio
import logging
from datetime import datetime
from os import getenv

import requests
from celery import shared_task
from dotenv import load_dotenv
from requests.models import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import (
    get_current_unix_timestamp,
    make_minute_to_milisecond_timestamp,
    transform_timestamp_datetime,
)
from app.data.common.services.stock_code_file_service import StockCodeFileReader
from app.data.polygon.constant import STOCK_COLLECT_END_TIME_MINUTE, TOTAL_STOCK_COLLECT_START_TIME_MINUTE
from app.module.asset.model import StockMinutely
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_mysql_session
from database.enum import EnvironmentType

load_dotenv()
POLYGON_API_KEY = getenv("POLYGON_API_KEY", None)
ENVIRONMENT = getenv("ENVIRONMENT", None)

logger = logging.getLogger("usa_realtime_stock")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/usa_realtime_stock.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def collect_realtime_stock_history(session: AsyncSession, code: str):
    now = get_current_unix_timestamp()
    start_time = now - make_minute_to_milisecond_timestamp(TOTAL_STOCK_COLLECT_START_TIME_MINUTE)
    end_time = now - make_minute_to_milisecond_timestamp(STOCK_COLLECT_END_TIME_MINUTE)

    url = f"https://api.polygon.io/v2/aggs/ticker/{code}/range/1/minute/{start_time}/{end_time}"
    params = {"adjusted": "true", "sort": "asc", "limit": 5000, "apiKey": POLYGON_API_KEY}

    response = requests.get(url, params=params, timeout=10)
    stocks: list[tuple[str, datetime, float]] = parse_response_data(response, code)
    db_bulk_data = []

    for code, current_datetime, price in stocks:
        current_stock_data = StockMinutely(code=code, datetime=current_datetime, price=price)
        db_bulk_data.append(current_stock_data)

    await StockMinutelyRepository.bulk_upsert(session, db_bulk_data)


def parse_response_data(response: Response, code: str) -> list[tuple[str, datetime, float]]:
    if response.status_code != 200:
        return []

    stock_data = response.json()

    result = []
    stocks = stock_data.get("results", [])

    for record in stocks:
        current_datetime = transform_timestamp_datetime(record["t"])
        result.append((code, current_datetime, record["c"]))

    return result


async def execute_async_task():
    logger.info("미국 분당 주식 데이터 수집을 시작합니다.")
    async with get_mysql_session() as session:
        stock_code_list: list[StockInfo] = StockCodeFileReader.get_usa_stock_code_list()

        for stock_info in stock_code_list:
            await collect_realtime_stock_history(session, stock_info.code)


@shared_task
async def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
