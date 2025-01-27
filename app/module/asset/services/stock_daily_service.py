from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.model import Asset, StockDaily
from app.module.asset.repository.stock_daily_repository import StockDailyRepository


class StockDailyService:
    async def get_latest_map_by_codes(self, session: AsyncSession, stock_codes: list[str]) -> dict[str, StockDaily]:
        lastest_stock_dailies: list[StockDaily] = await StockDailyRepository.get_latest(session, stock_codes)
        return {daily.code: daily for daily in lastest_stock_dailies}

    async def get_latest_map(self, session: AsyncSession, assets: list[Asset]) -> dict[str, StockDaily]:
        stock_codes = list(set([asset.asset_stock.stock.code for asset in assets]))
        lastest_stock_dailies: list[StockDaily] = await StockDailyRepository.get_latest(session, stock_codes)
        return {daily.code: daily for daily in lastest_stock_dailies}

    async def get_map_range(self, session: AsyncSession, assets: list[Asset]) -> dict[tuple[str, date], StockDaily]:
        stock_code_date_pairs = [(asset.asset_stock.stock.code, asset.asset_stock.trade_date) for asset in assets]
        stock_dailies: list[StockDaily] = await StockDailyRepository.get_stock_dailies_by_code_and_date(
            session, stock_code_date_pairs
        )
        return {(daily.code, daily.date): daily for daily in stock_dailies}

    async def get_date_map(
        self, session: AsyncSession, assets: list[Asset], target_date: date
    ) -> dict[tuple[str, date], StockDaily]:
        stock_code_date_pairs = [(asset.asset_stock.stock.code, target_date) for asset in assets]

        stock_dailies: list[StockDaily] = await StockDailyRepository.get_stock_dailies_by_code_and_date(
            session, stock_code_date_pairs
        )

        return {(daily.code, daily.date): daily for daily in stock_dailies}

    async def get_date_map_dates(
        self, session: AsyncSession, assets: list[Asset], target_dates: list[date]
    ) -> dict[tuple[str, date], StockDaily]:
        stock_code_date_pairs = [
            (asset.asset_stock.stock.code, target_date) for target_date in target_dates for asset in assets
        ]

        stock_dailies: list[StockDaily] = await StockDailyRepository.get_stock_dailies_by_code_and_date(
            session, stock_code_date_pairs
        )

        return {(daily.code, daily.date): daily for daily in stock_dailies}
