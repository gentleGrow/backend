from datetime import date
from typing import Optional

import numpy
from fastapi import status
from pydantic import BaseModel, Field, RootModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.constant import ASSET_FIELD, PURCHASE_PRICE_MAX, PURCHASE_QUANTITY_MAX, REQUIRED_ASSET_FIELD
from app.module.asset.enum import AccountType, InvestmentBankType, PurchaseCurrencyType, StockAsset, TradeType
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository


class ParentAssetDeleteResponse(BaseModel):
    status_code: int = Field(..., description="상태 코드")
    detail: str

    @staticmethod
    def validate_stock_code(assets: list[Asset], stock_code: str) -> Optional["ParentAssetDeleteResponse"]:
        for asset in assets:
            if stock_code == asset.asset_stock.stock.code:
                return None

        return ParentAssetDeleteResponse(status_code=status.HTTP_404_NOT_FOUND, detail="해당하는 주식 종목을 보유하고 있지 않습니다.")


class StockAssetField(BaseModel):
    isRequired: bool
    value: float | str | date | None


class StockAssetSchema(BaseModel):
    id: int
    거래가: StockAssetField
    거래금: StockAssetField
    거래량: StockAssetField
    계좌종류: StockAssetField
    고가: StockAssetField
    매매일자: StockAssetField
    배당금: StockAssetField
    수량: StockAssetField
    수익금: StockAssetField
    수익률: StockAssetField
    시가: StockAssetField
    저가: StockAssetField
    종목명: StockAssetField
    주식코드: StockAssetField
    주식통화: str | None
    증권사: StockAssetField
    현재가: StockAssetField
    매매: StockAssetField


class AggregateStockAsset(BaseModel):
    종목명: str
    수익률: float
    수익금: float
    배당금: float


class StockAssetGroup(BaseModel):
    parent: AggregateStockAsset
    sub: list[StockAssetSchema]


class AssetStockPostRequest(BaseModel):
    trade_date: date | None = Field(None, description="매매일자")
    purchase_currency_type: PurchaseCurrencyType | None = Field(None, description="매입 통화")
    quantity: int | None = Field(None, description="수량")
    stock_code: str = Field(..., description="종목 코드", examples=["AAPL"])
    account_type: AccountType | None = Field(None, description="계좌 종류", example=f"{AccountType.ISA} (Optional)")
    investment_bank: InvestmentBankType | None = Field(
        None, description="증권사", example=f"{InvestmentBankType.TOSS} (Optional)"
    )
    trade_price: float | None = Field(None, description="거래가", example=f"{62000} (Optional)")
    trade: TradeType | None = Field(None, description="매매", examples=["매수/매도"])

    @classmethod
    async def id_validate(cls, session: AsyncSession, asset_id: int | None) -> Optional["AssetStockStatusResponse"]:
        asset = await AssetRepository.get_asset_by_id(session, asset_id)
        if not asset:
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당하는 asset을 찾지 못 했습니다.",
                field=StockAsset.ID,
            )
        else:
            return None

    @classmethod
    def validate(cls, request_data: "AssetStockPostRequest") -> Optional["AssetStockStatusResponse"]:
        if request_data.quantity and request_data.quantity > PURCHASE_QUANTITY_MAX:
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST, detail="수량은 10,000을 넘길 수 없습니다.", field=StockAsset.QUANTITY
            )
        elif request_data.quantity and request_data.quantity < 0:
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST, detail="수량은 음수일 수 없습니다.", field=StockAsset.QUANTITY
            )
        elif request_data.trade_price and request_data.trade_price > PURCHASE_PRICE_MAX:  # type: ignore # 전방 참조로 추후 type이 체킹됨
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재가가 10,000,000을 넘길 수 없습니다.",
                field=StockAsset.TRADE_PRICE,
            )
        elif request_data.trade_price and request_data.trade_price < 0:  # type: ignore # 전방 참조로 추후 type이 체킹됨
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재가가 음수일 수 없습니다.",
                field=StockAsset.TRADE_PRICE,
            )
        elif all(value is None for value in request_data.model_dump().values()):
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST, detail="최소 1개의 필드값은 있어야 합니다.", field=""
            )
        else:
            return None


class AssetStockPutRequest(BaseModel):
    id: int = Field(..., description="자산 고유 값")
    trade_date: date | None = Field(None, description="매매일자")
    purchase_currency_type: PurchaseCurrencyType | None = Field(None, description="매입 통화")
    quantity: int | None = Field(None, description="수량")
    stock_code: str = Field(..., description="종목 코드", examples=["AAPL"])
    account_type: AccountType | None = Field(None, description="계좌 종류", example=f"{AccountType.ISA} (Optional)")
    investment_bank: InvestmentBankType | None = Field(
        None, description="증권사", example=f"{InvestmentBankType.TOSS} (Optional)"
    )
    trade_price: float | None = Field(None, description="거래가", example=f"{62000} (Optional)")
    trade: TradeType | None = Field(None, description="매매", examples=["매수/매도"])

    @classmethod
    async def id_validate(cls, session: AsyncSession, asset_id: int | None) -> Optional["AssetStockStatusResponse"]:
        asset = await AssetRepository.get_asset_by_id(session, asset_id)
        if not asset:
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당하는 asset을 찾지 못 했습니다.",
                field=StockAsset.ID,
            )
        else:
            return None

    @classmethod
    def validate(cls, request_data: "AssetStockPutRequest") -> Optional["AssetStockStatusResponse"]:
        if request_data.quantity and request_data.quantity > PURCHASE_QUANTITY_MAX:
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST, detail="수량은 10,000을 넘길 수 없습니다.", field=StockAsset.QUANTITY
            )
        elif request_data.quantity and request_data.quantity < 0:
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST, detail="수량은 음수일 수 없습니다.", field=StockAsset.QUANTITY
            )
        elif request_data.trade_price and request_data.trade_price > PURCHASE_PRICE_MAX:  # type: ignore # 전방 참조로 추후 type이 체킹됨
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재가가 10,000,000을 넘길 수 없습니다.",
                field=StockAsset.TRADE_PRICE,
            )
        elif request_data.trade_price and request_data.trade_price < 0:  # type: ignore # 전방 참조로 추후 type이 체킹됨
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재가가 음수일 수 없습니다.",
                field=StockAsset.TRADE_PRICE,
            )
        elif all(value is None for value in request_data.model_dump().values()):
            return AssetStockStatusResponse(
                status_code=status.HTTP_400_BAD_REQUEST, detail="최소 1개의 필드값은 있어야 합니다.", field=""
            )
        else:
            return None


class AssetStockStatusResponse(BaseModel):
    status_code: int = Field(..., description="상태 코드")
    detail: str
    field: str | None


class UpdateAssetFieldRequest(RootModel[list[str]]):
    class Config:
        json_schema_extra = {
            "example": [
                "매매일자",
                "매매",
                "수량",
                "계좌종류",
                "현재가",
                "배당금",
                "고가",
                "증권사",
                "저가",
                "시가",
                "수익률",
                "수익금",
                "거래금",
                "거래가",
                "종목명",
                "거래량",
            ]
        }


class AssetFieldUpdateResponse(BaseModel):
    status_code: int
    detail: str

    @classmethod
    def validate(cls, update_field: list) -> Optional["AssetFieldUpdateResponse"]:
        if len(update_field) == 0:
            return cls(status_code=status.HTTP_404_NOT_FOUND, detail="빈 배열을 받았습니다. 필수 필드가 포함되어 있어야 합니다.")

        all_include = numpy.isin(REQUIRED_ASSET_FIELD, update_field).all()
        proper_fields = numpy.isin(update_field, ASSET_FIELD).all()

        if not all_include:
            return cls(status_code=status.HTTP_404_NOT_FOUND, detail=f"{REQUIRED_ASSET_FIELD}가 모두 포함되어 있어야 합니다.")
        elif not proper_fields:
            return cls(status_code=status.HTTP_404_NOT_FOUND, detail=f"필드: {ASSET_FIELD} 만 허용합니다.")
        elif update_field[:len(REQUIRED_ASSET_FIELD)] != REQUIRED_ASSET_FIELD:
            return cls(status_code=status.HTTP_404_NOT_FOUND, detail=f"필수 필드의 순서는 {REQUIRED_ASSET_FIELD}와 같아야 합니다.")
        else:
            return None


class AssetFieldResponse(RootModel[list[str]]):
    pass


class BankAccountResponse(BaseModel):
    investment_bank_list: list[str]
    account_list: list[str]


class StockListValue(BaseModel):
    name_en: str
    name_kr: str
    code: str


class StockListResponse(RootModel[list[StockListValue]]):
    pass


class AssetStockResponse(BaseModel):
    stock_assets: list[StockAssetGroup]
    asset_fields: list
    total_asset_amount: float
    total_invest_amount: float
    total_profit_rate: float
    total_profit_amount: float
    total_dividend_amount: float
    dollar_exchange: float
    won_exchange: float

    @classmethod
    def parse(
        cls,
        stock_assets: list[StockAssetGroup],
        asset_fields: list,
        total_asset_amount: float,
        total_invest_amount: float,
        total_dividend_amount: float,
        dollar_exchange: float,
        won_exchange: float,
    ) -> "AssetStockResponse":
        return cls(
            stock_assets=stock_assets,
            asset_fields=asset_fields,
            total_asset_amount=total_asset_amount,
            total_invest_amount=total_invest_amount,
            total_profit_rate=((total_asset_amount - total_invest_amount) / total_invest_amount) * 100
            if total_invest_amount > 0
            else 0.0,
            total_profit_amount=total_asset_amount - total_invest_amount,
            total_dividend_amount=total_dividend_amount,
            dollar_exchange=dollar_exchange if dollar_exchange else 1.0,
            won_exchange=won_exchange if won_exchange else 1.0,
        )

    @staticmethod
    def validate_assets(assets: list[Asset], asset_fields: list[str]) -> Optional["AssetStockResponse"]:
        if len(assets) == 0:
            return AssetStockResponse(
                stock_assets=[],
                asset_fields=asset_fields,
                total_asset_amount=0.0,
                total_invest_amount=0.0,
                total_profit_rate=0.0,
                total_profit_amount=0.0,
                total_dividend_amount=0.0,
                dollar_exchange=0.0,
                won_exchange=0.0,
            )
        return None


class StockInfo(BaseModel):
    code: str = Field(..., description="종목 코드", examples="095570")
    name_kr: str = Field(..., description="종목명", examples="BGF리테일")
    name_en: str = Field(..., description="종목명", examples="Apple")
    country: str = Field(..., description="나라명", examples="Korea")
    market_index: str = Field(..., description="주가 지수", examples="KOSPI")


class MarketIndexData(BaseModel):
    country: str = Field(..., description="지수 국가")
    name: str = Field(..., description="지수명")
    current_value: str | float = Field(..., description="현재 지수")
    change_value: str | float = Field(..., description="이전 지수 대비 변동 값")
    change_percent: str | float = Field(..., description="이전 지수 대비 변동률")
    update_time: str = Field(..., description="최근 업데이트 시간")


class TodayTempStockDaily(BaseModel):
    adj_close_price: float
    highest_price: float
    lowest_price: float
    opening_price: float
    trade_volume: int
