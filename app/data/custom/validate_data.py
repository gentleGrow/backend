import asyncio
import logging

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

# from app.data.custom.email_service import send_email_via_gmail
# from database.dependency import get_mysql_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/backend/validate_data.log"),
        logging.StreamHandler(),
    ],
)


async def check_data(session: AsyncSession) -> str:
    pass


async def execute_async_task():
    logging.info("데이터 수집을 검증합니다.")
    # async with get_mysql_session() as session:
    #     pass


@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
