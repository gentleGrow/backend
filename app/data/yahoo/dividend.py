import asyncio
import logging
from os import getenv

import pandas as pd
import yfinance
from celery import shared_task
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.common.services.stock_code_file_service import StockCodeFileReader
from app.data.yahoo.source.constant import BATCH_SIZE
from app.data.yahoo.source.service import format_stock_code
from app.module.asset.enum import Country
from app.module.asset.model import Dividend
from app.module.asset.repository.dividend_repository import DividendRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_mysql_session
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

logger = logging.getLogger("dividend")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD or ENVIRONMENT == EnvironmentType.DEV:
    file_handler = logging.FileHandler("/home/backend/dividend.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def insert_dividend_data(session: AsyncSession, stock_list: list[StockInfo], batch_size: int):
    for i in range(0, len(stock_list), batch_size):
        stock_list_batch = stock_list[i : i + batch_size]

        for stock in stock_list_batch:
            dividend_list = []
            try:
                stock_code = format_stock_code(
                    stock.code.strip(), Country[stock.country.upper().strip()], stock.market_index.upper().strip()
                )

                stock_info = yfinance.Ticker(stock_code)

                dividends = stock_info.dividends

                if dividends.empty:
                    continue

                for dividend_date, dividend_amount in dividends.items():
                    try:
                        dividend = Dividend(
                            dividend=dividend_amount, code=stock.code, date=pd.to_datetime(dividend_date).date()
                        )
                    except Exception:
                        continue

                    dividend_list.append(dividend)
                await DividendRepository.bulk_upsert(session=session, dividends=dividend_list)
            except Exception:
                continue

    logger.info("배당 수집을 마칩니다")


async def execute_async_task():
    logger.info("배당 수집을 시작합니다.")
    stock_list: list[StockInfo] = StockCodeFileReader.get_usa_korea_stock_code_list()

    async with get_mysql_session() as session:
        await insert_dividend_data(session, stock_list, BATCH_SIZE)


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
