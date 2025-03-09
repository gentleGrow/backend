import asyncio
import json
import logging
from datetime import datetime
from os import getenv

import yfinance
from celery import shared_task
from dotenv import load_dotenv
from pandas import Series
from redis.asyncio import Redis

from app.data.common.services.stock_code_file_service import StockCodeFileReader
from app.data.yahoo.source.constant import REDIS_ESTIMATE_DIVIDEND_KEY, REDIS_ESTIMATE_EXPIRE_SECOND
from app.data.yahoo.source.enums import Months
from app.data.yahoo.source.service import format_stock_code
from app.module.asset.enum import Country
from app.module.asset.redis_repository import RedisEstimateDividendRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_redis_pool
from database.enum import EnvironmentType

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

            dividend_growth_rate = get_cagr_dividend_rate(dividends)

            estimate_dividend = get_estimate_dividend(dividends, dividend_growth_rate)
            if not estimate_dividend:
                continue

            await RedisEstimateDividendRepository.set(
                redis_client,
                REDIS_ESTIMATE_DIVIDEND_KEY + stock.code,
                json.dumps(estimate_dividend),
                REDIS_ESTIMATE_EXPIRE_SECOND,
            )

        except Exception:
            continue


def get_cagr_dividend_rate(dividends: Series) -> float:
    annual_dividends = dividends.resample("YE").sum()
    annual_dividends = annual_dividends[annual_dividends > 0]

    if len(annual_dividends) > 1:
        years = len(annual_dividends) - 1

        start_div = annual_dividends.iloc[0]
        end_div = annual_dividends.iloc[-1]
        return (end_div / start_div) ** (1 / years) - 1
    else:
        return 0


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
    year_before_last_dividends = {date: amount for date, amount in dividends.items() if date.year == year_before_last}
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
    dividend_growth_rate: float,
) -> list:
    result = []

    for month in Months:
        current_month_exist = any(date.month == month.value for date in current_year_dividends.keys())
        if current_month_exist:
            continue

        last_year_exist = any(date.month == month.value for date in last_year_dividends.keys())
        year_before_last_exist = any(date.month == month.value for date in year_before_last_dividends.keys())
        year_before_last_last_exist = any(date.month == month.value for date in year_before_last_last_dividends.keys())

        if not (last_year_exist or year_before_last_exist or year_before_last_last_exist):
            continue

        month_estimated_dividend = calculate_estimated_dividend(
            last_year_dividends,
            year_before_last_dividends,
            year_before_last_last_dividends,
            month,
            dividend_growth_rate,
        )

        if month_estimated_dividend:
            result.append((month.value, month_estimated_dividend))
    return result


def calculate_estimated_dividend(
    last_year_dividends: dict,
    year_before_last_dividends: dict,
    year_before_last_last_dividends: dict,
    month: Months,
    dividend_growth_rate: float,
) -> float | None:
    past_dividend = get_dividend_for_month(last_year_dividends, month)
    if past_dividend:
        return past_dividend * (1 + dividend_growth_rate)

    past_dividend = get_dividend_for_month(year_before_last_dividends, month)
    if past_dividend:
        return past_dividend * (1 + dividend_growth_rate) * (1 + dividend_growth_rate)

    past_dividend = get_dividend_for_month(year_before_last_last_dividends, month)
    if past_dividend:
        return past_dividend * (1 + dividend_growth_rate) * (1 + dividend_growth_rate) * (1 + dividend_growth_rate)

    return None


def get_dividend_for_month(dividends: dict, month: Months) -> float | None:
    for date, amount in dividends.items():
        if date.month == month.value:
            return amount
    return None


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
