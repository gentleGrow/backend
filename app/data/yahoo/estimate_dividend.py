# import asyncio
# import logging
# from datetime import datetime
# from os import getenv

# import yfinance
# from celery import shared_task
# from dotenv import load_dotenv
# from icecream import ic
# from pandas import Series
# from redis.asyncio import Redis

# from app.data.common.services.stock_code_file_service import StockCodeFileReader
# from app.data.yahoo.source.constant import BATCH_SIZE
# from app.data.yahoo.source.enums import Quarters
# from app.data.yahoo.source.service import format_stock_code
# from app.module.asset.enum import Country
# from app.module.asset.schema import StockInfo
# from database.dependency import get_redis_pool
# from database.enum import EnvironmentType

# load_dotenv()

# ENVIRONMENT = getenv("ENVIRONMENT", None)


# logger = logging.getLogger("dividend")
# logger.setLevel(logging.INFO)


# if ENVIRONMENT == EnvironmentType.PROD or ENVIRONMENT == EnvironmentType.DEV:
#     file_handler = logging.FileHandler("/home/backend/dividend.log", delay=False)
#     file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
#     logger.addHandler(file_handler)


# async def save_estimate_dividend(redis_client: Redis, stock_list: list[StockInfo], batch_size: int):
#     for i in range(0, len(stock_list), batch_size):
#         stock_list_batch = stock_list[i : i + batch_size]
#         for stock in stock_list_batch:
#             try:
#                 stock_code = format_stock_code(
#                     stock.code.strip(), Country[stock.country.upper().strip()], stock.market_index.upper().strip()
#                 )

#                 stock_code = "SCHD"

#                 stock_info = yfinance.Ticker(stock_code)

#                 dividends = stock_info.dividends
#                 if dividends.empty:
#                     continue

#                 estimate_dividend = calculate_this_year_dividend(dividends)

#                 if not estimate_dividend:
#                     continue

#             except Exception:
#                 continue


# def calculate_this_year_dividend(dividends_raw: Series) -> list:
#     dividends = {date: amount for date, amount in dividends_raw.items()}
#     if not dividends:
#         return []

#     current_year = datetime.now().year
#     last_year = current_year - 1
#     year_before_last = current_year - 2
#     year_before_last_last = current_year - 3

#     try:
#         current_year_dividends = {date: amount for date, amount in dividends.items() if date.year == current_year}
#         last_year_dividends = {date: amount for date, amount in dividends.items() if date.year == last_year}
#         year_before_last_dividends = {
#             date: amount for date, amount in dividends.items() if date.year == year_before_last
#         }
#         year_before_last_last_dividends = {
#             date: amount for date, amount in dividends.items() if date.year == year_before_last_last
#         }
#     except Exception:
#         return []

#     if not last_year_dividends or not year_before_last_dividends or not year_before_last_last_dividends:
#         return []

#     average_growth_rate = calculate_dividend_growth_rate(last_year_dividends, year_before_last_dividends)
#     current_year_estimate_dividend(
#         current_year_dividends,
#         last_year_dividends,
#         year_before_last_dividends,
#         year_before_last_last_dividends,
#         average_growth_rate,
#     )

#     return


# def current_year_estimate_dividend(
#     current_year_dividends: dict,
#     last_year_dividends: dict,
#     year_before_last_dividends: dict,
#     year_before_last_last_dividends: dict,
#     average_growth_rate: list,
# ) -> dict:
#     ic(current_year_dividends)
#     ic(last_year_dividends)
#     ic(year_before_last_dividends)
#     ic(year_before_last_last_dividends)
#     ic(average_growth_rate)


# def calculate_dividend_growth_rate(last_year_dividends: dict, year_before_last_dividends: dict) -> list:
#     quarterly_growth_rates = []

#     for quarter in Quarters:
#         last_year_total = sum(amount for date, amount in last_year_dividends.items() if date.month in quarter.value)
#         year_before_last_total = sum(
#             amount for date, amount in year_before_last_dividends.items() if date.month in quarter.value
#         )

#         if last_year_total == 0 or year_before_last_total == 0:
#             growth_rate = 0
#         else:
#             growth_rate = (last_year_total - year_before_last_total) / year_before_last_total

#         quarterly_growth_rates.append(growth_rate)

#     return quarterly_growth_rates


# async def execute_async_task():
#     logger.info("예상 배당 수집을 시작합니다.")
#     stock_list: list[StockInfo] = StockCodeFileReader.get_usa_korea_stock_code_list()
#     redis_client = get_redis_pool()
#     await save_estimate_dividend(redis_client, stock_list, BATCH_SIZE)
#     logger.info("예상 배당 수집이 완료되었습니다.")


# @shared_task
# def main():
#     asyncio.run(execute_async_task())


# if __name__ == "__main__":
#     asyncio.run(execute_async_task())
