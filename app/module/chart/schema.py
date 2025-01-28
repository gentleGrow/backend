from datetime import date, datetime, timedelta
from statistics import mean
from typing import Optional, Union

from pydantic import BaseModel, Field, RootModel

from app.common.util.time import get_now_date, get_now_datetime
from app.module.asset.constant import (
    ASSET_SAVE_TREND_YEAR,
    INFLATION_RATE,
    MARKET_INDEX_KR_MAPPING,
    THREE_MONTH_DAY,
    만,
    억,
)
from app.module.asset.enum import ASSETNAME, AmountUnit, MarketIndex
from app.module.asset.model import Asset
from app.module.chart.enum import IntervalType


class AssetSaveTrendResponse(BaseModel):
    xAxises: list[str]
    dates: list[str]
    values1: dict[str, Union[list[float], str]]
    values2: dict[str, Union[list[float], str]]
    unit: str

    @classmethod
    async def validate(cls, assets: list[Asset], total_asset_amount: float) -> Optional["AssetSaveTrendResponse"]:
        if not len(assets):
            return AssetSaveTrendResponse(xAxises=[], dates=[], values1={}, values2={}, unit="")

        near_assets = cls._filter_near_asset(assets)

        if not len(near_assets):
            return cls.no_near_invest_response(total_asset_amount)
        else:
            return None

    @classmethod
    def _filter_near_asset(cls, assets: list[Asset]) -> list[Asset]:
        return [
            asset
            for asset in assets
            if asset.asset_stock.trade_date > (get_now_date() - timedelta(days=THREE_MONTH_DAY))
        ]

    @classmethod
    def no_near_invest_response(cls, total_asset_amount_all: float) -> "AssetSaveTrendResponse":
        if total_asset_amount_all >= 억:
            values1 = {
                "values": [total_asset_amount_all / 억] * ASSET_SAVE_TREND_YEAR,
                "name": ASSETNAME.ESTIMATE_ASSET,
            }
            values2 = {
                "values": [
                    (total_asset_amount_all * ((1 - INFLATION_RATE * 0.01) ** i)) / 억
                    for i in range(ASSET_SAVE_TREND_YEAR)
                ],
                "name": ASSETNAME.REAL_ASSET,
            }
            unit = AmountUnit.BILLION_WON
        else:
            values1 = {"values": [total_asset_amount_all / 만] * ASSET_SAVE_TREND_YEAR, "name": ASSETNAME.ESTIMATE_ASSET}
            values2 = {
                "values": [
                    (total_asset_amount_all * ((1 - INFLATION_RATE * 0.01) ** i)) / 만
                    for i in range(ASSET_SAVE_TREND_YEAR)
                ],
                "name": ASSETNAME.REAL_ASSET,
            }
            unit = AmountUnit.MILLION_WON

        return AssetSaveTrendResponse(
            xAxises=[f"{i + int(str(get_now_datetime().year)[-2:]) + 1}" for i in range(ASSET_SAVE_TREND_YEAR)],
            dates=[f"{i + 1}년후" for i in range(ASSET_SAVE_TREND_YEAR)],
            values1=values1,
            values2=values2,
            unit=unit,
        )


class ChartTipResponse(RootModel[str]):
    pass


class ProfitDetail(BaseModel):
    profit_amount: float = Field(..., description="수익금")
    profit_rate: float = Field(..., description="수익률")

    @classmethod
    def parse(cls, total_asset_amount: float, total_investment_amount: float) -> "ProfitDetail":
        """총 자산 금액과 투자 금액을 받아 수익금과 수익률을 계산."""
        profit_amount = total_asset_amount - total_investment_amount
        profit_rate = (profit_amount / total_investment_amount) * 100 if total_investment_amount > 0.0 else 0.0
        return cls(profit_amount=profit_amount, profit_rate=profit_rate)


class SummaryResponse(BaseModel):
    # [TODO] 협의 후 바로 추가할 인자입니다.
    # increase_asset_amount: float = Field(..., description="오늘의 review 증가액")
    today_review_rate: float = Field(..., description="오늘의 review 수익금")
    total_asset_amount: float = Field(..., description="나의 총 자산")
    total_investment_amount: float = Field(..., description="나의 투자 금액")
    profit: ProfitDetail = Field(..., description="수익 정보")

    @classmethod
    def validate(cls, assets: list[Asset]) -> Optional["SummaryResponse"]:
        if not len(assets):
            return cls(
                increase_asset_amount=0.0,
                today_review_rate=0.0,
                total_asset_amount=0.0,
                total_investment_amount=0.0,
                profit=ProfitDetail(profit_amount=0.0, profit_rate=0.0),
            )
        else:
            return None


class MarketIndiceValue(BaseModel):
    name: str = Field(..., example=f"{', '.join([e.value for e in MarketIndex])}")
    name_kr: str = Field(..., description="한국어 지수 이름", example=f"{', '.join(MARKET_INDEX_KR_MAPPING.values())}")
    current_value: float = Field(..., description="현재 지수")
    change_percent: float = Field(..., description="1일 기준 변동성")


class MarketIndiceResponse(RootModel[list[MarketIndiceValue]]):
    pass


class CompositionResponseValue(BaseModel):
    name: str = Field(..., description="종목 명 혹은 계좌 명")
    percent_rate: float = Field(..., description="비중")
    current_amount: float = Field(..., description="현재가")


class CompositionResponse(RootModel[list[CompositionResponseValue]]):
    @classmethod
    def validate(cls, assets: list[Asset]) -> Optional["CompositionResponse"]:
        if not len(assets):
            return CompositionResponse([])
        else:
            return None


class PerformanceAnalysisResponse(BaseModel):
    xAxises: list[str]
    dates: list[str]
    values1: dict
    values2: dict
    unit: str
    myReturnRate: float
    contrastMarketReturns: float

    @classmethod
    def validate(cls, assets: list[Asset]) -> Optional["PerformanceAnalysisResponse"]:
        if not len(assets):
            return cls(
                xAxises=[], dates=[], values1={}, values2={}, unit="", myReturnRate=0.0, contrastMarketReturns=0.0
            )
        else:
            return None

    @classmethod
    def parse(
        cls,
        market_analysis_data: dict[datetime, float] | dict[date, float] | dict[tuple[int, int], float],
        user_analysis_data: dict[datetime, float] | dict[date, float] | dict[tuple[int, int], float],
        interval_times: list[datetime] | list[date],
        interval: IntervalType,
    ) -> "PerformanceAnalysisResponse":
        if interval is IntervalType.ONEMONTH:
            return cls(
                xAxises=[interval_time.strftime("%m.%d") for interval_time in interval_times],
                dates=[interval_time.strftime("%Y.%m.%d") for interval_time in interval_times],
                values1={
                    "values": [user_analysis_data[interval_time] for interval_time in interval_times],  # type: ignore # IntervalType.FIVEDAY 조건에 의해 date 보장
                    "name": "내 수익률",
                },
                values2={
                    "values": [market_analysis_data[interval_time] for interval_time in interval_times],  # type: ignore # IntervalType.FIVEDAY 조건에 의해 date 보장
                    "name": "코스피",
                },
                unit="%",
                myReturnRate=mean([user_analysis_data[interval_time] for interval_time in interval_times]),  # type: ignore # IntervalType.FIVEDAY 조건에 의해 date 보장
                contrastMarketReturns=mean([market_analysis_data[interval_time] for interval_time in interval_times]),  # type: ignore # IntervalType.FIVEDAY 조건에 의해 date 보장
            )
        else:
            interval_year_month = sorted(
                set([(interval_time.year, interval_time.month) for interval_time in interval_times])
            )
            return cls(
                xAxises=[f"{str(year)[-2:]}.{month}" for year, month in interval_year_month],
                dates=[f"{year}.{month}" for year, month in interval_year_month],
                values1={
                    "values": [user_analysis_data.get(interval_time, 0) for interval_time in interval_year_month],  # type: ignore # IntervalType.FIVEDAY 조건에 의해 date 보장
                    "name": "내 수익률",
                },
                values2={
                    "values": [market_analysis_data.get(interval_time, 0) for interval_time in interval_year_month],  # type: ignore # IntervalType.FIVEDAY 조건에 의해 date 보장
                    "name": "코스피",
                },
                unit="%",
                myReturnRate=mean([user_analysis_data.get(interval_time, 0) for interval_time in interval_year_month]),  # type: ignore # IntervalType.FIVEDAY 조건에 의해 date 보장
                contrastMarketReturns=mean([market_analysis_data.get(interval_time, 0) for interval_time in interval_year_month]),  # type: ignore # IntervalType.FIVEDAY 조건에 의해 date 보장
            )


class EstimateDividendEveryValue(BaseModel):
    xAxises: list[str] = Field(..., description="월별 표시 (1월, 2월, ...)")
    data: list[float] = Field(..., description="월별 배당금 데이터")
    unit: str = Field(..., description="단위")
    total: float = Field(..., description="해당 연도의 배당금 총합")


class EstimateDividendEveryResponse(RootModel[dict[str, EstimateDividendEveryValue]]):
    @classmethod
    def validate(cls, assets: list[Asset]) -> Optional["EstimateDividendEveryResponse"]:
        if not len(assets):
            return EstimateDividendEveryResponse(
                {str(date.today().year): EstimateDividendEveryValue(xAxises=[], data=[], unit="", total=0.0)}
            )
        else:
            return None


class EstimateDividendTypeValue(BaseModel):
    name: str
    current_amount: float
    percent_rate: float


class EstimateDividendTypeResponse(RootModel[list[EstimateDividendTypeValue]]):
    @classmethod
    def validate(cls, assets: list[Asset]) -> Optional["EstimateDividendEveryResponse"]:
        if not len(assets):
            return EstimateDividendTypeResponse(
                [EstimateDividendTypeValue(name="", current_amount=0.0, percent_rate=0.0)]
            )
        else:
            return None


class MyStockResponseValue(BaseModel):
    name: str
    current_price: float
    profit_rate: float
    profit_amount: float
    quantity: int


class MyStockResponse(RootModel[list[MyStockResponseValue]]):
    pass


class RichPickValue(BaseModel):
    name: str
    price: float
    rate: float


class RichPickResponse(RootModel[list[RichPickValue]]):
    pass


class PortfolioStockData(BaseModel):
    name: str
    percent_ratio: float


class RichPortfolioValue(BaseModel):
    name: str
    data: list[PortfolioStockData]


class RichPortfolioResponse(RootModel[list[RichPortfolioValue]]):
    pass


class PeoplePortfolioValue(BaseModel):
    name: str
    data: list[PortfolioStockData]


class PeoplePortfolioResponse(RootModel[list[PeoplePortfolioValue]]):
    pass
