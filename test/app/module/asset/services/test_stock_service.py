from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.dependencies.stock_daily_dependency import get_stock_daily_service
from app.module.asset.dependencies.stock_dependency import get_stock_service
from app.module.asset.enum import AssetType
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock.stock_service import StockService
from app.module.auth.constant import DUMMY_USER_ID


class TestStockService:
    async def test_get_stock_map(self, session: AsyncSession, setup_asset, setup_stock, setup_user):
        # Given
        stock_service: StockService = get_stock_service()

        stock_code = "AAPL"

        expected_stock = await StockRepository.get_by_code(session, stock_code)
        expected_stock_map = {expected_stock.code: expected_stock}

        # When
        stock_map = await stock_service.get_stock_map(session, stock_code)

        # Then
        assert expected_stock_map is not None
        assert stock_map is not None

        for code, stock in expected_stock_map.items():
            assert stock_map.get(code) == stock

    async def test_get_current_stock_price(
        self,
        session: AsyncSession,
        redis_client: Redis,
        setup_user,
        setup_stock_daily,
        setup_realtime_stock_price,
        setup_asset,
    ):
        # Given
        stock_daily_service: StockDailyService = get_stock_daily_service()
        stock_service: StockService = get_stock_service()

        assets = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        lastest_stock_daily_map = await stock_daily_service.get_latest_map(session, assets)

        expected_keys, expected_values = setup_realtime_stock_price
        current_prices = await stock_service.get_current_stock_price(redis_client, lastest_stock_daily_map, assets)

        # Then
        for stock_code, expected_value in zip(expected_keys, expected_values):
            assert current_prices[stock_code] == float(expected_value)

        for asset in assets:
            stock_code = asset.asset_stock.stock.code
            assert stock_code in current_prices

        for stock_code, stock_daily in lastest_stock_daily_map.items():
            if stock_code not in expected_keys:
                assert current_prices[stock_code] == stock_daily.adj_close_price
