from datetime import date, datetime

from freezegun import freeze_time
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.dependencies.asset_dependency import get_asset_service
from app.module.asset.dependencies.exchange_rate_dependency import get_exchange_rate_service
from app.module.asset.dependencies.stock_daily_dependency import get_stock_daily_service
from app.module.asset.enum import AccountType, AssetType, InvestmentBankType, PurchaseCurrencyType, TradeType
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AssetStockPutRequest
from app.module.asset.services.asset.asset_service import AssetService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.auth.constant import DUMMY_USER_ID


class TestAssetService:
    async def test_get_total_asset_amount_with_datetime(self, redis_client: Redis, session: AsyncSession, setup_all):
        # Given
        exchange_rate_service: ExchangeRateService = get_exchange_rate_service()
        stock_daily_service: StockDailyService = get_stock_daily_service()
        asset_service: AssetService = get_asset_service()

        exchange_rate_map: dict[str, float] = await exchange_rate_service.get_exchange_rate_map(redis_client)

        stock_datetime_price_map = {
            "AAPL_2024-08-13 10:30:00": 150.0,
            "AAPL_2024-08-13 10:45:00": 151.0,
            "TSLA_2024-08-13 10:30:00": 720.0,
            "TSLA_2024-08-13 10:45:00": 725.0,
        }

        current_datetime = datetime(2024, 8, 13, 10, 30)
        assets = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        stock_daily_map = await stock_daily_service.get_map_range(session, assets)

        # When
        total_amount = asset_service.get_total_asset_amount_with_datetime(
            assets=assets,
            exchange_rate_map=exchange_rate_map,
            stock_datetime_price_map=stock_datetime_price_map,
            current_datetime=current_datetime,
            stock_daily_map=stock_daily_map,
        )

        expected_amount = 150.0 * 1 * 1300.0 + 720.0 * 2 * 1300.0 + 72000 * 1 * 1

        # Then
        assert total_amount == expected_amount

    @freeze_time("2024-08-15")
    async def test_asset_list_from_days(self, session: AsyncSession, setup_all):
        # Given
        asset_service: AssetService = get_asset_service()
        days = 5
        assets = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)

        # When
        result = asset_service.asset_list_from_days(assets, days)

        # Then
        assert isinstance(result, dict)
        assert len(result) == 3

    async def test_get_asset_map_success(
        self,
        session: AsyncSession,
        setup_asset,
    ):
        # Given
        asset_service: AssetService = get_asset_service()
        asset_id = 1

        # When
        result = await asset_service.get_asset_map(session, asset_id)

        # Then
        assert result is not None
        assert isinstance(result, dict)
        assert result[asset_id].id == asset_id
        assert result[asset_id].asset_type == AssetType.STOCK
        assert result[asset_id].asset_stock.trade_price == 500.0

    async def test_update_asset_stock(self, session: AsyncSession, setup_all):
        # Given
        asset_service: AssetService = get_asset_service()
        asset_id = 1
        asset: Asset = await AssetRepository.get_asset_by_id(session, asset_id)

        request_data = AssetStockPutRequest(
            id=asset.id,
            trade_date=date(2024, 9, 1),
            purchase_currency_type=PurchaseCurrencyType.KOREA,
            quantity=5,
            stock_code="005930",
            account_type=AccountType.REGULAR,
            investment_bank=InvestmentBankType.KB,
            trade_price=600.0,
            trade=TradeType.BUY,
        )

        # When
        await asset_service.save_asset_by_put(session, request_data)
        updated_asset = await AssetRepository.get_asset_by_id(session, asset_id)

        # Then
        assert updated_asset.asset_stock.account_type == AccountType.REGULAR
        assert updated_asset.asset_stock.investment_bank == InvestmentBankType.KB
        assert updated_asset.asset_stock.purchase_currency_type == PurchaseCurrencyType.KOREA
        assert updated_asset.asset_stock.trade_date == date(2024, 9, 1)
        assert updated_asset.asset_stock.trade_price == 600.0
        assert updated_asset.asset_stock.quantity == 5
        assert updated_asset.asset_stock.trade == TradeType.BUY
