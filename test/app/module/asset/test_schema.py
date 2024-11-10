import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.constant import CurrencyType
from app.module.asset.dependencies.asset_dependency import get_asset_service
from app.module.asset.dependencies.asset_field_dependency import get_asset_field_service
from app.module.asset.dependencies.dividend_dependency import get_dividend_service
from app.module.asset.enum import AssetType
from app.module.asset.model import Asset
from app.module.asset.redis_repository import RedisExchangeRateRepository
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AggregateStockAsset, AssetStockResponse, StockAssetGroup, StockAssetSchema
from app.module.auth.constant import DUMMY_USER_ID


class TestAssetStockResponse:
    async def test_validate_assets_empty(self, setup_asset):
        # Given
        empty_assets: list[Asset] = []
        stock_fields = []

        # When
        response = AssetStockResponse.validate_assets(empty_assets, stock_fields)

        # Then
        expected_response = AssetStockResponse(
            stock_assets=[],
            aggregate_stock_assets=[],
            asset_fields=[],
            total_asset_amount=0.0,
            total_invest_amount=0.0,
            total_profit_rate=0.0,
            total_profit_amount=0.0,
            total_dividend_amount=0.0,
            dollar_exchange=0.0,
            won_exchange=0.0,
        )

        assert response == expected_response

    async def test_validate_assets_non_empty(self, session, setup_asset):
        # Given
        non_empty_assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        stock_fields = []

        # When
        response = AssetStockResponse.validate_assets(non_empty_assets, stock_fields)

        # Then
        assert response is None

    async def test_parse(self, session: AsyncSession, redis_client: Redis, setup_all):
        # Given
        asset_service = get_asset_service()
        dividend_service = get_dividend_service()
        asset_field_service = get_asset_field_service()

        assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        asset_fields = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)
        stock_asset_elements: list[StockAssetSchema] = await asset_service.get_stock_assets(
            session=session, redis_client=redis_client, assets=assets, asset_fields=asset_fields
        )

        aggregate_stock_assets: list[AggregateStockAsset] = asset_service.aggregate_stock_assets(stock_asset_elements)
        stock_assets: list[StockAssetGroup] = asset_service.group_stock_assets(
            stock_asset_elements, aggregate_stock_assets
        )

        total_asset_amount = await asset_service.get_total_asset_amount(session, redis_client, assets)
        total_invest_amount = await asset_service.get_total_investment_amount(session, redis_client, assets)
        total_dividend_amount = await dividend_service.get_total_dividend(session, redis_client, assets)
        dollar_exchange = await RedisExchangeRateRepository.get(
            redis_client, f"{CurrencyType.KOREA}_{CurrencyType.USA}"
        )
        won_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.USA}_{CurrencyType.KOREA}")

        # When
        stock_asset_response = AssetStockResponse.parse(
            stock_assets=stock_assets,
            asset_fields=asset_fields,
            total_asset_amount=total_asset_amount,
            total_invest_amount=total_invest_amount,
            total_dividend_amount=total_dividend_amount,
            dollar_exchange=dollar_exchange if dollar_exchange else 0.0,
            won_exchange=won_exchange if won_exchange else 0.0,
        )

        # Then
        expected_profit_rate = ((total_asset_amount - total_invest_amount) / total_invest_amount) * 100
        assert stock_asset_response.total_profit_rate == pytest.approx(expected_profit_rate)

        expected_profit_amount = total_asset_amount - total_invest_amount
        assert stock_asset_response.total_profit_amount == pytest.approx(expected_profit_amount)

        assert len(stock_asset_response.stock_assets) == len(stock_assets)
