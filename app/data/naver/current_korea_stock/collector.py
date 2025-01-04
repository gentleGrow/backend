import asyncio
import logging
from os import getenv
from app.module.asset.schema import StockInfo
from celery import shared_task
from dotenv import load_dotenv
from app.data.common.services.stock_code_file_service import StockCodeFileReader
from database.enum import EnvironmentType
from app.data.naver.current_korea_stock.korea_stock_service import KoreaRealtimeStockCollector

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)


logger = logging.getLogger("current_korea_stock")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_korea_stock.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def execute_async_task():
    logger.info("현재 한국 주식을 수집합니다.")
    collector = KoreaRealtimeStockCollector()
    stock_list: list[StockInfo] = StockCodeFileReader.get_korea_stock_code_list()
    await collector.collect(stock_list)



@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())


