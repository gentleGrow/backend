from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.common.schema.common_schema import DeleteResponse, PutResponse
from app.module.asset.constant import CurrencyType
from app.module.asset.dependencies.asset_dependency import get_asset_service
from app.module.asset.dependencies.asset_field_dependency import get_asset_field_service
from app.module.asset.dependencies.asset_stock_dependency import get_asset_stock_service
from app.module.asset.dependencies.dividend_dependency import get_dividend_service
from app.module.asset.dependencies.stock_dependency import get_stock_service
from app.module.asset.enum import AccountType, AssetType, InvestmentBankType, StockAsset
from app.module.asset.model import Asset, AssetField, Stock
from app.module.asset.redis_repository import RedisExchangeRateRepository
from app.module.asset.repository.asset_field_repository import AssetFieldRepository
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.schema import (
    AggregateStockAsset,
    AssetStockResponse,
    StockAssetSchema,
    StockAssetGroup
)
from app.module.asset.services.asset_field_service import AssetFieldService
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.stock_service import StockService
from app.module.auth.constant import DUMMY_USER_ID
from app.module.auth.schema import AccessToken
from database.dependency import get_mysql_session_router, get_redis_pool

asset_stock_router_v2 = APIRouter(prefix="/v2")


@asset_stock_router_v2.get("/sample/assetstock", summary="임시 자산 정보를 반환합니다.", response_model=AssetStockResponse)
async def get_sample_asset_stock(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    dividend_service: DividendService = Depends(get_dividend_service),
    asset_field_service: AssetFieldService = Depends(get_asset_field_service),
) -> AssetStockResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    asset_fields: list[str] = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)

    no_asset_response = AssetStockResponse.validate_assets(assets, asset_fields)
    if no_asset_response:
        return no_asset_response

    asset_fields = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)
    stock_asset_elements: list[StockAssetSchema] = await asset_service.get_stock_assets(
        session, redis_client, assets, asset_fields
    )
    aggregate_stock_assets: list[AggregateStockAsset] = asset_service.aggregate_stock_assets(stock_asset_elements)

    stock_assets: list[StockAssetGroup] = asset_service.group_stock_assets(stock_asset_elements, aggregate_stock_assets)

    total_asset_amount = await asset_service.get_total_asset_amount(session, redis_client, assets)
    total_invest_amount = await asset_service.get_total_investment_amount(session, redis_client, assets)
    total_dividend_amount = await dividend_service.get_total_dividend(session, redis_client, assets)

    dollar_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.KOREA}_{CurrencyType.USA}")
    won_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.USA}_{CurrencyType.KOREA}")

    return AssetStockResponse.parse(
        stock_assets,
        asset_fields,
        total_asset_amount,
        total_invest_amount,
        total_dividend_amount,
        dollar_exchange if dollar_exchange else 1.0,
        won_exchange if won_exchange else 1.0,
    )


@asset_stock_router_v2.get("/assetstock", summary="사용자의 자산 정보를 반환합니다.", response_model=AssetStockResponse)
async def get_asset_stock(
    token: AccessToken = Depends(verify_jwt_token),
    redis_client: Redis = Depends(get_redis_pool),
    session: AsyncSession = Depends(get_mysql_session_router),
    asset_service: AssetService = Depends(get_asset_service),
    dividend_service: DividendService = Depends(get_dividend_service),
    asset_field_service: AssetFieldService = Depends(get_asset_field_service),
) -> AssetStockResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    asset_fields: list[str] = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)

    no_asset_response = AssetStockResponse.validate_assets(assets, asset_fields)
    if no_asset_response:
        return no_asset_response

    asset_fields = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)
    stock_assets: list[StockAssetSchema] = await asset_service.get_stock_assets(
        session, redis_client, assets, asset_fields
    )
    aggregate_stock_assets: list[AggregateStockAsset] = asset_service.aggregate_stock_assets(stock_assets)

    total_asset_amount = await asset_service.get_total_asset_amount(session, redis_client, assets)
    total_invest_amount = await asset_service.get_total_investment_amount(session, redis_client, assets)
    total_dividend_amount = await dividend_service.get_total_dividend(session, redis_client, assets)

    dollar_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.KOREA}_{CurrencyType.USA}")
    won_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.USA}_{CurrencyType.KOREA}")

    return AssetStockResponse.parse(
        stock_assets,
        aggregate_stock_assets,
        asset_fields,
        total_asset_amount,
        total_invest_amount,
        total_dividend_amount,
        dollar_exchange if dollar_exchange else 1.0,
        won_exchange if won_exchange else 1.0,
    )
