from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.model import Asset, StockMinutely
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository


class StockMinutelyService:
    async def get_datetime_interval_map(
        self,
        session: AsyncSession,
        interval_start: datetime,
        interval_end: datetime,
        assets: list[Asset],
        interval: int,
    ) -> dict[str, float]:
        stock_minute_list: list[StockMinutely] = await StockMinutelyRepository.get_by_range_interval_minute(
            session,
            (interval_start, interval_end),
            list(set([asset.asset_stock.stock.code for asset in assets])),
            interval,
        )

        return {
            f"{stock_minutely.code}_{stock_minutely.datetime}": stock_minutely.price
            for stock_minutely in stock_minute_list
        }
