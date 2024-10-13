import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.module.asset.enum import AssetType, PurchaseCurrencyType
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.auth.constant import DUMMY_USER_ID
from app.module.asset.facades.asset_facade import AssetFacade
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_service import StockService

class TestAssetFacade:
    async def test_get_total_investment_amount(
        self,
        session: AsyncSession,
        redis_client: Redis,
        setup_all
    ):
        # Given
        assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)
        stock_daily_map = await StockDailyService.get_map_range(session, assets)
        
        # When
        total_investment_amount = await AssetFacade.get_total_investment_amount(
            session=session,
            redis_client=redis_client,
            assets=assets
        )
        
        expected_total_investment_amount = 0.0
        for asset in assets:
            stock_daily = stock_daily_map.get((asset.asset_stock.stock.code, asset.asset_stock.purchase_date), None)
            if stock_daily is None:
                continue

            if asset.asset_stock.purchase_currency_type == PurchaseCurrencyType.USA:
                invest_price = (
                    asset.asset_stock.purchase_price
                    * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
                    if asset.asset_stock.purchase_price
                    else stock_daily.adj_close_price
                    * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
                )
            else:
                invest_price = (
                    asset.asset_stock.purchase_price
                    if asset.asset_stock.purchase_price
                    else stock_daily.adj_close_price
                )

            expected_total_investment_amount += invest_price * asset.asset_stock.quantity

        # Then
        assert total_investment_amount == pytest.approx(expected_total_investment_amount)
    
    
    
    
    async def test_get_total_asset_amount(
        self,
        session: AsyncSession,
        redis_client: Redis,
        setup_all
    ):
        # Given
        assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        
        expected_total_asset_amount = 0.0
        lastest_stock_daily_map = await StockDailyService.get_latest_map(session, assets)
        current_stock_price_map = await StockService.get_current_stock_price(redis_client, lastest_stock_daily_map, assets)
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)

        for asset in assets:
            stock_code = asset.asset_stock.stock.code
            quantity = asset.asset_stock.quantity
            current_price = current_stock_price_map.get(stock_code, 0.0)
            exchange_rate = ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            expected_total_asset_amount += current_price * quantity * exchange_rate

        # When
        actual_total_asset_amount = await AssetFacade.get_total_asset_amount(
            session=session,
            redis_client=redis_client,
            assets=assets
        )

        # Then
        assert actual_total_asset_amount == pytest.approx(expected_total_asset_amount, rel=1e-2)
