import asyncio
import logging
from datetime import datetime
from os import getenv

import yfinance
from celery import shared_task
from dotenv import load_dotenv
from icecream import ic
from pandas import Series
from redis.asyncio import Redis

from app.data.common.services.stock_code_file_service import StockCodeFileReader
from app.data.yahoo.source.enums import Months
from app.data.yahoo.source.service import format_stock_code
from app.module.asset.enum import Country
from app.module.asset.schema import StockInfo
from database.dependency import get_redis_pool
from database.enum import EnvironmentType
from app.module.asset.redis_repository import RedisEstimateDividendRepository
from app.data.yahoo.source.constant import REDIS_ESTIMATE_EXPIRE_SECOND

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)


logger = logging.getLogger("dividend")
logger.setLevel(logging.INFO)


if ENVIRONMENT == EnvironmentType.PROD or ENVIRONMENT == EnvironmentType.DEV:
    file_handler = logging.FileHandler("/home/backend/dividend.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def save_estimate_dividend(redis_client: Redis, stock_list: list[StockInfo]):
    for stock in stock_list:
        try:
            stock_code = format_stock_code(
                stock.code.strip(), Country[stock.country.upper().strip()], stock.market_index.upper().strip()
            )

            stock_info = yfinance.Ticker(stock_code)

            dividends = stock_info.dividends
            if dividends.empty:
                continue

            # [TODO] stock_info에서 배당성장률 가져오기
            dividend_growth_rate = stock_info.info.get("dividendRate")

            estimate_dividend = get_estimate_dividend(dividends, dividend_growth_rate)
            if not estimate_dividend:
                continue

            RedisEstimateDividendRepository.set(redis_client, stock.code, estimate_dividend, REDIS_ESTIMATE_EXPIRE_SECOND)

        except Exception:
            continue


def get_estimate_dividend(dividends_raw: Series, dividend_growth_rate: float) -> list:
    dividends = {date: amount for date, amount in dividends_raw.items()}
    if not dividends:
        return []

    current_year = datetime.now().year
    last_year = current_year - 1
    year_before_last = current_year - 2
    year_before_last_last = current_year - 3
 
    current_year_dividends = {date: amount for date, amount in dividends.items() if date.year == current_year}
    last_year_dividends = {date: amount for date, amount in dividends.items() if date.year == last_year}
    year_before_last_dividends = {
        date: amount for date, amount in dividends.items() if date.year == year_before_last
    }
    year_before_last_last_dividends = {
        date: amount for date, amount in dividends.items() if date.year == year_before_last_last
    }


    if not last_year_dividends or not year_before_last_dividends or not year_before_last_last_dividends:
        return []
 
    return get_estimate_dividend_cache(
            current_year_dividends,
            last_year_dividends,
            year_before_last_dividends,
            year_before_last_last_dividends,
            dividend_growth_rate,
        )


def get_estimate_dividend_cache(
    current_year_dividends: dict,
    last_year_dividends: dict,
    year_before_last_dividends: dict,
    year_before_last_last_dividends: dict,
    dividend_growth_rate: float
) -> list:
    result = []

    for month in Months:
        current_month_exist = any(date.month == month.value for date in current_year_dividends.keys())
        if current_month_exist:
            continue

        last_year_exist = any(date.month == month.value for date in last_year_dividends.keys())
        year_before_last_exist = any(date.month == month.value for date in year_before_last_dividends.keys())
        year_before_last_last_exist = any(date.month == month.value for date in year_before_last_last_dividends.keys())

        if not (last_year_exist and year_before_last_exist and year_before_last_last_exist):
            continue

        estimated_dividend = calculate_estimated_dividend(last_year_dividends, month, dividend_growth_rate)
        if estimated_dividend:
            result.append((month, estimated_dividend))

    return result

def calculate_estimated_dividend(last_year_dividends: dict, month: Months, dividend_growth_rate: float) -> float | None:
    past_dividend = last_year_dividends.get(month.value)
    if past_dividend:
        return past_dividend * (1 + dividend_growth_rate)
    
    past_dividend = last_year_dividends.get(month.value)
    if past_dividend:
        return past_dividend * (1 + dividend_growth_rate) * (1 + dividend_growth_rate)
    
    past_dividend = last_year_dividends.get(month.value)
    if past_dividend:
        return past_dividend * (1 + dividend_growth_rate) * (1 + dividend_growth_rate) * (1 + dividend_growth_rate)
    
    return 


async def execute_async_task():
    logger.info("예상 배당 수집을 시작합니다.")
    stock_list: list[StockInfo] = StockCodeFileReader.get_usa_korea_stock_code_list()
    redis_client = get_redis_pool()
    await save_estimate_dividend(redis_client, stock_list)
    logger.info("예상 배당 수집이 완료되었습니다.")



@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())





