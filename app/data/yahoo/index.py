import asyncio
import logging
import yfinance

from celery import shared_task
from database.dependency import get_mysql_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.common.enum import MarketIndexEnum
from app.data.yahoo.source.constant import MARKET_INDEX_TIME_INTERVALS
from app.data.yahoo.source.service import get_last_week_period_bounds
from app.module.asset.model import MarketIndexDaily, MarketIndexMonthly, MarketIndexWeekly
from app.module.asset.repository.market_index_daily_repository import MarketIndexDailyRepository
from app.module.asset.repository.market_index_monthly_repository import MarketIndexMonthlyRepository
from app.module.asset.repository.market_index_weekly_repository import MarketIndexWeeklyRepository


logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",  
    handlers=[
        logging.FileHandler("index.log"), 
        logging.StreamHandler(),  
    ],
)


async def fetch_and_save_market_index_data(
    session: AsyncSession,
    index_symbol: str,
    start_period: str,
    end_period: str,
    interval: str,
    model: MarketIndexDaily | MarketIndexWeekly | MarketIndexMonthly,
    repository: MarketIndexDailyRepository | MarketIndexWeeklyRepository | MarketIndexMonthlyRepository,
):
    index_data = yfinance.download(index_symbol, start=start_period, end=end_period, interval=interval, progress=False)

    if index_data.empty:
        return

    market_index_records = []

    for index, row in index_data.iterrows():
        market_index_record = model(
            name=index_symbol.value.lstrip("^"),
            date=index.date(),
            open_price=row["Open"],
            close_price=row["Close"],
            high_price=row["High"],
            low_price=row["Low"],
            volume=row["Volume"],
        )
        market_index_records.append(market_index_record)

    if market_index_records:
        await repository.bulk_upsert(session, market_index_records)


async def fetch_and_save_all_intervals(session: AsyncSession, index_symbol: str, start_period: str, end_period: str):
    for time_interval, model, repository in MARKET_INDEX_TIME_INTERVALS:
        # [객체 안 객체 인식 안됨]
        await fetch_and_save_market_index_data(
            session, index_symbol, start_period, end_period, time_interval.value, model, repository  # type: ignore
        )


async def execute_async_task():
    logging.info('일별 시장 지수 수집을 시작합니다.')
    start_period, end_period = get_last_week_period_bounds()

    async with get_mysql_session() as session:
        for index_symbol in MarketIndexEnum:
            await fetch_and_save_all_intervals(session, index_symbol, start_period, end_period)

    logging.info('일별 시장 지수 수집을 마칩니다.')


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
