from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.common.schema.common_schema import DeleteResponse, PutResponse
from app.module.asset.constant import KOREA, USA, CurrencyType
from app.module.asset.dependencies.asset_dependency import get_asset_query, get_asset_service, get_asset_validate
from app.module.asset.dependencies.asset_field_dependency import get_asset_field_service
from app.module.asset.dependencies.asset_stock_dependency import get_asset_stock_service
from app.module.asset.dependencies.common_dependency import get_asset_common_validate
from app.module.asset.dependencies.dividend_dependency import get_dividend_service
from app.module.asset.enum import AccountType, AssetType, InvestmentBankType, TradeType
from app.module.asset.model import Asset, AssetField, Stock
from app.module.asset.redis_repository import RedisExchangeRateRepository
from app.module.asset.repository.asset_field_repository import AssetFieldRepository
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.schema import (
    AggregateStockAsset,
    AssetFieldResponse,
    AssetFieldUpdateResponse,
    AssetStockPostRequest,
    AssetStockPutRequest,
    AssetStockResponse,
    AssetStockStatusResponse,
    BankAccountResponse,
    ParentAssetDeleteResponse,
    StockAssetGroup,
    StockAssetSchema,
    StockListResponse,
    StockListValue,
    UpdateAssetFieldRequest,
)
from app.module.asset.services.asset.asset_query import AssetQuery
from app.module.asset.services.asset.asset_service import AssetService
from app.module.asset.services.asset.asset_validate import AssetValidate
from app.module.asset.services.asset_field_service import AssetFieldService
from app.module.asset.services.asset_stock.asset_stock_service import AssetStockService
from app.module.asset.services.common.common_validate import AssetCommonValidate
from app.module.asset.services.dividend_service import DividendService
from app.module.auth.constant import DUMMY_USER_ID
from app.module.auth.schema import AccessToken
from database.dependency import get_mysql_session_router, get_redis_pool
from icecream import ic

asset_stock_router = APIRouter(prefix="/v1")


@asset_stock_router.get("/asset-field", summary="자산 필드를 반환합니다.", response_model=AssetFieldResponse)
async def get_asset_field(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    asset_field_service: AssetFieldService = Depends(get_asset_field_service),
) -> AssetFieldResponse:
    asset_field: list[str] = await asset_field_service.get_asset_field(session, token.get("user"))
    return AssetFieldResponse(asset_field)


@asset_stock_router.put("/asset-field", summary="자산 필드를 변경합니다.", response_model=PutResponse)
async def update_asset_field(
    request_data: UpdateAssetFieldRequest,
    session: AsyncSession = Depends(get_mysql_session_router),
    token: AccessToken = Depends(verify_jwt_token),
) -> AssetFieldUpdateResponse:
    request_validate = AssetFieldUpdateResponse.validate(request_data.root)
    if request_validate:
        return request_validate

    asset_field = await AssetFieldRepository.get(session, token.get("user"))
    await AssetFieldRepository.update(
        session, AssetField(id=asset_field.id, user_id=token.get("user"), field_preference=request_data.root)
    )

    return AssetFieldUpdateResponse(status_code=status.HTTP_200_OK, detail="자산관리 필드를 성공적으로 수정 하였습니다.")


@asset_stock_router.get("/bank-accounts", summary="증권사와 계좌 리스트를 반환합니다.", response_model=BankAccountResponse)
async def get_bank_account_list() -> BankAccountResponse:
    investment_bank_list = [bank.value for bank in InvestmentBankType]
    account_list = [account.value for account in AccountType]

    return BankAccountResponse(investment_bank_list=investment_bank_list, account_list=account_list)


@asset_stock_router.get("/stocks", summary="주시 종목 코드를 반환합니다.", response_model=StockListResponse)
async def get_stock_list(session: AsyncSession = Depends(get_mysql_session_router)) -> StockListResponse:
    # [INFO] 현재는 국내/미국 주식만 반환하고 추후 서비스 안정화가 되면 전세계 주식을 반환합니다.
    stock_list: list[Stock] = await StockRepository.get_countries_stock(session, [KOREA, USA])

    return StockListResponse(
        [StockListValue(name_en=stock.name_en, name_kr=stock.name_kr, code=stock.code) for stock in stock_list]
    )


@asset_stock_router.post("/assetstock", summary="자산관리 정보를 등록합니다.", response_model=AssetStockStatusResponse)
async def create_asset_stock(
    request_data: AssetStockPostRequest,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_common_validate: AssetCommonValidate = Depends(get_asset_common_validate),
    asset_stock_service: AssetStockService = Depends(get_asset_stock_service),
    asset_query: AssetQuery = Depends(get_asset_query),
) -> AssetStockStatusResponse:
    abnormal_data_response = AssetStockPostRequest.validate(request_data)
    if abnormal_data_response:
        return abnormal_data_response

    validate_response = await asset_common_validate.check_asset_stock_request(session, request_data)
    if validate_response:
        return validate_response

    await asset_stock_service.save_asset_stock_by_post(session, request_data, token.get("user"))
    await asset_query.cache_user_data(session, redis_client, token.get("user"))
    return AssetStockStatusResponse(status_code=status.HTTP_201_CREATED, detail="주식 자산 성공적으로 등록 했습니다.", field="")


@asset_stock_router.put("/assetstock", summary="주식 자산을 수정합니다.", response_model=AssetStockStatusResponse)
async def update_asset_stock(
    request_data: AssetStockPutRequest,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_common_validate: AssetCommonValidate = Depends(get_asset_common_validate),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
) -> AssetStockStatusResponse:
    asset_validate_response = await AssetStockPutRequest.id_validate(session, request_data.id)
    if asset_validate_response:
        return asset_validate_response

    validate_response = await asset_common_validate.check_asset_stock_request(session, request_data)
    if validate_response:
        return validate_response

    await asset_service.save_asset_by_put(session, request_data)

    await asset_query.cache_user_data(session, redis_client, token.get("user"))
    return AssetStockStatusResponse(status_code=status.HTTP_200_OK, detail="주식 자산을 성공적으로 수정 하였습니다.", field="")


@asset_stock_router.delete("/assetstock/{asset_id}", summary="자산을 삭제합니다.", response_model=DeleteResponse)
async def delete_asset(
    asset_id: int,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_validate: AssetValidate = Depends(get_asset_validate),
    asset_query: AssetQuery = Depends(get_asset_query),
) -> DeleteResponse:
    user_asset_exist = await asset_validate.check_asset_exist(session, asset_id, token.get("user"))
    if not user_asset_exist:
        return DeleteResponse(status_code=status.HTTP_404_NOT_FOUND, detail="해당하는 asset id가 유저에게 존재하지 않습니다.")
    await AssetRepository.delete_asset(session, asset_id)
    await asset_query.cache_user_data(session, redis_client, token.get("user"))
    return DeleteResponse(status_code=status.HTTP_200_OK, detail="주식 자산이 성공적으로 삭제 되었습니다.")


@asset_stock_router.delete("/assetstock/stock/{stock_code}", summary="주식 부모 행을 삭제합니다.", response_model=DeleteResponse)
async def delete_asset_stock(
    stock_code: str,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
) -> DeleteResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    no_matching_response = ParentAssetDeleteResponse.validate_stock_code(assets, stock_code)
    if no_matching_response:
        return no_matching_response

    await asset_service.delete_parent_row(session, assets, stock_code)
    await asset_query.cache_user_data(session, redis_client, token.get("user"))
    return DeleteResponse(status_code=status.HTTP_200_OK, detail="부모행을 성공적으로 삭제 하였습니다.")


@asset_stock_router.get("/sample/assetstock", summary="임시 자산 정보를 반환합니다.", response_model=AssetStockResponse)
async def get_sample_asset_stock(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    dividend_service: DividendService = Depends(get_dividend_service),
    asset_field_service: AssetFieldService = Depends(get_asset_field_service),
) -> AssetStockResponse:
    assets = await asset_query.get_full_required_assets(session, DUMMY_USER_ID, AssetType.STOCK)
    asset_fields: list[str] = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)
    no_asset_response = AssetStockResponse.validate_assets(assets, asset_fields)
    if no_asset_response:
        return no_asset_response

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, DUMMY_USER_ID)

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    buy_stock_assets = [
        buy_asset for buy_asset in filter(lambda asset: asset.asset_stock.trade == TradeType.BUY, complete_asset)
    ]

    incomplete_stock_asset_elements = asset_service.get_incomplete_stock_assets(incomplete_assets)
    complete_stock_asset_elements: list[StockAssetSchema] = asset_service.get_stock_assets(
        complete_asset,
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    )
    full_stock_asset_elements = incomplete_stock_asset_elements + complete_stock_asset_elements

    buy_stock_assets_elements = [
        buy_asset for buy_asset in filter(lambda asset: asset.매매 == TradeType.BUY, complete_stock_asset_elements)
    ]
    aggregate_stock_assets: list[AggregateStockAsset] = asset_service.aggregate_stock_assets(buy_stock_assets_elements)
    stock_assets: list[StockAssetGroup] = asset_service.group_stock_assets(
        full_stock_asset_elements, aggregate_stock_assets
    )

    total_asset_amount = asset_service.get_total_asset_amount(
        buy_stock_assets, current_stock_price_map, exchange_rate_map
    )
    total_invest_amount = asset_service.get_total_investment_amount(
        buy_stock_assets, stock_daily_map, exchange_rate_map
    )
    total_dividend_amount = dividend_service.get_total_dividend(buy_stock_assets, exchange_rate_map, dividend_map)

    dollar_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.KOREA}_{CurrencyType.USA}")
    won_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.USA}_{CurrencyType.KOREA}")

    return AssetStockResponse.parse(
        stock_assets,
        asset_fields,
        total_asset_amount,
        total_invest_amount,
        total_dividend_amount,
        dollar_exchange=dollar_exchange or 0.00072,
        won_exchange=won_exchange or 1400.0,
    )


@asset_stock_router.get("/assetstock", summary="사용자의 자산 정보를 반환합니다.", response_model=AssetStockResponse)
async def get_asset_stock(
    token: AccessToken = Depends(verify_jwt_token),
    redis_client: Redis = Depends(get_redis_pool),
    session: AsyncSession = Depends(get_mysql_session_router),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    dividend_service: DividendService = Depends(get_dividend_service),
    asset_field_service: AssetFieldService = Depends(get_asset_field_service),
) -> AssetStockResponse:
    assets: list = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    asset_fields: list[str] = await asset_field_service.get_asset_field(session, token.get("user"))
    no_asset_response = AssetStockResponse.validate_assets(assets, asset_fields)
    if no_asset_response:
        return no_asset_response

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, token.get("user"))

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)

    buy_stock_assets = [
        buy_asset for buy_asset in filter(lambda asset: asset.asset_stock.trade == TradeType.BUY, complete_asset)
    ]

    incomplete_stock_asset_elements = asset_service.get_incomplete_stock_assets(incomplete_assets)
    complete_stock_asset_elements: list[StockAssetSchema] = asset_service.get_stock_assets(
        complete_asset,
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    )
    full_stock_asset_elements = incomplete_stock_asset_elements + complete_stock_asset_elements

    buy_stock_assets_elements = [
        buy_asset for buy_asset in filter(lambda asset: asset.매매 == TradeType.BUY, complete_stock_asset_elements)
    ]
    aggregate_stock_assets: list[AggregateStockAsset] = asset_service.aggregate_stock_assets(buy_stock_assets_elements)
    stock_assets: list[StockAssetGroup] = asset_service.group_stock_assets(
        full_stock_asset_elements, aggregate_stock_assets
    )

    total_asset_amount = asset_service.get_total_asset_amount(
        buy_stock_assets, current_stock_price_map, exchange_rate_map
    )
    total_invest_amount = asset_service.get_total_investment_amount(
        buy_stock_assets, stock_daily_map, exchange_rate_map
    )
    total_dividend_amount = dividend_service.get_total_dividend(buy_stock_assets, exchange_rate_map, dividend_map)

    dollar_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.KOREA}_{CurrencyType.USA}")
    won_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.USA}_{CurrencyType.KOREA}")

    return AssetStockResponse.parse(
        stock_assets,
        asset_fields,
        total_asset_amount,
        total_invest_amount,
        total_dividend_amount,
        dollar_exchange=dollar_exchange or 0.00072,
        won_exchange=won_exchange or 1400.0,
    )
