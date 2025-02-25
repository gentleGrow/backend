from app.module.asset.enum import AssetType
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AssetStockResponse
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
