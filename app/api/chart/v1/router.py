from datetime import date, datetime, timedelta
from statistics import mean

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.common.util.time import get_now_date
from app.module.asset.constant import (
    ASSET_FIELD,
    ASSET_SAVE_TREND_YEAR,
    INFLATION_RATE,
    MARKET_INDEX_KR_MAPPING,
    MONTHS,
    THREE_MONTH,
    THREE_MONTH_DAY,
)
from app.module.asset.dependencies.asset_dependency import get_asset_service
from app.module.asset.enum import AssetType, CurrencyType, StockAsset
from app.module.asset.facades.asset_facade import AssetFacade
from app.module.asset.facades.dividend_facade import DividendFacade
from app.module.asset.model import Asset, StockDaily
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import MarketIndexData
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_service import StockService
from app.module.auth.constant import DUMMY_USER_ID
from app.module.auth.schema import AccessToken
from app.module.chart.constant import DEFAULT_TIP, TIP_TODAY_ID_REDIS_KEY
from app.module.chart.enum import CompositionType, EstimateDividendType, IntervalType
from app.module.chart.facade.composition_facade import CompositionFacade
from app.module.chart.facade.performance_analysis_facade import PerformanceAnalysisFacade
from app.module.chart.facade.rich_facade import RichFacade
from app.module.chart.facade.summary_facade import SummaryFacade
from app.module.chart.redis_repository import RedisTipRepository
from app.module.chart.repository import TipRepository
from app.module.chart.schema import (
    AssetSaveTrendResponse,
    ChartTipResponse,
    CompositionResponse,
    CompositionResponseValue,
    EstimateDividendEveryResponse,
    EstimateDividendEveryValue,
    EstimateDividendTypeResponse,
    EstimateDividendTypeValue,
    MarketIndiceResponse,
    MarketIndiceResponseValue,
    MyStockResponse,
    MyStockResponseValue,
    PeoplePortfolioResponse,
    PeoplePortfolioValue,
    PerformanceAnalysisResponse,
    PortfolioStockData,
    ProfitDetail,
    RichPickResponse,
    RichPickValue,
    RichPortfolioResponse,
    RichPortfolioValue,
    SummaryResponse,
)
from app.module.chart.service.index_service import IndexService
from app.module.chart.service.rich_portfolio_service import RichPortfolioService
from app.module.chart.service.save_trend_service import SaveTrendService
from database.dependency import get_mysql_session_router, get_redis_pool

chart_router = APIRouter(prefix="/v1")


@chart_router.get("/rich-portfolio", summary="부자들의 포트폴리오", response_model=RichPortfolioResponse)
async def get_rich_portfolio(redis_client: Redis = Depends(get_redis_pool)) -> RichPortfolioResponse:
    rich_portfolio_map: dict = await RichPortfolioService.get_rich_porfolio_map(redis_client)

    return RichPortfolioResponse(
        [
            RichPortfolioValue(
                name=person,
                data=[
                    PortfolioStockData(name=stock, percent_ratio=float(percent.strip("%")))
                    for stock, percent in portfolio.items()
                ],
            )
            for person, portfolio in rich_portfolio_map.items()
        ]
    )


# 임시 dummy api 생성, 추후 개발하겠습니다.
@chart_router.get("/people-portfolio", summary="포트폴리오 구경하기", response_model=PeoplePortfolioResponse)
async def get_people_portfolio():
    return PeoplePortfolioResponse(
        [
            PeoplePortfolioValue(
                name="배당주 포트폴리오",
                data=[
                    PortfolioStockData(name="코카콜라", percent_ratio=10.5),
                    PortfolioStockData(name="펩시코", percent_ratio=8.4),
                    PortfolioStockData(name="존슨앤존슨", percent_ratio=7.2),
                    PortfolioStockData(name="프록터 앤 갬블", percent_ratio=6.3),
                    PortfolioStockData(name="맥도날드", percent_ratio=5.7),
                    PortfolioStockData(name="화이자", percent_ratio=4.9),
                    PortfolioStockData(name="머크", percent_ratio=4.3),
                    PortfolioStockData(name="AT&T", percent_ratio=3.8),
                    PortfolioStockData(name="버라이즌", percent_ratio=3.2),
                    PortfolioStockData(name="IBM", percent_ratio=2.9),
                ],
            ),
            PeoplePortfolioValue(
                name="성장주 포트폴리오",
                data=[
                    PortfolioStockData(name="애플", percent_ratio=20.1),
                    PortfolioStockData(name="아마존", percent_ratio=18.3),
                    PortfolioStockData(name="구글", percent_ratio=17.2),
                    PortfolioStockData(name="마이크로소프트", percent_ratio=15.5),
                    PortfolioStockData(name="엔비디아", percent_ratio=12.3),
                    PortfolioStockData(name="테슬라", percent_ratio=8.9),
                    PortfolioStockData(name="메타", percent_ratio=5.0),
                    PortfolioStockData(name="넷플릭스", percent_ratio=2.7),
                ],
            ),
            PeoplePortfolioValue(
                name="국내 포트폴리오",
                data=[
                    PortfolioStockData(name="삼성전자", percent_ratio=25.6),
                    PortfolioStockData(name="SK하이닉스", percent_ratio=19.8),
                    PortfolioStockData(name="LG화학", percent_ratio=12.4),
                    PortfolioStockData(name="NAVER", percent_ratio=9.3),
                    PortfolioStockData(name="카카오", percent_ratio=8.7),
                    PortfolioStockData(name="셀트리온", percent_ratio=7.4),
                    PortfolioStockData(name="현대차", percent_ratio=6.2),
                    PortfolioStockData(name="삼성SDI", percent_ratio=5.1),
                ],
            ),
            PeoplePortfolioValue(
                name="안전자산 포트폴리오",
                data=[
                    PortfolioStockData(name="SPDR 골드 트러스트", percent_ratio=35.0),
                    PortfolioStockData(name="바클레이즈 미국 채권", percent_ratio=25.0),
                    PortfolioStockData(name="뱅가드 리츠", percent_ratio=15.0),
                    PortfolioStockData(name="팁스 (물가연동채)", percent_ratio=10.0),
                    PortfolioStockData(name="애그리게이트 채권", percent_ratio=8.0),
                    PortfolioStockData(name="중기채권 (IEF)", percent_ratio=7.0),
                ],
            ),
            PeoplePortfolioValue(
                name="소형주 포트폴리오",
                data=[
                    PortfolioStockData(name="리제네론", percent_ratio=14.7),
                    PortfolioStockData(name="빌드", percent_ratio=13.4),
                    PortfolioStockData(name="코덱스시스", percent_ratio=11.9),
                    PortfolioStockData(name="크라토스", percent_ratio=10.5),
                    PortfolioStockData(name="NMI 홀딩스", percent_ratio=9.1),
                    PortfolioStockData(name="트랜스메딕스", percent_ratio=8.8),
                    PortfolioStockData(name="브룸", percent_ratio=8.4),
                    PortfolioStockData(name="캐네디언솔라", percent_ratio=7.6),
                    PortfolioStockData(name="이뮤노메딕스", percent_ratio=6.5),
                    PortfolioStockData(name="래피드7", percent_ratio=5.1),
                ],
            ),
            PeoplePortfolioValue(
                name="테크주 포트폴리오",
                data=[
                    PortfolioStockData(name="애플", percent_ratio=22.0),
                    PortfolioStockData(name="마이크로소프트", percent_ratio=18.3),
                    PortfolioStockData(name="구글", percent_ratio=16.1),
                    PortfolioStockData(name="아마존", percent_ratio=15.5),
                    PortfolioStockData(name="엔비디아", percent_ratio=12.2),
                    PortfolioStockData(name="테슬라", percent_ratio=9.8),
                    PortfolioStockData(name="메타", percent_ratio=6.1),
                ],
            ),
        ]
    )


@chart_router.get("/sample/asset-save-trend", summary="자산적립 추이", response_model=AssetSaveTrendResponse)
async def get_sample_asset_save_trend(
    session: AsyncSession = Depends(get_mysql_session_router), redis_client: Redis = Depends(get_redis_pool)
) -> AssetSaveTrendResponse:
    asset_all: list = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    if len(asset_all) == 0:
        return AssetSaveTrendResponse(xAxises=[], dates=[], values1={}, values2={}, unit="")
    total_asset_amount_all = await AssetFacade.get_total_asset_amount(session, redis_client, asset_all)

    asset_3month: list = await AssetRepository.get_eager_by_range(
        session, DUMMY_USER_ID, AssetType.STOCK, (get_now_date() - timedelta(days=THREE_MONTH_DAY), get_now_date())
    )
    if len(asset_3month) == 0:
        return AssetSaveTrendResponse.no_near_invest_response(total_asset_amount_all)

    total_asset_amount: float = await AssetFacade.get_total_asset_amount(session, redis_client, asset_3month)
    total_invest_amount: float = await AssetFacade.get_total_investment_amount(session, redis_client, asset_3month)
    total_dividend_amount: float = await DividendFacade.get_total_dividend(session, redis_client, asset_3month)

    total_profit_rate = AssetStockService.get_total_profit_rate(total_asset_amount, total_invest_amount)
    total_profit_rate_real = AssetStockService.get_total_profit_rate_real(
        total_asset_amount, total_invest_amount, INFLATION_RATE
    )

    increase_invest_year = AssetService.get_average_investment_with_dividend_year(
        total_invest_amount, total_dividend_amount, THREE_MONTH
    )

    values1, values2, unit = AssetService.calculate_trend_values(
        total_asset_amount_all, increase_invest_year, total_profit_rate, total_profit_rate_real, ASSET_SAVE_TREND_YEAR
    )

    return AssetSaveTrendResponse(
        xAxises=SaveTrendService.get_x_axises(ASSET_SAVE_TREND_YEAR),
        dates=SaveTrendService.get_dates(ASSET_SAVE_TREND_YEAR),
        values1=values1,
        values2=values2,
        unit=unit,
    )


@chart_router.get("/asset-save-trend", summary="자산적립 추이", response_model=AssetSaveTrendResponse)
async def get_asset_save_trend(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> AssetSaveTrendResponse:
    asset_all: list = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    if len(asset_all) == 0:
        return AssetSaveTrendResponse(xAxises=[], dates=[], values1={}, values2={}, unit="")
    total_asset_amount_all = await AssetFacade.get_total_asset_amount(session, redis_client, asset_all)

    asset_3month: list = await AssetRepository.get_eager_by_range(
        session, token.get("user"), AssetType.STOCK, (get_now_date() - timedelta(days=THREE_MONTH_DAY), get_now_date())
    )
    if len(asset_3month) == 0:
        return AssetSaveTrendResponse.no_near_invest_response(total_asset_amount_all)

    total_asset_amount: float = await AssetFacade.get_total_asset_amount(session, redis_client, asset_3month)
    total_invest_amount: float = await AssetFacade.get_total_investment_amount(session, redis_client, asset_3month)
    total_dividend_amount: float = await DividendFacade.get_total_dividend(session, redis_client, asset_3month)

    total_profit_rate = AssetStockService.get_total_profit_rate(total_asset_amount, total_invest_amount)
    total_profit_rate_real = AssetStockService.get_total_profit_rate_real(
        total_asset_amount, total_invest_amount, INFLATION_RATE
    )

    increase_invest_year = AssetService.get_average_investment_with_dividend_year(
        total_invest_amount, total_dividend_amount, THREE_MONTH
    )

    values1, values2, unit = AssetService.calculate_trend_values(
        total_asset_amount, increase_invest_year, total_profit_rate, total_profit_rate_real, ASSET_SAVE_TREND_YEAR
    )

    return AssetSaveTrendResponse(
        xAxises=SaveTrendService.get_x_axises(ASSET_SAVE_TREND_YEAR),
        dates=SaveTrendService.get_dates(ASSET_SAVE_TREND_YEAR),
        values1=values1,
        values2=values2,
        unit=unit,
    )


@chart_router.get(
    "/sample/estimate-dividend",
    summary="더미 예상 배당액",
    response_model=EstimateDividendEveryResponse | EstimateDividendTypeResponse,
)
async def get_sample_estimate_dividend(
    category: EstimateDividendType = Query(EstimateDividendType.EVERY, description="every는 모두, type은 종목 별 입니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> EstimateDividendEveryResponse | EstimateDividendTypeResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    if len(assets) == 0:
        return (
            EstimateDividendEveryResponse(
                {str(date.today().year): EstimateDividendEveryValue(xAxises=[], data=[], unit="", total=0.0)}
            )
            if category == EstimateDividendType.EVERY
            else EstimateDividendTypeResponse(
                [EstimateDividendTypeValue(name="", current_amount=0.0, percent_rate=0.0)]
            )
        )

    exchange_rate_map: dict[str, float] = await ExchangeRateService.get_exchange_rate_map(redis_client)
    dividend_map: dict[tuple[str, date], float] = await DividendService.get_dividend_map(session, assets)
    recent_dividend_map: dict[str, float] = await DividendService.get_recent_map(session, assets)

    if category == EstimateDividendType.EVERY:
        total_dividends: dict[date, float] = DividendFacade.get_full_month_estimate_dividend(
            assets, exchange_rate_map, dividend_map
        )

        dividend_data_by_year = DividendService.process_dividends_by_year_month(total_dividends)

        response_data = {}
        for year, months in dividend_data_by_year.items():
            data = [months.get(month, 0.0) for month in range(1, 13)]
            total = sum(data)
            response_data[year] = EstimateDividendEveryValue(xAxises=MONTHS, data=data, unit="원", total=total)

        return EstimateDividendEveryResponse(response_data)
    else:
        total_type_dividends: list[tuple[str, float, float]] = await DividendFacade.get_composition(
            assets, exchange_rate_map, recent_dividend_map
        )

        return EstimateDividendTypeResponse(
            [
                EstimateDividendTypeValue(name=stock_code, current_amount=amount, percent_rate=composition_rate)
                for stock_code, amount, composition_rate in total_type_dividends
            ]
        )


@chart_router.get(
    "/estimate-dividend", summary="예상 배당액", response_model=EstimateDividendEveryResponse | EstimateDividendTypeResponse
)
async def get_estimate_dividend(
    token: AccessToken = Depends(verify_jwt_token),
    category: EstimateDividendType = Query(EstimateDividendType.EVERY, description="every는 모두, type은 종목 별 입니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> EstimateDividendEveryResponse | EstimateDividendTypeResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, int(token.get("user")), AssetType.STOCK)
    if len(assets) == 0:
        return (
            EstimateDividendEveryResponse(
                {str(date.today().year): EstimateDividendEveryValue(xAxises=[], data=[], unit="", total=0.0)}
            )
            if category == EstimateDividendType.EVERY
            else EstimateDividendTypeResponse(
                [EstimateDividendTypeValue(name="", current_amount=0.0, percent_rate=0.0)]
            )
        )

    exchange_rate_map: dict[str, float] = await ExchangeRateService.get_exchange_rate_map(redis_client)
    dividend_map: dict[tuple[str, date], float] = await DividendService.get_dividend_map(session, assets)
    recent_dividend_map: dict[str, float] = await DividendService.get_recent_map(session, assets)

    if category == EstimateDividendType.EVERY:
        total_dividends: dict[date, float] = DividendFacade.get_full_month_estimate_dividend(
            assets, exchange_rate_map, dividend_map
        )

        dividend_data_by_year = DividendService.process_dividends_by_year_month(total_dividends)

        response_data = {}
        for year, months in dividend_data_by_year.items():
            data = [months.get(month, 0.0) for month in range(1, 13)]
            total = sum(data)
            response_data[year] = EstimateDividendEveryValue(xAxises=MONTHS, data=data, unit="만원", total=total)

        return EstimateDividendEveryResponse(response_data)
    else:
        total_type_dividends: list[tuple[str, float, float]] = await DividendFacade.get_composition(
            assets, exchange_rate_map, recent_dividend_map
        )

        return EstimateDividendTypeResponse(
            [
                EstimateDividendTypeValue(name=stock_code, current_amount=amount, percent_rate=composition_rate)
                for stock_code, amount, composition_rate in total_type_dividends
            ]
        )


@chart_router.get("/sample/performance-analysis", summary="더미 투자 성과 분석", response_model=PerformanceAnalysisResponse)
async def get_sample_performance_analysis(
    interval: IntervalType = Query(IntervalType.ONEMONTH, description="기간 별, 투자 성관 분석 데이터가 제공 됩니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> PerformanceAnalysisResponse:
    if interval is IntervalType.ONEMONTH:
        start_date, end_date = interval.get_start_end_time()
        market_analysis_result: dict[date, float] = await PerformanceAnalysisFacade.get_market_analysis(
            session, redis_client, start_date, end_date
        )
        user_analysis_result: dict[date, float] = await PerformanceAnalysisFacade.get_user_analysis_single_month(
            session, redis_client, DUMMY_USER_ID, interval, market_analysis_result
        )

        sorted_dates = sorted(market_analysis_result.keys())

        return PerformanceAnalysisResponse(
            xAxises=[date.strftime("%m.%d") for date in sorted_dates],
            dates=[date.strftime("%Y.%m.%d") for date in sorted_dates],
            values1={"values": [user_analysis_result[date] for date in sorted_dates], "name": "내 수익률"},
            values2={"values": [market_analysis_result[date] for date in sorted_dates], "name": "코스피"},
            unit="%",
            myReturnRate=mean([user_analysis_result[date] for date in sorted_dates]),
            contrastMarketReturns=mean([market_analysis_result[date] for date in sorted_dates]),
        )
    elif interval in IntervalType.FIVEDAY:
        start_datetime, end_datetime = interval.get_start_end_time()

        market_analysis_result_short: dict[datetime, float] = await PerformanceAnalysisFacade.get_market_analysis_short(
            session, redis_client, start_datetime, end_datetime, interval
        )
        user_analysis_result_short: dict[datetime, float] = await PerformanceAnalysisFacade.get_user_analysis_short(
            session,
            redis_client,
            start_datetime,
            end_datetime,
            DUMMY_USER_ID,
            interval,
            market_analysis_result_short,
        )

        sorted_datetimes = sorted(market_analysis_result_short.keys())

        return PerformanceAnalysisResponse(
            xAxises=[datetime.strftime("%m.%d") for datetime in sorted_datetimes],
            dates=[datetime.strftime("%Y.%m.%d %H:%M") for datetime in sorted_datetimes],
            values1={
                "values": [user_analysis_result_short[datetime] for datetime in sorted_datetimes],
                "name": "내 수익률",
            },
            values2={
                "values": [market_analysis_result_short[datetime] for datetime in sorted_datetimes],
                "name": "코스피",
            },
            unit="%",
            myReturnRate=mean([user_analysis_result_short[datetime] for datetime in sorted_datetimes]),
            contrastMarketReturns=mean([market_analysis_result_short[datetime] for datetime in sorted_datetimes]),
        )
    else:
        start_date, end_date = interval.get_start_end_time()
        market_analysis_result_month: dict[date, float] = await PerformanceAnalysisFacade.get_market_analysis(
            session, redis_client, start_date, end_date
        )
        user_analysis_result_month: dict[date, float] = await PerformanceAnalysisFacade.get_user_analysis(
            session, redis_client, start_date, end_date, DUMMY_USER_ID, market_analysis_result_month
        )

        return PerformanceAnalysisResponse.get_performance_analysis_response(
            market_analysis_result_month, user_analysis_result_month, interval
        )


@chart_router.get("/performance-analysis", summary="투자 성과 분석", response_model=PerformanceAnalysisResponse)
async def get_performance_analysis(
    token: AccessToken = Depends(verify_jwt_token),
    interval: IntervalType = Query(IntervalType.ONEMONTH, description="기간 별, 투자 성관 분석 데이터가 제공 됩니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> PerformanceAnalysisResponse:
    if interval is IntervalType.ONEMONTH:
        start_date, end_date = interval.get_start_end_time()
        market_analysis_result: dict[date, float] = await PerformanceAnalysisFacade.get_market_analysis(
            session, redis_client, start_date, end_date
        )
        user_analysis_result: dict[date, float] = await PerformanceAnalysisFacade.get_user_analysis(
            session, redis_client, start_date, end_date, token.get("user"), market_analysis_result
        )
        sorted_dates = sorted(market_analysis_result.keys())

        return PerformanceAnalysisResponse(
            xAxises=[date.strftime("%m.%d") for date in sorted_dates],
            dates=[date.strftime("%Y.%m.%d") for date in sorted_dates],
            values1={"values": [user_analysis_result[date] for date in sorted_dates], "name": "내 수익률"},
            values2={"values": [market_analysis_result[date] for date in sorted_dates], "name": "코스피"},
            unit="%",
            myReturnRate=mean([user_analysis_result[date] for date in sorted_dates]),
            contrastMarketReturns=mean([market_analysis_result[date] for date in sorted_dates]),
        )
    elif interval in IntervalType.FIVEDAY:
        start_datetime, end_datetime = interval.get_start_end_time()

        market_analysis_result_short: dict[datetime, float] = await PerformanceAnalysisFacade.get_market_analysis_short(
            session, redis_client, start_datetime, end_datetime, interval
        )
        user_analysis_result_short: dict[datetime, float] = await PerformanceAnalysisFacade.get_user_analysis_short(
            session,
            redis_client,
            start_datetime,
            end_datetime,
            token.get("user"),
            interval,
            market_analysis_result_short,
        )

        sorted_datetimes = sorted(market_analysis_result_short.keys())

        return PerformanceAnalysisResponse(
            xAxises=[datetime.strftime("%m.%d") for datetime in sorted_datetimes],
            dates=[datetime.strftime("%Y.%m.%d %H:%M") for datetime in sorted_datetimes],
            values1={
                "values": [user_analysis_result_short[datetime] for datetime in sorted_datetimes],
                "name": "내 수익률",
            },
            values2={
                "values": [market_analysis_result_short[datetime] for datetime in sorted_datetimes],
                "name": "코스피",
            },
            unit="%",
            myReturnRate=mean([user_analysis_result_short[datetime] for datetime in sorted_datetimes]),
            contrastMarketReturns=mean([market_analysis_result_short[datetime] for datetime in sorted_datetimes]),
        )
    else:
        start_date, end_date = interval.get_start_end_time()
        market_analysis_result_month: dict[date, float] = await PerformanceAnalysisFacade.get_market_analysis(
            session, redis_client, start_date, end_date
        )
        user_analysis_result_month: dict[date, float] = await PerformanceAnalysisFacade.get_user_analysis(
            session, redis_client, start_date, end_date, token.get("user"), market_analysis_result_month
        )

        return PerformanceAnalysisResponse.get_performance_analysis_response(
            market_analysis_result_month, user_analysis_result_month, interval
        )


@chart_router.get("/sample/composition", summary="종목 구성", response_model=CompositionResponse)
async def get_sample_composition(
    type: CompositionType = Query(CompositionType.COMPOSITION, description="composition은 종목 별, account는 계좌 별 입니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> CompositionResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    if len(assets) == 0:
        return CompositionResponse([CompositionResponseValue(name="자산 없음", percent_rate=0.0, current_amount=0.0)])

    lastest_stock_daily_map = await StockDailyService.get_latest_map(session, assets)
    current_stock_price_map = await StockService.get_current_stock_price_by_code(
        redis_client, lastest_stock_daily_map, [asset.asset_stock.stock.code for asset in assets]
    )
    exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)

    if type is CompositionType.COMPOSITION:
        stock_composition_data = CompositionFacade.get_asset_stock_composition(
            assets, current_stock_price_map, exchange_rate_map
        )
        return CompositionResponse(
            [
                CompositionResponseValue(
                    name=item["name"], percent_rate=item["percent_rate"], current_amount=item["current_amount"]
                )
                for item in stock_composition_data
            ]
        )
    else:
        account_composition_data = CompositionFacade.get_asset_stock_account(
            assets, current_stock_price_map, exchange_rate_map
        )

        return CompositionResponse(
            [
                CompositionResponseValue(
                    name=item["name"], percent_rate=item["percent_rate"], current_amount=item["current_amount"]
                )
                for item in account_composition_data
            ]
        )


@chart_router.get("/composition", summary="종목 구성", response_model=CompositionResponse)
async def get_composition(
    token: AccessToken = Depends(verify_jwt_token),
    type: CompositionType = Query(CompositionType.COMPOSITION, description="composition은 종목 별, account는 계좌 별 입니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> CompositionResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    if len(assets) == 0:
        return CompositionResponse([CompositionResponseValue(name="자산 없음", percent_rate=0.0, current_amount=0.0)])

    lastest_stock_daily_map = await StockDailyService.get_latest_map(session, assets)
    current_stock_price_map = await StockService.get_current_stock_price_by_code(
        redis_client, lastest_stock_daily_map, [asset.asset_stock.stock.code for asset in assets]
    )
    exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)

    if type is CompositionType.COMPOSITION:
        stock_composition_data = CompositionFacade.get_asset_stock_composition(
            assets, current_stock_price_map, exchange_rate_map
        )
        return CompositionResponse(
            [
                CompositionResponseValue(
                    name=item["name"], percent_rate=item["percent_rate"], current_amount=item["current_amount"]
                )
                for item in stock_composition_data
            ]
        )
    else:
        account_composition_data = CompositionFacade.get_asset_stock_account(
            assets, current_stock_price_map, exchange_rate_map
        )

        return CompositionResponse(
            [
                CompositionResponseValue(
                    name=item["name"], percent_rate=item["percent_rate"], current_amount=item["current_amount"]
                )
                for item in account_composition_data
            ]
        )


@chart_router.get("/sample/my-stock", summary="내 보유 주식", response_model=MyStockResponse)
async def get_sample_my_stock(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
) -> MyStockResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    if len(assets) == 0:
        return MyStockResponse(
            [MyStockResponseValue(name="", current_price=0.0, profit_rate=0.0, profit_amount=0.0, quantity=0)]
        )

    stock_assets: list[dict] = await asset_service.get_stock_assets(session, redis_client, assets, ASSET_FIELD)

    return MyStockResponse(
        [
            MyStockResponseValue(
                name=stock_asset[StockAsset.STOCK_NAME.value]["value"],
                current_price=stock_asset[StockAsset.CURRENT_PRICE.value]["value"],
                profit_rate=stock_asset[StockAsset.PROFIT_RATE.value]["value"],
                profit_amount=stock_asset[StockAsset.PROFIT_AMOUNT.value]["value"],
                quantity=stock_asset[StockAsset.QUANTITY.value]["value"],
            )
            for stock_asset in stock_assets
        ]
    )


@chart_router.get("/my-stock", summary="내 보유 주식", response_model=MyStockResponse)
async def get_my_stock(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
) -> MyStockResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    if len(assets) == 0:
        return MyStockResponse(
            [MyStockResponseValue(name="", current_price=0.0, profit_rate=0.0, profit_amount=0.0, quantity=0)]
        )

    stock_assets: list[dict] = await asset_service.get_stock_assets(session, redis_client, assets, ASSET_FIELD)

    return MyStockResponse(
        [
            MyStockResponseValue(
                name=stock_asset[StockAsset.STOCK_NAME.value]["value"],
                current_price=stock_asset[StockAsset.CURRENT_PRICE.value]["value"],
                profit_rate=stock_asset[StockAsset.PROFIT_RATE.value]["value"],
                profit_amount=stock_asset[StockAsset.PROFIT_AMOUNT.value]["value"],
                quantity=stock_asset[StockAsset.QUANTITY.value]["value"],
            )
            for stock_asset in stock_assets
        ]
    )


@chart_router.get("/summary", summary="오늘의 리뷰, 나의 총자산, 나의 투자 금액, 수익금", response_model=SummaryResponse)
async def get_summary(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> SummaryResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, token.get("user"), AssetType.STOCK)
    if len(assets) == 0:
        return SummaryResponse(
            today_review_rate=0.0,
            total_asset_amount=0,
            total_investment_amount=0,
            profit=ProfitDetail(profit_amount=0.0, profit_rate=0.0),
        )

    latest_stock_daily_map: dict[str, StockDaily] = await StockDailyService.get_latest_map(session, assets)
    current_stock_price_map: dict[str, float] = await StockService.get_current_stock_price_by_code(
        redis_client, latest_stock_daily_map, [asset.asset_stock.stock.code for asset in assets]
    )
    exchange_rate_map: dict[str, float] = await ExchangeRateService.get_exchange_rate_map(redis_client)

    total_asset_amount = await AssetFacade.get_total_asset_amount(session, redis_client, assets)
    total_investment_amount = await AssetFacade.get_total_investment_amount(session, redis_client, assets)
    today_review_rate: float = SummaryFacade.get_today_review_rate(
        assets, total_asset_amount, current_stock_price_map, exchange_rate_map
    )

    return SummaryResponse(
        today_review_rate=today_review_rate,
        total_asset_amount=total_asset_amount,
        total_investment_amount=total_investment_amount,
        profit=ProfitDetail(
            profit_amount=total_asset_amount - total_investment_amount,
            profit_rate=(total_asset_amount - total_investment_amount) / total_asset_amount * 100
            if total_investment_amount > 0.0 and total_asset_amount > 0.0
            else 0.0,
        ),
    )


@chart_router.get("/sample/summary", summary="오늘의 리뷰, 나의 총자산, 나의 투자 금액, 수익금", response_model=SummaryResponse)
async def get_sample_summary(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> SummaryResponse:
    assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
    if len(assets) == 0:
        return SummaryResponse(
            today_review_rate=0.0,
            total_asset_amount=0,
            total_investment_amount=0,
            profit=ProfitDetail(profit_amount=0.0, profit_rate=0.0),
        )

    latest_stock_daily_map: dict[str, StockDaily] = await StockDailyService.get_latest_map(session, assets)
    current_stock_price_map: dict[str, float] = await StockService.get_current_stock_price_by_code(
        redis_client, latest_stock_daily_map, [asset.asset_stock.stock.code for asset in assets]
    )
    exchange_rate_map: dict[str, float] = await ExchangeRateService.get_exchange_rate_map(redis_client)

    total_asset_amount = await AssetFacade.get_total_asset_amount(session, redis_client, assets)
    total_investment_amount = await AssetFacade.get_total_investment_amount(session, redis_client, assets)
    today_review_rate: float = SummaryFacade.get_today_review_rate(
        assets, total_asset_amount, current_stock_price_map, exchange_rate_map
    )

    return SummaryResponse(
        today_review_rate=today_review_rate,
        total_asset_amount=total_asset_amount,
        total_investment_amount=total_investment_amount,
        profit=ProfitDetail(
            profit_amount=total_asset_amount - total_investment_amount,
            profit_rate=(total_asset_amount - total_investment_amount) / total_asset_amount * 100
            if total_investment_amount > 0.0 and total_asset_amount > 0.0
            else 0.0,
        ),
    )


@chart_router.get("/tip", summary="오늘의 투자 tip", response_model=ChartTipResponse)
async def get_today_tip(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> ChartTipResponse:
    today_tip_id = await RedisTipRepository.get(redis_client, TIP_TODAY_ID_REDIS_KEY)

    if today_tip_id is None:
        return ChartTipResponse(DEFAULT_TIP)

    invest_tip = await TipRepository.get(session, int(today_tip_id))

    if invest_tip is None:
        return ChartTipResponse(DEFAULT_TIP)

    return ChartTipResponse(invest_tip.tip)


@chart_router.get("/indice", summary="현재 시장 지수", response_model=MarketIndiceResponse)
async def get_market_index(
    redis_client: Redis = Depends(get_redis_pool),
) -> MarketIndiceResponse:
    market_index_values: list[MarketIndexData] = await IndexService.get_current_market_index_value(redis_client)

    return MarketIndiceResponse(
        [
            MarketIndiceResponseValue(
                name=market_index_value.name,
                name_kr=MARKET_INDEX_KR_MAPPING.get(market_index_value.name, "N/A"),
                current_value=float(market_index_value.current_value),
                change_percent=float(market_index_value.change_percent),
            )
            for market_index_value in market_index_values
            if market_index_value is not None
        ]
    )


@chart_router.get("/rich-pick", summary="미국 부자들이 선택한 종목 TOP10", response_model=RichPickResponse)
async def get_rich_pick(
    session: AsyncSession = Depends(get_mysql_session_router), redis_client: Redis = Depends(get_redis_pool)
) -> RichPickResponse:
    top_10_stock_codes, stock_name_map = await RichFacade.get_rich_top_10_pick(session, redis_client)
    lastest_stock_daily_map = await StockDailyService.get_latest_map_by_codes(session, top_10_stock_codes)
    current_stock_price_map: dict[str, float] = await StockService.get_current_stock_price_by_code(
        redis_client, lastest_stock_daily_map, top_10_stock_codes
    )
    exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)
    stock_daily_profit: dict[str, float] = StockService.get_daily_profit(
        lastest_stock_daily_map, current_stock_price_map, top_10_stock_codes
    )
    won_exchange_rate = ExchangeRateService.get_exchange_rate(CurrencyType.USA, CurrencyType.KOREA, exchange_rate_map)
    stock_korea_price = {stock_code: price * won_exchange_rate for stock_code, price in current_stock_price_map.items()}

    return RichPickResponse(
        [
            RichPickValue(
                name=stock_name_map.get(stock_code),
                price=stock_korea_price[stock_code],
                rate=stock_daily_profit[stock_code],
            )
            for stock_code in top_10_stock_codes
        ]
    )
