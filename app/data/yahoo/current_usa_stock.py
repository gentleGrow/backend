import asyncio
import logging
from os import getenv

import yfinance
from celery import shared_task
from dotenv import load_dotenv
from redis.asyncio import Redis
from icecream import ic
from app.data.common.constant import STOCK_CACHE_SECOND
from app.data.common.services.stock_code_file_service import StockCodeFileReader
from app.data.yahoo.source.service import format_stock_code
from app.module.asset.enum import Country
from app.module.asset.redis_repository import RedisRealTimeStockRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_redis_pool
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)


logger = logging.getLogger("current_usa_stock")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_usa_stock.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def process_stock_data(redis_client: Redis, stock_list: list[StockInfo]):
    redis_bulk_data = []

    for stock_info in stock_list:
        try:
            stock_code = format_stock_code(
                stock_info.code,
                Country[stock_info.country.upper().replace(" ", "_")],
                stock_info.market_index.upper(),
            )
        except Exception as e:
            logger.error(e)
            continue

        code, current_price = fetch_stock_price(stock_code, stock_info.code)
        if not current_price:
            continue
        redis_bulk_data.append((code, current_price))
    
    if redis_bulk_data:
        await RedisRealTimeStockRepository.bulk_save(redis_client, redis_bulk_data, expire_time=STOCK_CACHE_SECOND)


def fetch_stock_price(stock_code: str, code: str) -> tuple[str, float]:
    try:
        stock = yfinance.Ticker(stock_code)

        info_currentPrice = stock.info.get("currentPrice")
        info_bid = stock.info.get("bid")
        info_ask = stock.info.get("ask")
        current_price = info_currentPrice or info_bid or info_ask

        return code, current_price if current_price is not None else 0.0
    except Exception as e:
        logger.error(e)
        return code, 0.0


async def execute_async_task():
    logger.info("현재 미국 주가를 수집합니다.")
    stock_list: list[StockInfo] = StockCodeFileReader.get_usa_stock_code_list()
    redis_client = get_redis_pool()
    await process_stock_data(redis_client, stock_list)


@shared_task
def main():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        logger.info("main loop가 이미 실행 중입니다. task를 실행합니다.")
        asyncio.ensure_future(execute_async_task())
    else:
        loop.run_until_complete(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
