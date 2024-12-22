import asyncio
import logging
from datetime import timedelta
from os import getenv
from zoneinfo import ZoneInfo

from celery import shared_task
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import get_now_date, get_now_datetime
from app.data.common.constant import VALIDATE_CODES, VALIDATE_INDICES
from app.data.custom.email_service import send_email
from app.module.asset.repository.market_index_daily_repository import MarketIndexDailyRepository
from app.module.asset.repository.market_index_minutely_repository import MarketIndexMinutelyRepository
from app.module.asset.repository.stock_daily_repository import StockDailyRepository
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from database.dependency import get_mysql_session
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)
SENDER_EMAIL = getenv("SENDER_EMAIL", None)

logger = logging.getLogger("validate_data")
logger.setLevel(logging.INFO)


if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/validate_data.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


async def check_data(session: AsyncSession) -> None:
    stock_dailies = await StockDailyRepository.get_latest(session, VALIDATE_CODES)
    index_dailies = await MarketIndexDailyRepository.get_latest(session, VALIDATE_INDICES)
    stock_minutelies = await StockMinutelyRepository.get_latest(session, VALIDATE_CODES)
    index_minutelies = await MarketIndexMinutelyRepository.get_latest(session, VALIDATE_INDICES)

    past_date = get_now_date() - timedelta(days=1)
    past_datetime = get_now_datetime() - timedelta(days=1)

    if not SENDER_EMAIL:
        return

    for stock_daily in stock_dailies:
        if stock_daily.date < past_date:
            send_email(
                "Stock Daily 미수집",
                f"{stock_daily.date} 날짜에 {stock_daily.code}가 수집되지 않았습니다.",
                SENDER_EMAIL,
            )

    for index_daily in index_dailies:
        if not index_daily or index_daily.date is None or index_daily.name is None:
            continue

        if index_daily.date < past_date:
            send_email(
                "Index Daily 미수집",
                f"{index_daily.date} 날짜에 {index_daily.name}가 수집되지 않았습니다.",
                SENDER_EMAIL,
            )

    for stock_minutely in stock_minutelies:
        if not stock_minutely or stock_minutely.datetime is None or stock_minutely.code is None:
            continue

        if stock_minutely.datetime.replace(tzinfo=ZoneInfo("Asia/Seoul")) < past_datetime:
            send_email(
                "Stock Minutely 미수집",
                f"{stock_minutely.datetime} 시간에 {stock_minutely.code}가 수집되지 않았습니다.",
                SENDER_EMAIL,
            )

    for index_minutely in index_minutelies:
        if not index_minutely or index_minutely.datetime is None or index_minutely.name is None:
            continue

        if index_minutely.datetime.replace(tzinfo=ZoneInfo("Asia/Seoul")) < past_datetime:
            send_email(
                "Index Minutely 미수집",
                f"{index_minutely.datetime} 시간에 {index_minutely.name}가 수집되지 않았습니다.",
                SENDER_EMAIL,
            )


async def execute_async_task():
    logger.info("데이터 수집 현황을 확인합니다.")
    async with get_mysql_session() as session:
        await check_data(session)


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
