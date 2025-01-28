from datetime import date

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from app.common.auth.security import verify_jwt_token
from app.module.asset.constant import ASSET_SAVE_TREND_YEAR, RICH_PEOPLE_DATA_KEY, RICH_TOP_PICK_NUM
from app.module.asset.dependencies.asset_dependency import get_asset_query, get_asset_service
from app.module.asset.dependencies.dividend_dependency import get_dividend_service
from app.module.asset.dependencies.realtime_index_dependency import get_realtime_index_service
from app.module.asset.enum import AssetType, MarketIndex
from app.module.asset.schema import MarketIndexData, StockAssetSchema
from app.module.asset.services.asset.asset_query import AssetQuery
from app.module.asset.services.asset.asset_service import AssetService
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.realtime_index_service import RealtimeIndexService
from app.module.auth.constant import DUMMY_USER_ID
from app.module.auth.schema import AccessToken
from app.module.chart.constant import DEFAULT_TIP
from app.module.chart.dependencies.composition_dependency import get_composition_service
from app.module.chart.dependencies.performance_analysis_dependency import get_performance_analysis_service
from app.module.chart.dependencies.rich_dependency import get_rich_service
from app.module.chart.dependencies.save_trend_dependency import get_save_trend_service
from app.module.chart.dependencies.summary_dependency import get_summary_service
from app.module.chart.enum import CompositionType, EstimateDividendType, IntervalType
from app.module.chart.schema import (
    AssetSaveTrendResponse,
    ChartTipResponse,
    CompositionResponse,
    EstimateDividendEveryResponse,
    EstimateDividendEveryValue,
    EstimateDividendTypeResponse,
    EstimateDividendTypeValue,
    MarketIndiceResponse,
    MyStockResponse,
    MyStockResponseValue,
    PeoplePortfolioResponse,
    PeoplePortfolioValue,
    PerformanceAnalysisResponse,
    PortfolioStockData,
    ProfitDetail,
    RichPickResponse,
    RichPortfolioResponse,
    SummaryResponse,
)
from app.module.chart.services.composition_service import CompositionService
from app.module.chart.services.performance_analysis_service import PerformanceAnalysisService
from app.module.chart.services.rich_service import RichService
from app.module.chart.services.save_trend_service import SaveTrendService
from app.module.chart.services.summary_service import SummaryService
from database.dependency import get_mysql_session_router, get_redis_pool


chart_router = APIRouter(prefix="/v1")


@chart_router.get("/sample/asset-save-trend", summary="자산적립 추이", response_model=AssetSaveTrendResponse)
async def get_sample_asset_save_trend(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    save_trend_service: SaveTrendService = Depends(get_save_trend_service),
) -> AssetSaveTrendResponse:
    assets = await asset_query.get_full_required_assets(session, DUMMY_USER_ID, AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, DUMMY_USER_ID)

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)

    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    total_asset_amount = asset_service.get_total_asset_amount(
        complete_buy_asset, current_stock_price_map, exchange_rate_map
    )

    validate_response = await AssetSaveTrendResponse.validate(complete_buy_asset, total_asset_amount)
    if validate_response:
        return validate_response

    estimate_asset_amount, real_asset_amount, unit = asset_service.get_asset_trend_values(
        complete_buy_asset,
        stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
        ASSET_SAVE_TREND_YEAR,
    )

    return AssetSaveTrendResponse(
        xAxises=save_trend_service.get_x_axises(ASSET_SAVE_TREND_YEAR),
        dates=save_trend_service.get_dates(ASSET_SAVE_TREND_YEAR),
        values1=estimate_asset_amount,
        values2=real_asset_amount,
        unit=unit,
    )


@chart_router.get("/asset-save-trend", summary="자산적립 추이", response_model=AssetSaveTrendResponse)
async def get_asset_save_trend(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    save_trend_service: SaveTrendService = Depends(get_save_trend_service),
) -> AssetSaveTrendResponse:
    assets = await asset_query.get_full_required_assets(session, token.get("user"), AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, token.get("user"))

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    total_asset_amount = asset_service.get_total_asset_amount(
        complete_buy_asset, current_stock_price_map, exchange_rate_map
    )

    validate_response = await AssetSaveTrendResponse.validate(complete_buy_asset, total_asset_amount)
    if validate_response:
        return validate_response

    estimate_asset_amount, real_asset_amount, unit = asset_service.get_asset_trend_values(
        complete_buy_asset,
        stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
        ASSET_SAVE_TREND_YEAR,
    )

    return AssetSaveTrendResponse(
        xAxises=save_trend_service.get_x_axises(ASSET_SAVE_TREND_YEAR),
        dates=save_trend_service.get_dates(ASSET_SAVE_TREND_YEAR),
        values1=estimate_asset_amount,
        values2=real_asset_amount,
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
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    dividend_service: DividendService = Depends(get_dividend_service),
) -> EstimateDividendEveryResponse | EstimateDividendTypeResponse:
    assets = await asset_query.get_full_required_assets(session, DUMMY_USER_ID, AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        recent_dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, DUMMY_USER_ID)
    dividend_map: dict[tuple[str, date], float] = await dividend_service.get_dividend_map(session, assets)

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    if category == EstimateDividendType.EVERY:
        no_asset_response = EstimateDividendEveryResponse.validate(complete_buy_asset)
        if no_asset_response:
            return no_asset_response
    else:
        no_asset_response = EstimateDividendTypeResponse.validate(complete_buy_asset)
        if no_asset_response:
            return no_asset_response

    if category == EstimateDividendType.EVERY:
        every_dividend_data: dict[str, EstimateDividendEveryValue] = dividend_service.get_dividend_every_chart_data(
            complete_buy_asset, exchange_rate_map, dividend_map
        )
        return EstimateDividendEveryResponse(every_dividend_data)
    else:
        type_dividend_data: list[EstimateDividendTypeValue] = await dividend_service.get_composition(
            complete_buy_asset, exchange_rate_map, recent_dividend_map
        )

        return EstimateDividendTypeResponse(type_dividend_data)


@chart_router.get(
    "/estimate-dividend", summary="예상 배당액", response_model=EstimateDividendEveryResponse | EstimateDividendTypeResponse
)
async def get_estimate_dividend(
    token: AccessToken = Depends(verify_jwt_token),
    category: EstimateDividendType = Query(EstimateDividendType.EVERY, description="every는 모두, type은 종목 별 입니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    dividend_service: DividendService = Depends(get_dividend_service),
) -> EstimateDividendEveryResponse | EstimateDividendTypeResponse:
    assets = await asset_query.get_full_required_assets(session, token.get("user"), AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        recent_dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, token.get("user"))
    dividend_map: dict[tuple[str, date], float] = await dividend_service.get_dividend_map(session, assets)

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    if category == EstimateDividendType.EVERY:
        no_asset_response = EstimateDividendEveryResponse.validate(complete_buy_asset)
        if no_asset_response:
            return no_asset_response
    else:
        no_asset_response = EstimateDividendTypeResponse.validate(complete_buy_asset)
        if no_asset_response:
            return no_asset_response

    if category == EstimateDividendType.EVERY:
        every_dividend_data: dict[str, EstimateDividendEveryValue] = dividend_service.get_dividend_every_chart_data(
            complete_buy_asset, exchange_rate_map, dividend_map
        )
        return EstimateDividendEveryResponse(every_dividend_data)
    else:
        type_dividend_data: list[EstimateDividendTypeValue] = await dividend_service.get_composition(
            complete_buy_asset, exchange_rate_map, recent_dividend_map
        )

        return EstimateDividendTypeResponse(type_dividend_data)


@chart_router.get("/sample/composition", summary="종목 구성", response_model=CompositionResponse)
async def get_sample_composition(
    type: CompositionType = Query(CompositionType.COMPOSITION, description="composition은 종목 별, account는 계좌 별 입니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    composition_service: CompositionService = Depends(get_composition_service),
) -> CompositionResponse:
    assets = await asset_query.get_full_required_assets(session, DUMMY_USER_ID, AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, DUMMY_USER_ID)

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    no_asset_response = CompositionResponse.validate(complete_buy_asset)
    if no_asset_response:
        return no_asset_response

    if type is CompositionType.COMPOSITION:
        stock_composition_data = composition_service.get_asset_stock_composition(
            complete_buy_asset, current_stock_price_map, exchange_rate_map
        )
        return CompositionResponse(stock_composition_data)
    else:
        account_composition_data = composition_service.get_asset_stock_account(
            complete_buy_asset, current_stock_price_map, exchange_rate_map
        )

        return CompositionResponse(account_composition_data)


@chart_router.get("/composition", summary="종목 구성", response_model=CompositionResponse)
async def get_composition(
    token: AccessToken = Depends(verify_jwt_token),
    type: CompositionType = Query(CompositionType.COMPOSITION, description="composition은 종목 별, account는 계좌 별 입니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    composition_service: CompositionService = Depends(get_composition_service),
) -> CompositionResponse:
    assets = await asset_query.get_full_required_assets(session, token.get("user"), AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, token.get("user"))

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    no_asset_response = CompositionResponse.validate(complete_buy_asset)
    if no_asset_response:
        return no_asset_response

    if type is CompositionType.COMPOSITION:
        stock_composition_data = composition_service.get_asset_stock_composition(
            complete_buy_asset, current_stock_price_map, exchange_rate_map
        )
        return CompositionResponse(stock_composition_data)
    else:
        account_composition_data = composition_service.get_asset_stock_account(
            complete_buy_asset, current_stock_price_map, exchange_rate_map
        )

        return CompositionResponse(account_composition_data)


@chart_router.get("/sample/performance-analysis", summary="더미 투자 성과 분석", response_model=PerformanceAnalysisResponse)
async def get_sample_performance_analysis(
    interval: IntervalType = Query(IntervalType.ONEMONTH, description="기간 별, 투자 성관 분석 데이터가 제공 됩니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    asset_query: AssetQuery = Depends(get_asset_query),
    realtime_index_service: RealtimeIndexService = Depends(get_realtime_index_service),
    asset_service: AssetService = Depends(get_asset_service),
    redis_client: Redis = Depends(get_redis_pool),
    performance_analysis_service: PerformanceAnalysisService = Depends(get_performance_analysis_service),
) -> PerformanceAnalysisResponse:
    assets = await asset_query.get_full_required_assets(session, DUMMY_USER_ID, AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, DUMMY_USER_ID)

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    no_len_response = PerformanceAnalysisResponse.validate(complete_buy_asset)
    if no_len_response:
        return no_len_response

    current_kospi_price = await realtime_index_service.get_current_index_price(redis_client, MarketIndex.KOSPI)
    (
        market_analysis_data,
        user_analysis_data,
        interval_times,
    ) = await performance_analysis_service.performance_analysis_chart_data(
        complete_buy_asset,
        session,
        current_kospi_price,
        exchange_rate_map,
        current_stock_price_map,
        interval,
    )

    return PerformanceAnalysisResponse.parse(market_analysis_data, user_analysis_data, interval_times, interval)


@chart_router.get("/performance-analysis", summary="투자 성과 분석", response_model=PerformanceAnalysisResponse)
async def get_performance_analysis(
    token: AccessToken = Depends(verify_jwt_token),
    interval: IntervalType = Query(IntervalType.ONEMONTH, description="기간 별, 투자 성관 분석 데이터가 제공 됩니다."),
    session: AsyncSession = Depends(get_mysql_session_router),
    asset_query: AssetQuery = Depends(get_asset_query),
    realtime_index_service: RealtimeIndexService = Depends(get_realtime_index_service),
    asset_service: AssetService = Depends(get_asset_service),
    redis_client: Redis = Depends(get_redis_pool),
    performance_analysis_service: PerformanceAnalysisService = Depends(get_performance_analysis_service),
) -> PerformanceAnalysisResponse:
    assets = await asset_query.get_full_required_assets(session, token.get("user"), AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, token.get("user"))

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    no_len_response = PerformanceAnalysisResponse.validate(complete_buy_asset)
    if no_len_response:
        return no_len_response

    current_kospi_price = await realtime_index_service.get_current_index_price(redis_client, MarketIndex.KOSPI)

    (
        market_analysis_data,
        user_analysis_data,
        interval_times,
    ) = await performance_analysis_service.performance_analysis_chart_data(
        complete_buy_asset,
        session,
        current_kospi_price,
        exchange_rate_map,
        current_stock_price_map,
        interval,
    )

    return PerformanceAnalysisResponse.parse(market_analysis_data, user_analysis_data, interval_times, interval)


@chart_router.get("/sample/my-stock", summary="내 보유 주식", response_model=MyStockResponse)
async def get_sample_my_stock(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_query: AssetQuery = Depends(get_asset_query),
    asset_service: AssetService = Depends(get_asset_service),
) -> MyStockResponse:
    assets = await asset_query.get_full_required_assets(session, DUMMY_USER_ID, AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, DUMMY_USER_ID)

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    stock_assets: list[StockAssetSchema] = asset_service.get_stock_assets(
        complete_buy_asset,
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
        always_won=True,
    )

    return MyStockResponse(
        [
            MyStockResponseValue(
                name=stock_asset.종목명,
                current_price=stock_asset.현재가,
                profit_rate=stock_asset.수익률,
                profit_amount=stock_asset.수익금,
                quantity=stock_asset.수량,
            )
            for stock_asset in stock_assets
        ]
    )


@chart_router.get("/my-stock", summary="내 보유 주식", response_model=MyStockResponse)
async def get_my_stock(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_query: AssetQuery = Depends(get_asset_query),
    asset_service: AssetService = Depends(get_asset_service),
) -> MyStockResponse:
    assets = await asset_query.get_full_required_assets(session, token.get("user"), AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, token.get("user"))

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    stock_assets: list[StockAssetSchema] = asset_service.get_stock_assets(
        complete_buy_asset,
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
        always_won=True,
    )

    return MyStockResponse(
        [
            MyStockResponseValue(
                name=stock_asset.종목명,
                current_price=stock_asset.현재가,
                profit_rate=stock_asset.수익률,
                profit_amount=stock_asset.수익금,
                quantity=stock_asset.수량,
            )
            for stock_asset in stock_assets
        ]
    )


@chart_router.get("/indice", summary="현재 시장 지수", response_model=MarketIndiceResponse)
async def get_market_index(
    redis_client: Redis = Depends(get_redis_pool),
    realtime_index_service: RealtimeIndexService = Depends(get_realtime_index_service),
) -> MarketIndiceResponse:
    market_index_data: list[MarketIndexData] = await realtime_index_service.get_current_market_index_value(redis_client)

    return MarketIndiceResponse(market_index_data)


@chart_router.get("/summary", summary="오늘의 리뷰, 나의 총자산, 나의 투자 금액, 수익금", response_model=SummaryResponse)
async def get_summary(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_query: AssetQuery = Depends(get_asset_query),
    asset_service: AssetService = Depends(get_asset_service),
    summary_service: SummaryService = Depends(get_summary_service),
) -> SummaryResponse:
    assets = await asset_query.get_full_required_assets(session, token.get("user"), AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, token.get("user"))

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    no_asset_response = SummaryResponse.validate(complete_buy_asset)
    if no_asset_response:
        return no_asset_response

    past_stock_map = await summary_service.get_past_stock_map(session, complete_buy_asset, lastest_stock_daily_map)

    total_asset_amount = asset_service.get_total_asset_amount(
        complete_buy_asset, current_stock_price_map, exchange_rate_map
    )

    total_investment_amount = asset_service.get_total_investment_amount(
        complete_buy_asset, stock_daily_map, exchange_rate_map
    )

    today_review_rate, increase_asset_amount = summary_service.get_today_review_rate(
        complete_buy_asset, current_stock_price_map, exchange_rate_map, past_stock_map
    )

    # [TODO] 협의 후 바로 추가할 인자입니다.
    return SummaryResponse(
        # increase_asset_amount=increase_asset_amount,
        today_review_rate=today_review_rate,
        total_asset_amount=total_asset_amount,
        total_investment_amount=total_investment_amount,
        profit=ProfitDetail.parse(total_asset_amount, total_investment_amount),
    )


@chart_router.get("/sample/summary", summary="오늘의 리뷰, 나의 총자산, 나의 투자 금액, 수익금", response_model=SummaryResponse)
async def get_sample_summary(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    asset_service: AssetService = Depends(get_asset_service),
    asset_query: AssetQuery = Depends(get_asset_query),
    summary_service: SummaryService = Depends(get_summary_service),
) -> SummaryResponse:
    assets = await asset_query.get_full_required_assets(session, DUMMY_USER_ID, AssetType.STOCK)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, DUMMY_USER_ID)

    complete_asset, incomplete_assets = asset_service.separate_assets_by_full_data(assets, stock_daily_map)
    complete_buy_asset = asset_service.get_buy_assets(complete_asset)

    no_asset_response = SummaryResponse.validate(complete_buy_asset)
    if no_asset_response:
        return no_asset_response

    past_stock_map = await summary_service.get_past_stock_map(session, complete_buy_asset, lastest_stock_daily_map)

    total_asset_amount = asset_service.get_total_asset_amount(
        complete_buy_asset, current_stock_price_map, exchange_rate_map
    )

    total_investment_amount = asset_service.get_total_investment_amount(
        complete_buy_asset, stock_daily_map, exchange_rate_map
    )

    today_review_rate, increase_asset_amount = summary_service.get_today_review_rate(
        complete_buy_asset, current_stock_price_map, exchange_rate_map, past_stock_map
    )

    # [TODO] 협의 후 바로 추가할 인자입니다.
    return SummaryResponse(
        # increase_asset_amount=increase_asset_amount,
        today_review_rate=today_review_rate,
        total_asset_amount=total_asset_amount,
        total_investment_amount=total_investment_amount,
        profit=ProfitDetail.parse(total_asset_amount, total_investment_amount),
    )


# [TODO] 삭제될 예정입니다.
@chart_router.get("/tip", summary="오늘의 투자 tip", response_model=ChartTipResponse)
async def get_today_tip() -> ChartTipResponse:
    return ChartTipResponse(DEFAULT_TIP)


@chart_router.get("/rich-portfolio", summary="부자들의 포트폴리오", response_model=RichPortfolioResponse)
async def get_rich_portfolio(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    rich_service: RichService = Depends(get_rich_service),
) -> RichPortfolioResponse:
    rich_portfolio_list = await rich_service.get_rich_portfolio_chart_data(session, redis_client)
    
    return RichPortfolioResponse(rich_portfolio_list)


@chart_router.get("/rich-pick", summary="미국 부자들이 선택한 종목 TOP10", response_model=RichPickResponse)
async def get_rich_pick(
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
    rich_service: RichService = Depends(get_rich_service),
    asset_query: AssetQuery = Depends(get_asset_query),
) -> RichPickResponse:
    assets = await rich_service.get_full_rich_assets(session)

    (
        stock_daily_map,
        lastest_stock_daily_map,
        dividend_map,
        exchange_rate_map,
        current_stock_price_map,
    ) = await asset_query.get_user_data(session, redis_client, assets, RICH_PEOPLE_DATA_KEY)

    top_rich_pick_list = rich_service.get_top_rich_pick(
        assets, RICH_TOP_PICK_NUM, current_stock_price_map, exchange_rate_map, stock_daily_map
    )

    return RichPickResponse(top_rich_pick_list)


# [TODO] 임시 dummy api 생성, 추후 개발하겠습니다.
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



