from sqlalchemy import update
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func

from app.module.asset.model import Stock


class StockRepository:
    @staticmethod
    async def get_countries_stock(session: AsyncSession, countries: list[str]) -> list[Stock]:
        query = select(Stock).where(Stock.country.in_(countries))
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_all(session: AsyncSession) -> list[Stock]:
        stmt = select(Stock)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_stock(session: AsyncSession, stock_id: int) -> Stock | None:
        stock_instance = await session.execute(select(Stock).where(Stock.id == stock_id))
        return stock_instance.scalar_one_or_none()

    @staticmethod
    async def get_stocks(session: AsyncSession, stock_ids: list[int]) -> list[Stock]:
        result = await session.execute(select(Stock).where(Stock.id.in_(stock_ids)))
        return result.scalars().all()

    @staticmethod
    async def get_by_code(session: AsyncSession, stock_code: str) -> Stock | None:
        result = await session.execute(select(Stock).where(Stock.code == stock_code))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_codes(session: AsyncSession, stock_codes: list[str]) -> list[Stock]:
        result = await session.execute(select(Stock).where(Stock.code.in_(stock_codes)))
        return result.scalars().all()

    @staticmethod
    async def save(session: AsyncSession, stock: Stock) -> None:
        session.add(stock)
        await session.commit()

    @staticmethod
    async def bulk_save(session: AsyncSession, stocks: list[Stock]) -> None:
        session.add_all(stocks)
        await session.commit()

    @staticmethod
    async def bulk_upsert(session: AsyncSession, stocks: list[Stock]) -> None:
        stmt = insert(Stock).values(
            [
                {
                    "code": stock.code,
                    "name_kr": stock.name_kr,
                    "name_en": stock.name_en,
                    "market_index": stock.market_index,
                    "country": stock.country,
                }
                for stock in stocks
            ]
        )

        update_dict = {
            "name_kr": stmt.inserted.name_kr,
            "name_en": stmt.inserted.name_en,
            "market_index": stmt.inserted.market_index,
            "country": stmt.inserted.country,
            "updated_at": func.now(),
        }

        upsert_stmt = stmt.on_duplicate_key_update(update_dict)

        try:
            await session.execute(upsert_stmt)
            await session.commit()
        except Exception:
            await session.rollback()

    @staticmethod
    async def update_code_by_name_kr(session: AsyncSession, name_kr: str, new_code: str) -> None:
        stmt = update(Stock).where(Stock.name_kr == name_kr).values(code=new_code, updated_at=func.now())

        try:
            await session.execute(stmt)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
