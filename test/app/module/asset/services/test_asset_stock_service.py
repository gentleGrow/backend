from datetime import date

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.dependencies.asset_stock_dependency import get_asset_stock_service
from app.module.asset.dependencies.exchange_rate_dependency import get_exchange_rate_service
from app.module.asset.dependencies.stock_daily_dependency import get_stock_daily_service
from app.module.asset.dependencies.stock_dependency import get_stock_service
from app.module.asset.enum import AccountType, AssetType, InvestmentBankType, PurchaseCurrencyType, TradeType
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AssetStockPostRequest
from app.module.asset.services.asset_stock.asset_stock_service import AssetStockService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock.stock_service import StockService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.auth.constant import DUMMY_USER_ID


class TestAssetStockService:
    @pytest.mark.parametrize(
        "total_asset_amount, total_invest_amount, real_value_rate, expected_real_profit_rate",
        [
            (1200000.0, 1000000.0, 3.0, 17.0),
            (800000.0, 1000000.0, 3.0, -23.0),
            (1000000.0, 1000000.0, 3.0, -3.0),
            (0.0, 1000000.0, 3.0, -103.0),
            (1000000.0, 0.0, 3.0, 0.0),
        ],
    )
    def test_get_total_profit_rate_real(
        self,
        total_asset_amount,
        total_invest_amount,
        real_value_rate,
        expected_real_profit_rate,
    ):
        # Given
        asset_stock_service: AssetStockService = get_asset_stock_service()

        # When
        actual_real_profit_rate = asset_stock_service.get_total_profit_rate_real(
            total_asset_amount=total_asset_amount,
            total_invest_amount=total_invest_amount,
            real_value_rate=real_value_rate,
        )

        # Then
        assert actual_real_profit_rate == pytest.approx(expected_real_profit_rate, rel=1e-2)

    async def test_save_asset_stock_by_post(self, session: AsyncSession, setup_stock, setup_stock_daily, setup_user):
        # Given
        asset_stock_service: AssetStockService = get_asset_stock_service()
        stock_id = 1

        request_data = AssetStockPostRequest(
            trade_date=date(2024, 8, 13),
            purchase_currency_type=PurchaseCurrencyType.USA,
            quantity=10,
            stock_code="AAPL",
            account_type=AccountType.ISA,
            investment_bank=InvestmentBankType.KB,
            trade_price=500.0,
            trade=TradeType.BUY,
        )

        # When
        await asset_stock_service.save_asset_stock_by_post(session, request_data, DUMMY_USER_ID)
        saved_assets = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)

        # Then
        assert len(saved_assets) == 1
        assert saved_assets[0].asset_stock.stock_id == stock_id

    async def test_get_total_investment_amount(
        self, session: AsyncSession, redis_client: Redis, setup_asset, setup_exchange_rate, setup_stock_daily
    ):
        # Given
        exchange_rate_service: ExchangeRateService = get_exchange_rate_service()
        asset_stock_service: AssetStockService = get_asset_stock_service()
        stock_daily_service: StockDailyService = get_stock_daily_service()

        assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        exchange_rate_map = await exchange_rate_service.get_exchange_rate_map(redis_client)
        stock_daily_map = await stock_daily_service.get_map_range(session, assets)

        # When
        total_investment_amount = asset_stock_service.get_total_investment_amount(
            assets=assets,
            stock_daily_map=stock_daily_map,
            exchange_rate_map=exchange_rate_map,
        )

        expected_total_investment_amount = 0.0
        for asset in assets:
            stock_daily = stock_daily_map.get((asset.asset_stock.stock.code, asset.asset_stock.trade_date), None)
            if stock_daily is None:
                continue

            if asset.asset_stock.purchase_currency_type == PurchaseCurrencyType.USA:
                invest_price = (
                    asset.asset_stock.trade_price
                    * exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
                    if asset.asset_stock.trade_price
                    else stock_daily.adj_close_price
                    * exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
                )
            else:
                invest_price = (
                    asset.asset_stock.trade_price if asset.asset_stock.trade_price else stock_daily.adj_close_price
                )

            expected_total_investment_amount += invest_price * asset.asset_stock.quantity

        # Then
        assert total_investment_amount == pytest.approx(expected_total_investment_amount)

    async def test_get_total_asset_amount(
        self,
        session: AsyncSession,
        redis_client: Redis,
        setup_asset,
        setup_realtime_stock_price,
        setup_exchange_rate,
    ):
        # Given
        stock_daily_service: StockDailyService = get_stock_daily_service()
        stock_service: StockService = get_stock_service()
        exchange_rate_service: ExchangeRateService = get_exchange_rate_service()
        asset_stock_service: AssetStockService = get_asset_stock_service()

        assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        lastest_stock_daily_map = await stock_daily_service.get_latest_map(session, assets)
        current_stock_price_map = await stock_service.get_current_stock_price(
            redis_client, lastest_stock_daily_map, assets
        )
        exchange_rate_map = await exchange_rate_service.get_exchange_rate_map(redis_client)

        # When
        total_asset_amount = asset_stock_service.get_total_asset_amount(
            assets=assets,
            current_stock_price_map=current_stock_price_map,
            exchange_rate_map=exchange_rate_map,
        )

        # Then
        expected_total_asset_amount = 0.0
        for asset in assets:
            current_price = current_stock_price_map.get(asset.asset_stock.stock.code)
            exchange_rate = exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            expected_total_asset_amount += current_price * asset.asset_stock.quantity * exchange_rate

        assert total_asset_amount == pytest.approx(expected_total_asset_amount)
