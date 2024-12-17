import asyncio
import logging
from datetime import timedelta
from os import getenv

from celery import shared_task
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import get_now_datetime
from app.data.yahoo.source.constant import REMOVE_TIME_DAY
from app.module.asset.repository.market_index_minutely_repository import MarketIndexMinutelyRepository
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from database.dependency import get_mysql_session
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)


logger = logging.getLogger("remove_minutely")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/remove_minutely.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def remove_realtime_data(session: AsyncSession):
    remove_time = get_now_datetime() - timedelta(days=REMOVE_TIME_DAY)
    await StockMinutelyRepository.remove_by_datetime(session, remove_time)
    await MarketIndexMinutelyRepository.remove_by_datetime(session, remove_time)


async def execute_async_task():
    logger.info("분당 데이터 삭제 시작합니다.")

    async with get_mysql_session() as session:
        await remove_realtime_data(session)


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
