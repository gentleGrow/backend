import asyncio
import logging
import yfinance

from celery import shared_task
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.common.service import StockCodeFileReader
from app.data.yahoo.source.constant import TIME_INTERVAL_MODEL_REPO_MAP, TIME_INTERVAL_REPOSITORY_MAP
from app.data.yahoo.source.schema import StockDataFrame
from app.data.yahoo.source.service import format_stock_code, get_last_week_period_bounds
from app.module.asset.enum import Country, TimeInterval
from app.module.asset.schema import StockInfo
from database.dependency import get_mysql_session


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/backend/stock.log"),
        logging.StreamHandler(),
    ],
)


async def process_stock_data(session: AsyncSession, stock_list: list[StockInfo], start_period: int, end_period: int):
    for stock_info in stock_list:
        for interval in TimeInterval:
            stock_model = TIME_INTERVAL_MODEL_REPO_MAP[interval]
            interval_repository = TIME_INTERVAL_REPOSITORY_MAP[interval]

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
                df = stock.history(start=start_period, end=end_period, interval=interval.value)
                df.reset_index(inplace=True)
            except Exception as e:
                logging.error(e)
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
                except Exception as e:
                    logging.error(e)
                    continue

                stock_row = stock_model(
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

            try:
                await interval_repository.bulk_upsert(session, stock_rows)
            except IntegrityError as e:
                logging.error(e)
                await session.rollback()
                continue

    logging.info("일별 주식 수집을 마칩니다")


async def execute_async_task():
    logging.info("일별 주식 수집을 시작합니다.")
    start_period, end_period = get_last_week_period_bounds()
    stock_list: list[StockInfo] = StockCodeFileReader.get_usa_korea_stock_code_list()

    async with get_mysql_session() as session:
        await process_stock_data(session, stock_list, start_period, end_period)


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
