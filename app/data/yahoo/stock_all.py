import asyncio

import yfinance
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.common.services.stock_code_file_service import StockCodeFileReader
from app.data.yahoo.source.constant import STOCK_HISTORY_TIMERANGE_YEAR, STOCK_TIME_INTERVAL
from app.data.yahoo.source.schema import StockDataFrame
from app.data.yahoo.source.service import format_stock_code, get_period_bounds
from app.module.asset.enum import Country
from app.module.asset.model import StockDaily
from app.module.asset.repository.stock_daily_repository import StockDailyRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_mysql_session


async def process_stock_data(session: AsyncSession, stock_list: list[StockInfo], start_period: int, end_period: int):
    for stock_info in stock_list:
        try:
            stock_code = format_stock_code(
                stock_info.code,
                Country[stock_info.country.upper().replace(" ", "_")],
                stock_info.market_index.upper(),
            )
        except KeyError:
            continue

        try:
            stock = yfinance.Ticker(stock_code)
            df = stock.history(start=start_period, end=end_period, interval=STOCK_TIME_INTERVAL)
            df.reset_index(inplace=True)
        except Exception:
            continue

        stock_rows = []

        for _, row in df.iterrows():
            try:
                stock_dataframe = StockDataFrame(
                    date=row["Date"].strftime("%Y-%m-%d"),
                    open=row["Open"],
                    high=row["High"],
                    low=row["Low"],
                    close=row["Close"],
                    adj_close=row["Close"],
                    volume=row["Volume"],
                )
            except Exception:
                continue

            stock_row = StockDaily(
                code=stock_info.code,
                date=stock_dataframe.date,
                opening_price=stock_dataframe.open,
                highest_price=stock_dataframe.high,
                lowest_price=stock_dataframe.low,
                close_price=stock_dataframe.close,
                adj_close_price=stock_dataframe.adj_close,
                trade_volume=stock_dataframe.volume,
            )

            stock_rows.append(stock_row)

        await StockDailyRepository.bulk_upsert(session, stock_rows)


async def main():
    start_period, end_period = get_period_bounds(STOCK_HISTORY_TIMERANGE_YEAR)
    stock_list: list[StockInfo] = StockCodeFileReader.get_all_stock_code_list()

    async with get_mysql_session() as session:
        await process_stock_data(session, stock_list, start_period, end_period)


if __name__ == "__main__":
    asyncio.run(main())
