import asyncio
import logging
from os import getenv

import yfinance
from celery import shared_task
from dotenv import load_dotenv
from redis.asyncio import Redis

from app.data.common.constant import STOCK_CACHE_SECOND
from app.module.asset.constant import CURRENCY_PAIRS
from app.module.asset.redis_repository import RedisExchangeRateRepository
from database.dependency import get_redis_pool
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

logger = logging.getLogger("current_exchange_rate")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_exchange_rate.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def process_exchange_rate_data(redis_client: Redis):
    redis_bulk_data = []
    for source_currency, target_currency in CURRENCY_PAIRS:
        url = f"{source_currency}{target_currency}=X"
        try:
            ticker = yfinance.Ticker(url)
            current_price = ticker.info.get("regularMarketPrice") or ticker.info.get("regularMarketPreviousClose")
        except Exception as e:
            logger.error(e)
            continue

        if not current_price:
            continue
        cache_key = source_currency + "_" + target_currency
        redis_bulk_data.append((cache_key, current_price))

    
    if redis_bulk_data:
        await RedisExchangeRateRepository.bulk_save(redis_client, redis_bulk_data, expire_time=STOCK_CACHE_SECOND)


async def execute_async_task():
    logger.info("현재 환율을 수집합니다.")
    redis_client = get_redis_pool()
    await process_exchange_rate_data(redis_client)


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
