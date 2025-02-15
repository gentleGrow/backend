import asyncio

import yfinance
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.yahoo.source.constant import MARKET_TIME_INTERVAL, STOCK_HISTORY_TIMERANGE_YEAR
from app.data.yahoo.source.service import get_period_bounds
from app.module.asset.enum import MarketIndex
from app.module.asset.model import MarketIndexDaily
from app.module.asset.repository.market_index_daily_repository import MarketIndexDailyRepository
from database.dependency import get_mysql_session


async def fetch_and_save_market_index_data(
    session: AsyncSession,
    index_symbol: str,
    start_period: str,
    end_period: str,
):
    index_data = yfinance.download(
        f"^{index_symbol}", start=start_period, end=end_period, interval=MARKET_TIME_INTERVAL, progress=False
    )

    if index_data.empty:
        print(f"{index_symbol} 데이터를 찾지 못 했습니다.")
        return

    market_index_records = []

    for index, row in index_data.iterrows():
        market_index_record = MarketIndexDaily(
            name=index_symbol,
            date=index.date(),
            open_price=row["Open"].item(),
            close_price=row["Close"].item(),
            high_price=row["High"].item(),
            low_price=row["Low"].item(),
            volume=row["Volume"].item(),
        )

        market_index_records.append(market_index_record)

    if market_index_records:
        await MarketIndexDailyRepository.bulk_upsert(session, market_index_records)
        print(f"{index_symbol}의 {len(market_index_records)} 데이터를 저장 하였습니다.")


async def fetch_and_save_all_intervals(session: AsyncSession, index_symbol: str, start_period: str, end_period: str):
    await fetch_and_save_market_index_data(
        session,
        index_symbol,
        start_period,
        end_period,
    )


async def main():
    start_period, end_period = get_period_bounds(STOCK_HISTORY_TIMERANGE_YEAR)

    async with get_mysql_session() as session:
        for index_symbol in MarketIndex:
            await fetch_and_save_all_intervals(session, index_symbol, start_period, end_period)


if __name__ == "__main__":
    asyncio.run(main())
