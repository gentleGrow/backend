import asyncio
import logging
from os import getenv

import yfinance
from celery import shared_task
from dotenv import load_dotenv
from redis.asyncio import Redis
from app.data.common.enum import MarketIndexEnum
from app.data.common.constant import STOCK_CACHE_SECOND
from app.module.asset.redis_repository import RedisRealTimeMarketIndexRepository
from database.dependency import get_redis_pool
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)


logger = logging.getLogger("current_index")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_index.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
    
    
async def process_index_data(redis_client: Redis):
    redis_bulk_data = []
    for index_symbol in MarketIndexEnum:
        try:
            index = yfinance.Ticker(index_symbol.value)
            current_price = index.info.get("regularMarketPrice") or index.info.get("regularMarketPreviousClose")
        except Exception as e:
            logger.error(e)
        
        if not current_price:
            continue
        
        redis_bulk_data.append((index_symbol.value.lstrip("^"), current_price))
            
    if redis_bulk_data:
        await RedisRealTimeMarketIndexRepository.bulk_save(redis_client, redis_bulk_data, expire_time=STOCK_CACHE_SECOND)

async def execute_async_task():
    logger.info("현재 시장 지수를 수집합니다.")
    redis_client = get_redis_pool()
    await process_index_data(redis_client)
    

@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())

