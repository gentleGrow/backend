import asyncio
import logging
from os import getenv
from celery import shared_task
from dotenv import load_dotenv
from redis.asyncio import Redis

from app.data.common.constant import STOCK_CACHE_SECOND
from app.data.naver.current_index.current_index_korea import IndexKoreaCollector
from app.data.naver.current_index.current_index_world import IndexWorldCollector
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
    world_index_collector = IndexWorldCollector()
    korea_index_collector = IndexKoreaCollector()

    current_world_index = await world_index_collector.get_current_index()
    redis_bulk_data.extend(current_world_index)

    current_korea_index: list = await korea_index_collector.get_current_index()
    redis_bulk_data.extend(current_korea_index)

    if redis_bulk_data:
        await RedisRealTimeMarketIndexRepository.bulk_save(
            redis_client, redis_bulk_data, expire_time=STOCK_CACHE_SECOND
        )


async def execute_async_task():
    logger.info("현재 시장 지수를 수집합니다.")
    redis_client = get_redis_pool()
    await process_index_data(redis_client)


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
