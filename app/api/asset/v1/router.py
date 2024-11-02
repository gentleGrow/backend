from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.common.schema.common_schema import DeleteResponse, PutResponse
from app.common.util.time import check_weekend
from app.module.asset.constant import CurrencyType
from app.module.asset.dependencies.asset_dependency import get_asset_service
from app.module.asset.enum import AccountType, AssetType, InvestmentBankType, StockAsset
from app.module.asset.facades.asset_facade import AssetFacade
from app.module.asset.facades.dividend_facade import DividendFacade
from app.module.asset.model import Asset, AssetField, Stock
from app.module.asset.redis_repository import RedisExchangeRateRepository
from app.module.asset.repository.asset_field_repository import AssetFieldRepository
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.schema import (
    AssetFieldResponse,
    AssetPostResponse,
    AssetPutResponse,
    AssetStockPostRequest,
    AssetStockPutRequest,
    AssetStockResponse,
    BankAccountResponse,
    StockListResponse,
    StockListValue,
    UpdateAssetFieldRequest,
)
from app.module.asset.services.asset_field_service import AssetFieldService
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.stock_service import StockService
from app.module.auth.constant import DUMMY_USER_ID
from app.module.auth.schema import AccessToken
from database.dependency import get_mysql_session_router, get_redis_pool

asset_stock_router = APIRouter(prefix="/v1")


@asset_stock_router.get("/asset-field", summary="자산 필드를 반환합니다.", response_model=AssetFieldResponse)
async def get_asset_field(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
) -> AssetFieldResponse:
    asset_field: list[str] = await AssetFieldService.get_asset_field(session, token.get("user"))
    return AssetFieldResponse(asset_field)


@asset_stock_router.put("/asset-field", summary="자산 필드를 변경합니다.", response_model=PutResponse)
async def update_asset_field(
    request_data: UpdateAssetFieldRequest,
    session: AsyncSession = Depends(get_mysql_session_router),
    token: AccessToken = Depends(verify_jwt_token),
) -> PutResponse:
    UpdateAssetFieldRequest.validate_request_data(request_data)

    asset_field = await AssetFieldRepository.get(session, token.get("user"))
    await AssetFieldRepository.update(
        session, AssetField(id=asset_field.id, user_id=token.get("user"), field_preference=request_data.root)
    )
    return PutResponse(status_code=status.HTTP_200_OK, content="자산관리 필드를 성공적으로 수정 하였습니다.")


@asset_stock_router.get("/bank-accounts", summary="증권사와 계좌 리스트를 반환합니다.", response_model=BankAccountResponse)
async def get_bank_account_list() -> BankAccountResponse:
    investment_bank_list = [bank.value for bank in InvestmentBankType]
    account_list = [account.value for account in AccountType]

    return BankAccountResponse(investment_bank_list=investment_bank_list, account_list=account_list)


@asset_stock_router.get("/stocks", summary="주시 종목 코드를 반환합니다.", response_model=StockListResponse)
async def get_stock_list(session: AsyncSession = Depends(get_mysql_session_router)) -> StockListResponse:
    stock_list: list[Stock] = await StockRepository.get_all(session)

    return StockListResponse(
        [StockListValue(name_en=stock.name_en, name_kr=stock.name_kr, code=stock.code) for stock in stock_list]
    )


@asset_stock_router.get("/sample/assetstock", summary="임시 자산 정보를 반환합니다.", response_model=AssetStockResponse)
async def get_sample_asset_stock(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
) -> AssetStockResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    asset_fields: list[str] = await AssetFieldService.get_asset_field(session, DUMMY_USER_ID)

    no_asset_response = AssetStockResponse.validate_assets(assets, asset_fields)
    if no_asset_response:
        return no_asset_response

    asset_fields = await AssetFieldService.get_asset_field(session, DUMMY_USER_ID)
    stock_assets: list[dict] = await asset_service.get_stock_assets(session, redis_client, assets, asset_fields)

    total_asset_amount = await AssetFacade.get_total_asset_amount(session, redis_client, assets)
    total_invest_amount = await AssetFacade.get_total_investment_amount(session, redis_client, assets)
    total_dividend_amount = await DividendFacade.get_total_dividend(session, redis_client, assets)

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


@asset_stock_router.get("/assetstock", summary="사용자의 자산 정보를 반환합니다.", response_model=AssetStockResponse)
async def get_asset_stock(
    token: AccessToken = Depends(verify_jwt_token),
    redis_client: Redis = Depends(get_redis_pool),
    session: AsyncSession = Depends(get_mysql_session_router),
    asset_service: AssetService = Depends(get_asset_service),
) -> AssetStockResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    asset_fields: list[str] = await AssetFieldService.get_asset_field(session, token.get("user"))

    no_asset_response = AssetStockResponse.validate_assets(assets, asset_fields)
    if no_asset_response:
        return no_asset_response

    stock_assets: list[dict] = await asset_service.get_stock_assets(session, redis_client, assets, asset_fields)

    total_asset_amount = await AssetFacade.get_total_asset_amount(session, redis_client, assets)
    total_invest_amount = await AssetFacade.get_total_investment_amount(session, redis_client, assets)
    total_dividend_amount = await DividendFacade.get_total_dividend(session, redis_client, assets)
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


@asset_stock_router.post("/assetstock", summary="자산관리 정보를 등록합니다.", response_model=AssetPostResponse)
async def create_asset_stock(
    request_data: AssetStockPostRequest,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
) -> AssetPostResponse:
    stock = await StockRepository.get_by_code(session, request_data.stock_code)
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{request_data.stock_code}를 찾지 못 했습니다.",
            field=StockAsset.STOCK_CODE,
        )

    stock_exist = await StockService.check_stock_exist(session, request_data.stock_code, request_data.buy_date)
    if stock_exist is False:
        return AssetPostResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"{request_data.stock_code} 코드의 {request_data.buy_date} 날짜가 존재하지 않습니다.",
            field=StockAsset.BUY_DATE,
        )

    # is_weekend = check_weekend()
    
    # if is_weekend:
    #     return AssetPostResponse(
    #         status_code=status.HTTP_404_NOT_FOUND, content="구매일자 주말은 허용하지 않습니다.", field=StockAsset.BUY_DATE
    #     )

    await AssetStockService.save_asset_stock_by_post(session, request_data, stock.id, token.get("user"))
    return AssetPostResponse(status_code=status.HTTP_201_CREATED, content="주식 자산 성공적으로 등록 했습니다.", field="")


@asset_stock_router.patch("/assetstock", summary="주식 자산을 수정합니다.", response_model=AssetPutResponse)
async def update_asset_stock(
    request_data: AssetStockPutRequest,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
) -> AssetPutResponse:
    asset = await AssetRepository.get_asset_by_id(session, request_data.id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{request_data.id} id에 해당하는 자산을 찾지 못 했습니다.")

    if request_data.stock_code and request_data.buy_date:
        stock_exist = await StockService.check_stock_exist(session, request_data.stock_code, request_data.buy_date)
        if stock_exist is False:
            return AssetPutResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=f"{request_data.stock_code} 코드의 {request_data.buy_date} 날짜가 존재하지 않습니다.",
                field=StockAsset.BUY_DATE,
            )
    # is_weekend = check_weekend()
    # if is_weekend:
    #     return AssetPutResponse(
    #         status_code=status.HTTP_404_NOT_FOUND, content="구매일자 주말은 허용하지 않습니다.", field=StockAsset.BUY_DATE
    #     )

    stock = await StockRepository.get_by_code(session, request_data.stock_code)

    await AssetService.save_asset_by_put(session, request_data, asset, stock)
    return AssetPutResponse(status_code=status.HTTP_200_OK, content="주식 자산을 성공적으로 수정 하였습니다.", field="")


@asset_stock_router.delete("/assetstock/{asset_id}", summary="자산을 삭제합니다.", response_model=DeleteResponse)
async def delete_asset_stock(
    asset_id: int,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
) -> DeleteResponse:
    try:
        await AssetRepository.delete_asset(session, asset_id)
        return DeleteResponse(status_code=status.HTTP_200_OK, content="주식 자산이 성공적으로 삭제 되었습니다.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
