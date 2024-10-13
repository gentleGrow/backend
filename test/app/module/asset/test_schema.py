import pytest
from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.enum import AssetType
from app.module.asset.facades.asset_facade import AssetFacade
from app.module.asset.facades.dividend_facade import DividendFacade
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AssetStockResponse, UpdateAssetFieldRequest
from app.module.asset.services.asset_field_service import AssetFieldService
from app.module.auth.constant import DUMMY_USER_ID


class TestUpdateAssetFieldRequest:
    def test_validate_request_data_missing_required_fields(self):
        # Given
        request_data = UpdateAssetFieldRequest(root=["종목명", "수량"])

        # When
        try:
            UpdateAssetFieldRequest.validate_request_data(request_data)
            validation_passed = True
        except HTTPException as e:
            validation_passed = False
            error_detail = e.detail

        # Then
        assert validation_passed is False
        assert "필수 필드가 누락되었습니다" in error_detail
        assert "['구매일자']" in error_detail

    def test_validate_request_data_success(self):
        # Given
        valid_request_data = UpdateAssetFieldRequest(root=["구매일자", "수량", "종목명"])

        # When
        try:
            UpdateAssetFieldRequest.validate_request_data(valid_request_data)
            validation_passed = True
        except HTTPException:
            validation_passed = False

        # Then
        assert validation_passed is True

    def test_validate_request_data_fail(self):
        # Given
        invalid_request_data = UpdateAssetFieldRequest(root=["invalid_field", "수량"])

        # When
        try:
            UpdateAssetFieldRequest.validate_request_data(invalid_request_data)
            validation_passed = True
        except HTTPException as e:
            validation_passed = False
            error_detail = e.detail

        # Then
        assert validation_passed is False
        assert "'invalid_field'은 올바른 필드가 아닙니다." in error_detail


class TestAssetStockResponse:
    async def test_validate_assets_empty(self, setup_asset):
        # Given
        empty_assets: list[Asset] = []

        # When
        response = AssetStockResponse.validate_assets(empty_assets)

        # Then
        expected_response = AssetStockResponse(
            stock_assets=[],
            asset_fields=[],
            total_asset_amount=0.0,
            total_invest_amount=0.0,
            total_profit_rate=0.0,
            total_profit_amount=0.0,
            total_dividend_amount=0.0,
        )

        assert response == expected_response

    async def test_validate_assets_non_empty(self, session, setup_asset):
        # Given
        non_empty_assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)

        # When
        response = AssetStockResponse.validate_assets(non_empty_assets)

        # Then
        assert response is None

    async def test_parse(self, session: AsyncSession, redis_client: Redis, setup_all):
        # Given
        assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        asset_fields = await AssetFieldService.get_asset_field(session, DUMMY_USER_ID)
        stock_assets: list[dict] = await AssetFacade.get_stock_assets(
            session=session, redis_client=redis_client, assets=assets, asset_fields=asset_fields
        )

        total_asset_amount = await AssetFacade.get_total_asset_amount(session, redis_client, assets)
        total_invest_amount = await AssetFacade.get_total_investment_amount(session, redis_client, assets)
        total_dividend_amount = await DividendFacade.get_total_dividend(session, redis_client, assets)

        # When
        stock_asset_response = AssetStockResponse.parse(
            stock_assets=stock_assets,
            asset_fields=asset_fields,
            total_asset_amount=total_asset_amount,
            total_invest_amount=total_invest_amount,
            total_dividend_amount=total_dividend_amount,
        )

        # Then
        expected_profit_rate = ((total_asset_amount - total_invest_amount) / total_invest_amount) * 100
        assert stock_asset_response.total_profit_rate == pytest.approx(expected_profit_rate)

        expected_profit_amount = total_asset_amount - total_invest_amount
        assert stock_asset_response.total_profit_amount == pytest.approx(expected_profit_amount)

        assert len(stock_asset_response.stock_assets) == len(stock_assets)
