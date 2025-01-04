import asyncio
import logging
from os import getenv

from celery import shared_task
from dotenv import load_dotenv

from app.data.common.services.stock_code_file_service import StockCodeFileReader
from app.data.naver.current_korea_stock.korea_stock_service import KoreaRealtimeStockCollector
from app.module.asset.schema import StockInfo
from database.enum import EnvironmentType

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
    redis_len, db_len = await collector.collect(stock_list)
    logger.info(f"redis_bulk_data:{redis_len}와 db_bulk_data:{db_len}개의 데이터가 저장되었습니다.")


@shared_task
def main():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.info("main loop가 이미 실행 중입니다. task를 실행합니다.")
            asyncio.ensure_future(execute_async_task())
        else:
            logger.info("현재 시장 지수를 수집합니다.")
            asyncio.run(execute_async_task())
    except RuntimeError as e:
        logger.error(f"이벤트 루프 실행 중 문제가 발생했습니다: {e}")



if __name__ == "__main__":
    asyncio.run(execute_async_task())
