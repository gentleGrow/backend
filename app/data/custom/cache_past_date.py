import asyncio
import logging
from os import getenv

from celery import shared_task
from dotenv import load_dotenv
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import get_past_weekday_date
from app.module.asset.constant import (
    PAST_MONTH_DAY,
    REDIS_STOCK_EXPIRE_SECOND,
    REDIS_STOCK_PAST_DATE_CHECK_CODES,
    REDIS_STOCK_PAST_DATE_KEY,
)
from app.module.asset.redis_repository import RedisCurrentPastDateRepository
from app.module.asset.repository.stock_daily_repository import StockDailyRepository
from database.dependency import get_mysql_session, get_redis_pool
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

logger = logging.getLogger("cache_past_date")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/cache_past_date.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def cache_past_date(session: AsyncSession, redis_client: Redis):
    current_past_day = PAST_MONTH_DAY
    past_date = get_past_weekday_date(PAST_MONTH_DAY)

    while PAST_MONTH_DAY * 2 > current_past_day:
        stock_code_date_pairs = [(stock_code, past_date) for stock_code in REDIS_STOCK_PAST_DATE_CHECK_CODES]
        stock_dailes = await StockDailyRepository.get_stock_dailies_by_code_and_date(session, stock_code_date_pairs)

        if len(stock_dailes) == len(REDIS_STOCK_PAST_DATE_CHECK_CODES):
            await RedisCurrentPastDateRepository.set(
                redis_client, REDIS_STOCK_PAST_DATE_KEY, str(past_date), REDIS_STOCK_EXPIRE_SECOND
            )
            return

        current_past_day = current_past_day + 1
        past_date = get_past_weekday_date(current_past_day)


async def execute_async_task():
    logger.info("과거 past_date를 캐싱을 시도합니다.")
    redis_client = get_redis_pool()
    async with get_mysql_session() as session:
        await cache_past_date(session, redis_client)
        logger.info("과거 past_date를 캐싱하였습니다.")


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
