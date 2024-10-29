import asyncio
from datetime import timedelta

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import get_now_datetime
from app.data.yahoo.source.constant import REMOVE_TIME_DAY
from app.module.asset.repository.market_index_minutely_repository import MarketIndexMinutelyRepository
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from database.dependency import get_mysql_session


async def remove_realtime_data(session: AsyncSession):
    remove_time = get_now_datetime() - timedelta(days=REMOVE_TIME_DAY)
    await StockMinutelyRepository.remove_by_datetime(session, remove_time)
    await MarketIndexMinutelyRepository.remove_by_datetime(session, remove_time)


async def execute_async_task():
    async with get_mysql_session() as session:
        await remove_realtime_data(session)


@shared_task
def main():
    asyncio.run(execute_async_task())
