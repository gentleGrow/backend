from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.module.asset.constant import CurrencyType
from app.module.asset.dependencies.asset_dependency import get_asset_service
from app.module.asset.dependencies.asset_field_dependency import get_asset_field_service
from app.module.asset.dependencies.asset_stock_dependency import get_asset_stock_service
from app.module.asset.dependencies.dividend_dependency import get_dividend_service
from app.module.asset.dependencies.stock_dependency import get_stock_service
from app.module.asset.enum import AssetType, StockAsset, TradeType
from app.module.asset.model import Asset
from app.module.asset.redis_repository import RedisExchangeRateRepository
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.schema import (
    AggregateStockAsset,
    AssetPostResponse,
    AssetPutResponse,
    AssetStockPostRequest,
    AssetStockPutRequest,
    AssetStockResponse,
    StockAssetGroup,
    StockAssetSchema,
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


@asset_stock_router_v2.patch("/assetstock", summary="주식 자산을 수정합니다.", response_model=AssetPutResponse)
async def update_asset_stock(
    request_data: AssetStockPutRequest,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    stock_service: StockService = Depends(get_stock_service),
    asset_service: AssetService = Depends(get_asset_service),
) -> AssetPutResponse:
    asset = await AssetRepository.get_asset_by_id(session, request_data.id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{request_data.id} id에 해당하는 자산을 찾지 못 했습니다.")

    if request_data.stock_code and request_data.trade_date:
        stock_exist = await stock_service.check_stock_exist(session, request_data.stock_code, request_data.trade_date)
        if stock_exist is False:
            return AssetPutResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{request_data.stock_code} 코드의 {request_data.trade_date} 날짜가 존재하지 않습니다.",
                field=StockAsset.TRADE_DATE,
            )

    if request_data.trade not in TradeType:
        return AssetPutResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{request_data.trade}는 매수와 매도만 가능합니다",
            field=StockAsset.TRADE,
        )

    stock = await StockRepository.get_by_code(session, request_data.stock_code)

    await asset_service.save_asset_by_put(session, request_data, asset, stock)
    return AssetPutResponse(status_code=status.HTTP_200_OK, detail="주식 자산을 성공적으로 수정 하였습니다.", field="")


@asset_stock_router_v2.post("/assetstock", summary="자산관리 정보를 등록합니다.", response_model=AssetPostResponse)
async def create_asset_stock(
    request_data: AssetStockPostRequest,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    stock_service: StockService = Depends(get_stock_service),
    asset_stock_service: AssetStockService = Depends(get_asset_stock_service),
) -> AssetPostResponse:
    stock = await StockRepository.get_by_code(session, request_data.stock_code)
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{request_data.stock_code}를 찾지 못 했습니다.",
            field=StockAsset.STOCK_CODE,
        )

    if request_data.stock_code and request_data.trade_date:
        stock_exist = await stock_service.check_stock_exist(session, request_data.stock_code, request_data.trade_date)
        if stock_exist is False:
            return AssetPostResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{request_data.stock_code} 코드의 {request_data.trade_date} 날짜가 존재하지 않습니다.",
                field=StockAsset.TRADE_DATE,
            )

    if request_data.trade not in TradeType:
        return AssetPostResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{request_data.trade}는 매수와 매도만 가능합니다",
            field=StockAsset.TRADE,
        )

    await asset_stock_service.save_asset_stock_by_post(session, request_data, stock.id, token.get("user"))
    return AssetPostResponse(status_code=status.HTTP_201_CREATED, detail="주식을 성공적으로 등록 했습니다.", field="")


@asset_stock_router_v2.get("/sample/assetstock", summary="임시 자산 정보를 반환합니다.", response_model=AssetStockResponse)
async def get_sample_asset_stock(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    dividend_service: DividendService = Depends(get_dividend_service),
    asset_field_service: AssetFieldService = Depends(get_asset_field_service),
) -> AssetStockResponse:
    original_assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    asset_fields: list[str] = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)

    assets = asset_service.filter_undone_asset(original_assets)

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
    original_assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    asset_fields: list[str] = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)

    assets = asset_service.filter_undone_asset(original_assets)

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
