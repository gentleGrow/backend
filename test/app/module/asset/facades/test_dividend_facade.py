from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from pytest import approx
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.auth.constant import DUMMY_USER_ID
from app.module.asset.enum import AssetType
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.facades.dividend_facade import DividendFacade


class TestDividendFacade:
    async def test_get_total_dividend(
        self,
        session: AsyncSession,
        redis_client: Redis,
        setup_all
    ):
        # Given
        assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)
        dividend_map: dict[str, float] = await DividendService.get_recent_map(session, assets)
        
        # When
        total_dividend = await DividendFacade.get_total_dividend(session, redis_client, assets)
        expected_total_dividend = 0.0
        for asset in assets:
            dividend_per_stock = dividend_map.get(asset.asset_stock.stock.code, 0.0)
            exchange_rate = ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            expected_total_dividend += dividend_per_stock * asset.asset_stock.quantity * exchange_rate
        
        # Then
        assert total_dividend == approx(expected_total_dividend)
        
        
        
        
        
        