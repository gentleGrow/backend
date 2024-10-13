from app.module.asset.model import Asset
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService


class DividendFacade:
    @staticmethod
    async def get_total_dividend(
        session: AsyncSession,
        redis_client: Redis,
        assets: list[Asset]
    ) -> float:
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)
        dividend_map: dict[str, float] = await DividendService.get_recent_map(session, assets)
        
        result = 0.0

        for asset in assets:
            result += (
                dividend_map.get(asset.asset_stock.stock.code, 0.0)
                * asset.asset_stock.quantity
                * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return result


