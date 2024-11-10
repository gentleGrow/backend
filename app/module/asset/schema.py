from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, RootModel

from app.module.asset.enum import AccountType, InvestmentBankType, PurchaseCurrencyType
from app.module.asset.model import Asset


class StockAssetField(BaseModel):
    isRequired: bool
    value: float | str | date | None


class StockAssetSchema(BaseModel):
    id: int
    계좌종류: StockAssetField
    매매일자: StockAssetField
    현재가: StockAssetField
    배당금: StockAssetField
    고가: StockAssetField
    증권사: StockAssetField
    저가: StockAssetField
    시가: StockAssetField
    수익률: StockAssetField
    수익금: StockAssetField
    거래금: StockAssetField
    거래가: StockAssetField
    수량: StockAssetField
    종목명: StockAssetField
    거래량: StockAssetField
    주식통화: str


class AggregateStockAsset(BaseModel):
    종목명: str
    수익률: float
    수익금: float
    배당금: float


class StockAssetGroup(BaseModel):
    parent: AggregateStockAsset
    sub: list[StockAssetSchema]


class AssetPostResponse(BaseModel):
    status_code: int = Field(..., description="상태 코드")
    content: str
    field: str


class AssetPutResponse(BaseModel):
    status_code: int = Field(..., description="상태 코드")
    content: str
    field: str

# 확인 후 수정하겠습니다.
class AssetStockPostRequest_v1(BaseModel):
    buy_date: date = Field(..., description="구매일자")
    purchase_currency_type: PurchaseCurrencyType = Field(..., description="매입 통화")
    quantity: int = Field(..., description="수량")
    stock_code: str = Field(..., description="종목 코드", examples=["AAPL"])
    account_type: AccountType | None = Field(None, description="계좌 종류", example=f"{AccountType.ISA} (Optional)")
    investment_bank: InvestmentBankType | None = Field(
        None, description="증권사", example=f"{InvestmentBankType.TOSS} (Optional)"
    )
    purchase_price: float | None = Field(None, description="매입가", example=f"{62000} (Optional)")
    trade: str = Field(..., description="매매", examples=["매수/매도"])
####################


class AssetStockPostRequest(BaseModel):
    purchase_date: date = Field(..., description="매매일자")
    purchase_currency_type: PurchaseCurrencyType = Field(..., description="매입 통화")
    quantity: int = Field(..., description="수량")
    stock_code: str = Field(..., description="종목 코드", examples=["AAPL"])
    account_type: AccountType | None = Field(None, description="계좌 종류", example=f"{AccountType.ISA} (Optional)")
    investment_bank: InvestmentBankType | None = Field(
        None, description="증권사", example=f"{InvestmentBankType.TOSS} (Optional)"
    )
    trade_price: float | None = Field(None, description="거래가", example=f"{62000} (Optional)")
    trade: str = Field(..., description="매매", examples=["매수/매도"])


class UpdateAssetFieldRequest(RootModel[list[str]]):
    class Config:
        json_schema_extra = {
            "example": [
                "구매일자",
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
                "매입금",
                "매입가",
                "종목명",
                "거래량",
            ]
        }

# 확인 후 수정하겠습니다.
class AssetStockPutRequest_v1(BaseModel):
    id: int = Field(..., description="자산 고유 값")
    buy_date: date | None = Field(None, description="구매일자", example="2024-08-12 (Optional)")
    purchase_currency_type: PurchaseCurrencyType | None = Field(None, description="매입 통화", example="KRW/USD (Optional)")
    quantity: int | None = Field(None, description="수량", example="1 (Optional)")
    stock_code: str | None = Field(None, description="종목 코드", example="AAPL (Optional)")
    account_type: AccountType | None = Field(None, description="계좌 종류", example=f"{AccountType.ISA} (Optional)")
    investment_bank: str | None = Field(None, description="증권사", example=f"{InvestmentBankType.TOSS} (Optional)")
    purchase_price: float | None = Field(None, description="매입가", example=f"{62000} (Optional)")
################3


class AssetStockPutRequest(BaseModel):
    id: int = Field(..., description="자산 고유 값")
    purchase_date: date | None = Field(None, description="매매일자", example="2024-08-12 (Optional)")
    purchase_currency_type: PurchaseCurrencyType | None = Field(None, description="매입 통화", example="KRW/USD (Optional)")
    quantity: int | None = Field(None, description="수량", example="1 (Optional)")
    stock_code: str | None = Field(None, description="종목 코드", example="AAPL (Optional)")
    account_type: AccountType | None = Field(None, description="계좌 종류", example=f"{AccountType.ISA} (Optional)")
    investment_bank: str | None = Field(None, description="증권사", example=f"{InvestmentBankType.TOSS} (Optional)")
    trade_price: float | None = Field(None, description="거래가", example=f"{62000} (Optional)")
    trade: str = Field(..., description="매매", examples=["매수/매도"])


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


#### 임시 스키마로, 확인 후 삭제하겠습니다. ####
class AssetStockResponse_v1(BaseModel):
    stock_assets: list[dict]
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
        stock_assets: list[dict],
        asset_fields: list,
        total_asset_amount: float,
        total_invest_amount: float,
        total_dividend_amount: float,
        dollar_exchange: float,
        won_exchange: float,
    ) -> "AssetStockResponse_v1":
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
    def validate_assets(assets: list[Asset], asset_fields: list[str]) -> Optional["AssetStockResponse_v1"]:
        if len(assets) == 0:
            return AssetStockResponse_v1(
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


############################################


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
    country: str = Field(..., description="Country of the market index")
    name: str = Field(..., description="Name of the market index")
    current_value: str = Field(..., description="Current value of the index")
    change_value: str = Field(..., description="The change in value from the previous close")
    change_percent: str = Field(..., description="The percentage change from the previous close")
    update_time: str = Field(..., description="The time at which the data was last updated")


class TodayTempStockDaily(BaseModel):
    adj_close_price: float
    highest_price: float
    lowest_price: float
    opening_price: float
    trade_volume: int
