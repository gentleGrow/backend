from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.module.asset.model import MarketIndexDaily


class MarketIndexDailyRepository:
    @staticmethod
    async def get_latest(session: AsyncSession, stock_codes: list[str]) -> list[MarketIndexDaily]:
        subquery = (
            select(MarketIndexDaily.name, func.max(MarketIndexDaily.date).label("max_date"))
            .where(MarketIndexDaily.name.in_(stock_codes))
            .group_by(MarketIndexDaily.name)
            .subquery()
        )

        market_daily_alias = aliased(MarketIndexDaily)

        stmt = select(market_daily_alias).join(
            subquery, (market_daily_alias.name == subquery.c.name) & (market_daily_alias.date == subquery.c.max_date)
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_range(session: AsyncSession, date_range: tuple[date, date], name: str) -> list[MarketIndexDaily]:
        start_date, end_date = date_range
        stmt = select(MarketIndexDaily).where(
            MarketIndexDaily.date.between(start_date, end_date), MarketIndexDaily.name == name
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def save_market_indexes(session: AsyncSession, market_indexes: list[MarketIndexDaily]) -> None:
        session.add_all(market_indexes)
        await session.commit()

    @staticmethod
    async def bulk_upsert(session: AsyncSession, market_indexes: list[MarketIndexDaily]) -> None:
        stmt = insert(MarketIndexDaily).values(
            [
                {
                    "name": market_index.name,
                    "date": market_index.date,
                    "open_price": market_index.open_price,
                    "high_price": market_index.high_price,
                    "low_price": market_index.low_price,
                    "close_price": market_index.close_price,
                    "volume": market_index.volume,
                }
                for market_index in market_indexes
            ]
        )

        update_dict = {
            "open_price": stmt.inserted.open_price,
            "high_price": stmt.inserted.high_price,
            "low_price": stmt.inserted.low_price,
            "close_price": stmt.inserted.close_price,
            "volume": stmt.inserted.volume,
        }

        upsert_stmt = stmt.on_duplicate_key_update(update_dict)

        try:
            await session.execute(upsert_stmt)
            await session.commit()
        except Exception:
            await session.rollback()
