import asyncio
import logging
from os import getenv
from celery import shared_task
from dotenv import load_dotenv
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.module.asset.model import MarketIndexMinutely
from app.data.common.constant import STOCK_CACHE_SECOND
from app.data.naver.current_index.current_index_korea import IndexKoreaCollector
from app.data.naver.current_index.current_index_world import IndexWorldCollector
from app.module.asset.redis_repository import RedisRealTimeMarketIndexRepository
from app.module.asset.repository.market_index_minutely_repository import MarketIndexMinutelyRepository
from database.dependency import get_mysql_session, get_redis_pool
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

logger = logging.getLogger("current_index")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_index.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def process_index_data(session: AsyncSession, redis_client: Redis):
    db_bulk_data: list[MarketIndexMinutely] = []
    redis_bulk_data: list[tuple[str, str]] = []

    world_index_collector = IndexWorldCollector()
    korea_index_collector = IndexKoreaCollector()

    redis_current_world_index, db_current_world_index = await world_index_collector.get_current_index()
    if redis_current_world_index and db_current_world_index:
        redis_bulk_data.extend(redis_current_world_index)
        db_bulk_data.extend(db_current_world_index)

    redis_current_korea_index, db_current_korea_index = await korea_index_collector.get_current_index()
    if redis_current_korea_index and db_current_korea_index:
        redis_bulk_data.extend(redis_current_korea_index)
        db_bulk_data.extend(db_current_korea_index)

    if redis_bulk_data and db_bulk_data:
        await MarketIndexMinutelyRepository.bulk_upsert(session, db_bulk_data)
        await RedisRealTimeMarketIndexRepository.bulk_save(
            redis_client, redis_bulk_data, expire_time=STOCK_CACHE_SECOND
        )


async def execute_async_task():
    logger.info("현재 시장 지수를 수집합니다.")
    redis_client = get_redis_pool()
    async with get_mysql_session() as session:
        await process_index_data(session, redis_client)


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())

