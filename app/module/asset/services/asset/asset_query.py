from datetime import date

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.model import Asset, StockDaily
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_service import StockService


class AssetQuery:
    def __init__(
        self,
        stock_daily_service: StockDailyService,
        exchange_rate_service: ExchangeRateService,
        stock_service: StockService,
        dividend_service: DividendService,
    ):
        self.stock_daily_service = stock_daily_service
        self.exchange_rate_service = exchange_rate_service
        self.stock_service = stock_service
        self.dividend_service = dividend_service

    async def get_all_data(
        self, session: AsyncSession, redis_client: Redis, assets: list[Asset]
    ) -> tuple[
        dict[tuple[str, date], StockDaily],  # stock_daily_map
        dict[str, StockDaily],  # lastest_stock_daily_map
        dict[str, float],  # dividend_map
        dict[str, float],  # exchange_rate_map
        dict[str, float],  # current_stock_price_map
    ]:
        stock_daily_map: dict[tuple[str, date], StockDaily] = await self.stock_daily_service.get_map_range(
            session, assets
        )
        lastest_stock_daily_map: dict[str, StockDaily] = await self.stock_daily_service.get_latest_map(session, assets)
        dividend_map: dict[str, float] = await self.dividend_service.get_recent_map(session, assets)
        exchange_rate_map: dict[str, float] = await self.exchange_rate_service.get_exchange_rate_map(redis_client)
        current_stock_price_map: dict[str, float] = await self.stock_service.get_current_stock_price(
            redis_client, lastest_stock_daily_map, assets
        )

        return (stock_daily_map, lastest_stock_daily_map, dividend_map, exchange_rate_map, current_stock_price_map)
