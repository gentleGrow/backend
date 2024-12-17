from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.module.asset.model import StockMinutely


class StockMinutelyRepository:
    @staticmethod
    async def get_latest(session: AsyncSession, stock_codes: list[str]) -> list[StockMinutely]:
        subquery = (
            select(StockMinutely.code, func.max(StockMinutely.datetime).label("max_datetime"))
            .where(StockMinutely.code.in_(stock_codes))
            .group_by(StockMinutely.code)
            .subquery()
        )

        stock_minutely_alias = aliased(StockMinutely)

        stmt = select(stock_minutely_alias).join(
            subquery,
            (stock_minutely_alias.code == subquery.c.code) & (stock_minutely_alias.datetime == subquery.c.max_datetime),
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def remove_by_datetime(session: AsyncSession, remove_time: datetime) -> None:
        stmt = delete(StockMinutely).where(StockMinutely.datetime < remove_time)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def get_by_range_minute(
        session: AsyncSession,
        date_range: tuple,
        codes: list[str],
    ) -> list[StockMinutely]:
        start_datetime, end_datetime = date_range

        stmt = select(StockMinutely).where(
            StockMinutely.datetime.between(start_datetime, end_datetime),
            StockMinutely.code.in_(codes),
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def bulk_upsert(session: AsyncSession, stocks: list[StockMinutely]) -> None:
        stmt = insert(StockMinutely).values(
            [
                {
                    "code": stock.code,
                    "datetime": stock.datetime,
                    "price": stock.price,
                }
                for stock in stocks
            ]
        )

        update_dict = {"price": stmt.inserted.price}

        upsert_stmt = stmt.on_duplicate_key_update(update_dict)

        try:
            await session.execute(upsert_stmt)
            await session.commit()
        except Exception:
            await session.rollback()
