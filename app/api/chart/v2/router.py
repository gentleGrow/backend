from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.module.asset.dependencies.asset_dependency import get_asset_query, get_asset_service
from app.module.asset.dependencies.realtime_index_dependency import get_realtime_index_service
from app.module.asset.enum import AssetType, MarketIndex
from app.module.asset.services.asset.asset_query import AssetQuery
from app.module.asset.services.asset.asset_service import AssetService
from app.module.asset.services.realtime_index_service import RealtimeIndexService
from app.module.auth.constant import DUMMY_USER_ID
from app.module.auth.schema import AccessToken
from app.module.chart.dependencies.performance_analysis_dependency import get_performance_analysis_service
from app.module.chart.enum import IntervalTypeV2
from app.module.chart.schema import PerformanceAnalysisResponse
from app.module.chart.services.performance_analysis_service import PerformanceAnalysisService
from database.dependency import get_mysql_session_router, get_redis_pool

chart_router = APIRouter(prefix="/v2")


@chart_router.get("/sample/performance-analysis", summary="더미 투자 성과 분석", response_model=PerformanceAnalysisResponse)
async def get_sample_performance_analysis(
    interval: IntervalTypeV2 = Query(IntervalTypeV2.ONEMONTH, description="기간 별, 투자 성관 분석 데이터가 제공 됩니다."),
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
        stock_daily_map,
        exchange_rate_map,
        current_stock_price_map,
        interval,
    )

    return PerformanceAnalysisResponse.parse(market_analysis_data, user_analysis_data, interval_times, interval)


@chart_router.get("/performance-analysis", summary="투자 성과 분석", response_model=PerformanceAnalysisResponse)
async def get_performance_analysis(
    token: AccessToken = Depends(verify_jwt_token),
    interval: IntervalTypeV2 = Query(IntervalTypeV2.ONEMONTH, description="기간 별, 투자 성관 분석 데이터가 제공 됩니다."),
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
        stock_daily_map,
        exchange_rate_map,
        current_stock_price_map,
        interval,
    )

    return PerformanceAnalysisResponse.parse(market_analysis_data, user_analysis_data, interval_times, interval)
