from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.common.schema.common_schema import DeleteResponse, PutResponse
from app.module.asset.constant import KOREA, USA, CurrencyType
from app.module.asset.dependencies.asset_dependency import get_asset_service
from app.module.asset.dependencies.asset_field_dependency import get_asset_field_service
from app.module.asset.dependencies.asset_stock_dependency import get_asset_stock_service
from app.module.asset.dependencies.dividend_dependency import get_dividend_service
from app.module.asset.dependencies.stock_dependency import get_stock_service
from app.module.asset.enum import AccountType, AssetType, InvestmentBankType, StockAsset_v1
from app.module.asset.model import Asset, AssetField, Stock
from app.module.asset.redis_repository import RedisExchangeRateRepository
from app.module.asset.repository.asset_field_repository import AssetFieldRepository
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.schema import (
    AssetFieldResponse,
    AssetPostResponse,
    AssetPutResponse,
    AssetStockPostRequest_v1,
    AssetStockPutRequest_v1,
    AssetStockResponse_v1,
    BankAccountResponse,
    ParentAssetDeleteResponse,
    StockListResponse,
    StockListValue,
    UpdateAssetFieldRequest,
)
from app.module.asset.services.asset_field_service import AssetFieldService
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.stock_service import StockService
from app.module.auth.constant import DUMMY_USER_ID
from app.module.auth.schema import AccessToken
from database.dependency import get_mysql_session_router, get_redis_pool

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
) -> PutResponse:
    asset_field = await AssetFieldRepository.get(session, token.get("user"))
    await AssetFieldRepository.update(
        session, AssetField(id=asset_field.id, user_id=token.get("user"), field_preference=request_data.root)
    )
    return PutResponse(status_code=status.HTTP_200_OK, detail="자산관리 필드를 성공적으로 수정 하였습니다.")


@asset_stock_router.get("/bank-accounts", summary="증권사와 계좌 리스트를 반환합니다.", response_model=BankAccountResponse)
async def get_bank_account_list() -> BankAccountResponse:
    investment_bank_list = [bank.value for bank in InvestmentBankType]
    account_list = [account.value for account in AccountType]

    return BankAccountResponse(investment_bank_list=investment_bank_list, account_list=account_list)


@asset_stock_router.get("/stocks", summary="주시 종목 코드를 반환합니다.", response_model=StockListResponse)
async def get_stock_list(session: AsyncSession = Depends(get_mysql_session_router)) -> StockListResponse:
    stock_list: list[Stock] = await StockRepository.get_countries_stock(session, [KOREA, USA])

    return StockListResponse(
        [StockListValue(name_en=stock.name_en, name_kr=stock.name_kr, code=stock.code) for stock in stock_list]
    )


@asset_stock_router.get("/sample/assetstock", summary="임시 자산 정보를 반환합니다.", response_model=AssetStockResponse_v1)
async def get_sample_asset_stock(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    dividend_service: DividendService = Depends(get_dividend_service),
    asset_field_service: AssetFieldService = Depends(get_asset_field_service),
) -> AssetStockResponse_v1:
    assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    asset_fields: list[str] = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)

    no_asset_response = AssetStockResponse_v1.validate_assets(assets, asset_fields)
    if no_asset_response:
        return no_asset_response

    asset_fields = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)
    stock_assets: list[dict] = await asset_service.get_stock_assets_v1(session, redis_client, assets, asset_fields)

    total_asset_amount = await asset_service.get_total_asset_amount(session, redis_client, assets)
    total_invest_amount = await asset_service.get_total_investment_amount(session, redis_client, assets)
    total_dividend_amount = await dividend_service.get_total_dividend(session, redis_client, assets)

    dollar_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.KOREA}_{CurrencyType.USA}")
    won_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.USA}_{CurrencyType.KOREA}")

    return AssetStockResponse_v1.parse(
        stock_assets,
        asset_fields,
        total_asset_amount,
        total_invest_amount,
        total_dividend_amount,
        dollar_exchange if dollar_exchange else 1.0,
        won_exchange if won_exchange else 1.0,
    )


@asset_stock_router.get("/assetstock", summary="사용자의 자산 정보를 반환합니다.", response_model=AssetStockResponse_v1)
async def get_asset_stock(
    token: AccessToken = Depends(verify_jwt_token),
    redis_client: Redis = Depends(get_redis_pool),
    session: AsyncSession = Depends(get_mysql_session_router),
    asset_service: AssetService = Depends(get_asset_service),
    dividend_service: DividendService = Depends(get_dividend_service),
    asset_field_service: AssetFieldService = Depends(get_asset_field_service),
) -> AssetStockResponse_v1:
    assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    asset_fields: list[str] = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)

    no_asset_response = AssetStockResponse_v1.validate_assets(assets, asset_fields)
    if no_asset_response:
        return no_asset_response

    asset_fields = await asset_field_service.get_asset_field(session, DUMMY_USER_ID)
    stock_assets: list[dict] = await asset_service.get_stock_assets_v1(session, redis_client, assets, asset_fields)

    total_asset_amount = await asset_service.get_total_asset_amount(session, redis_client, assets)
    total_invest_amount = await asset_service.get_total_investment_amount(session, redis_client, assets)
    total_dividend_amount = await dividend_service.get_total_dividend(session, redis_client, assets)

    dollar_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.KOREA}_{CurrencyType.USA}")
    won_exchange = await RedisExchangeRateRepository.get(redis_client, f"{CurrencyType.USA}_{CurrencyType.KOREA}")

    return AssetStockResponse_v1.parse(
        stock_assets,
        asset_fields,
        total_asset_amount,
        total_invest_amount,
        total_dividend_amount,
        dollar_exchange if dollar_exchange else 1.0,
        won_exchange if won_exchange else 1.0,
    )


@asset_stock_router.post("/assetstock", summary="자산관리 정보를 등록합니다.", response_model=AssetPostResponse)
async def create_asset_stock(
    request_data: AssetStockPostRequest_v1,
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
            field=StockAsset_v1.STOCK_CODE,
        )

    stock_exist = await stock_service.check_stock_exist(session, request_data.stock_code, request_data.buy_date)
    if stock_exist is False:
        return AssetPostResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{request_data.stock_code} 코드의 {request_data.buy_date} 날짜가 존재하지 않습니다.",
            field=StockAsset_v1.BUY_DATE,
        )

    await asset_stock_service.save_asset_stock_by_post_v1(session, request_data, stock.id, token.get("user"))
    return AssetPostResponse(status_code=status.HTTP_201_CREATED, detail="주식 자산 성공적으로 등록 했습니다.", field="")


@asset_stock_router.patch("/assetstock", summary="주식 자산을 수정합니다.", response_model=AssetPutResponse)
async def update_asset_stock(
    request_data: AssetStockPutRequest_v1,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    stock_service: StockService = Depends(get_stock_service),
    asset_service: AssetService = Depends(get_asset_service),
) -> AssetPutResponse:
    asset = await AssetRepository.get_asset_by_id(session, request_data.id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{request_data.id} id에 해당하는 자산을 찾지 못 했습니다.")

    if request_data.stock_code and request_data.buy_date:
        stock_exist = await stock_service.check_stock_exist(session, request_data.stock_code, request_data.buy_date)
        if stock_exist is False:
            return AssetPutResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{request_data.stock_code} 코드의 {request_data.buy_date} 날짜가 존재하지 않습니다.",
                field=StockAsset_v1.BUY_DATE,
            )

    stock = await StockRepository.get_by_code(session, request_data.stock_code)

    await asset_service.save_asset_by_put_v1(session, request_data, asset, stock)
    return AssetPutResponse(status_code=status.HTTP_200_OK, detail="주식 자산을 성공적으로 수정 하였습니다.", field="")


@asset_stock_router.delete("/{asset_id}", summary="자산을 삭제합니다.", response_model=DeleteResponse)
async def delete_asset(
    asset_id: int,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
) -> DeleteResponse:
    try:
        await AssetRepository.delete_asset(session, asset_id)
        return DeleteResponse(status_code=status.HTTP_200_OK, detail="주식 자산이 성공적으로 삭제 되었습니다.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@asset_stock_router.delete("/assetstock/{stock_code}", summary="주식 부모 행을 삭제합니다.", response_model=DeleteResponse)
async def delete_asset_stock(
    stock_code: str,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    asset_service: AssetService = Depends(get_asset_service),
) -> DeleteResponse:
    try:
        assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
        no_matching_response = ParentAssetDeleteResponse.validate_stock_code(assets, stock_code)
        if no_matching_response:
            return no_matching_response

        await asset_service.delete_parent_row(session, assets, stock_code)

        return DeleteResponse(status_code=status.HTTP_200_OK, detail="부모행을 성공적으로 삭제 하였습니다.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
