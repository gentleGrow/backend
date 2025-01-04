from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.module.asset.model import MarketIndexMinutely
from os import getenv
import logging
from dotenv import load_dotenv
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

logger = logging.getLogger("current_index")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_index.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


class MarketIndexMinutelyRepository:
    @staticmethod
    async def get_latest(session: AsyncSession, stock_codes: list[str]) -> list[MarketIndexMinutely]:
        subquery = (
            select(MarketIndexMinutely.name, func.max(MarketIndexMinutely.datetime).label("max_datetime"))
            .where(MarketIndexMinutely.name.in_(stock_codes))
            .group_by(MarketIndexMinutely.name)
            .subquery()
        )

        stock_minutely_alias = aliased(MarketIndexMinutely)

        stmt = select(stock_minutely_alias).join(
            subquery,
            (stock_minutely_alias.name == subquery.c.name) & (stock_minutely_alias.datetime == subquery.c.max_datetime),
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def remove_by_datetime(session: AsyncSession, remove_time: datetime) -> None:
        stmt = delete(MarketIndexMinutely).where(MarketIndexMinutely.datetime < remove_time)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def get_by_range(session: AsyncSession, date_range: tuple, name: str) -> list[MarketIndexMinutely]:
        start_date, end_date = date_range
        stmt = select(MarketIndexMinutely).where(
            MarketIndexMinutely.datetime.between(start_date, end_date), MarketIndexMinutely.name == name
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_range_minute(
        session: AsyncSession,
        date_range: tuple,
        name: str,
    ) -> list[MarketIndexMinutely]:
        start_datetime, end_datetime = date_range

        stmt = select(MarketIndexMinutely).where(
            MarketIndexMinutely.datetime.between(start_datetime, end_datetime), MarketIndexMinutely.name == name
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def bulk_upsert(session: AsyncSession, market_indexes: list[MarketIndexMinutely]) -> None:
        try:
            stmt = insert(MarketIndexMinutely).values(
                [
                    {
                        "name": market_index.name,
                        "datetime": market_index.datetime,
                        "price": market_index.price,
                    }
                    for market_index in market_indexes
                ]
            )

            update_dict = {"price": stmt.inserted.price}

            upsert_stmt = stmt.on_duplicate_key_update(update_dict)

            await session.execute(upsert_stmt)
            await session.commit()
        except Exception as e:
            logger.error(f"bulk_upsert error: {e}")
            await session.rollback()
