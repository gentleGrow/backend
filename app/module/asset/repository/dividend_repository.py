from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func

from app.module.asset.model import Dividend


class DividendRepository:
    @staticmethod
    async def get_dividends_recent(session: AsyncSession, stock_codes: list[str]) -> list[Dividend]:
        subquery = (
            select(Dividend.code, func.max(Dividend.date).label("max_date"))
            .where(Dividend.code.in_(stock_codes))
            .group_by(Dividend.code)
            .subquery()
        )

        query = select(Dividend).join(
            subquery, (Dividend.code == subquery.c.code) & (Dividend.date == subquery.c.max_date)
        )

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_dividend(session: AsyncSession, code: str) -> Dividend:
        result = await session.execute(select(Dividend).where(Dividend.code == code))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_dividends(session: AsyncSession, stock_codes: list[str]) -> list[Dividend]:
        result = await session.execute(select(Dividend).where(Dividend.code.in_(stock_codes)))
        return result.scalars().all()

    @staticmethod
    async def save(session: AsyncSession, dividend: Dividend) -> None:
        session.add(dividend)
        await session.commit()

    @staticmethod
    async def upsert(session: AsyncSession, dividend: Dividend) -> None:
        dividend_value = float(dividend.dividend)
        stock_code_value = str(dividend.code)

        query_statement = insert(Dividend).values(
            dividend=dividend_value,
            stock_code=stock_code_value,
        )

        on_duplicate_stmt = query_statement.on_duplicate_key_update(
            dividend=query_statement.inserted.dividend, updated_at=func.now()
        )

        await session.execute(on_duplicate_stmt)
        await session.commit()

    @staticmethod
    async def bulk_upsert(session: AsyncSession, dividends: list[Dividend]) -> None:
        stmt = insert(Dividend).values(
            [
                {"dividend": float(dividend.dividend), "code": str(dividend.code), "date": dividend.date}
                for dividend in dividends
            ]
        )

        update_stmt = {"dividend": stmt.inserted.dividend, "updated_at": func.now()}

        upsert_stmt = stmt.on_duplicate_key_update(update_stmt)

        try:
            await session.execute(upsert_stmt)
            await session.commit()
        except Exception:
            await session.rollback()
