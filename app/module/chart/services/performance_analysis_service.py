from collections import defaultdict
from datetime import date, datetime, timedelta
from math import floor

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.enum import AssetType, MarketIndex
from app.module.asset.model import Asset, MarketIndexMinutely, StockDaily
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.index_daily_service import IndexDailyService
from app.module.asset.services.index_minutely_service import IndexMinutelyService
from app.module.asset.services.realtime_index_service import RealtimeIndexService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_minutely_service import StockMinutelyService
from app.module.asset.services.stock_service import StockService
from app.module.chart.enum import IntervalType


class PerformanceAnalysisService:
    def __init__(
        self,
        exchange_rate_service: ExchangeRateService,
        realtime_index_service: RealtimeIndexService,
        index_daily_service: IndexDailyService,
        index_minutely_service: IndexMinutelyService,
        stock_service: StockService,
        stock_daily_service: StockDailyService,
        stock_minutely_service: StockMinutelyService,
        asset_service: AssetService,
        asset_stock_service: AssetStockService,
    ):
        self.exchange_rate_service = exchange_rate_service
        self.realtime_index_service = realtime_index_service
        self.index_daily_service = index_daily_service
        self.index_minutely_service = index_minutely_service
        self.stock_service = stock_service
        self.stock_daily_service = stock_daily_service
        self.stock_minutely_service = stock_minutely_service
        self.asset_service = asset_service
        self.asset_stock_service = asset_stock_service

    async def get_market_analysis(
        self, session: AsyncSession, redis_client: Redis, start_date: date, end_date: date
    ) -> dict[date, float]:
        adjusted_start_date = start_date - timedelta(days=7)
        market_index_date_map = await self.index_daily_service.get_market_index_date_map(
            session, (adjusted_start_date, end_date), MarketIndex.KOSPI
        )
        current_kospi_price = await self.realtime_index_service.get_current_index_price(redis_client, MarketIndex.KOSPI)
        result = {}
        current_profit = 0.0
        current_date = adjusted_start_date

        while current_date <= end_date:
            if current_date in market_index_date_map:
                market_index = market_index_date_map[current_date]
                current_profit = ((current_kospi_price - market_index.close_price) / market_index.close_price) * 100

            if current_date > start_date:
                result[current_date] = current_profit
            current_date += timedelta(days=1)

        return result

    async def get_user_analysis(
        self,
        session: AsyncSession,
        redis_client: Redis,
        interval_start: date,
        interval_end: date,
        user_id: int,
        market_analysis_result: dict[date, float],
    ) -> dict[date, float]:
        assets = await AssetRepository.get_eager_by_range(
            session, user_id, AssetType.STOCK, (interval_start, interval_end)
        )

        stock_daily_map: dict[tuple[str, date], StockDaily] = await self.stock_daily_service.get_map_range(
            session,
            assets,
        )
        latest_stock_daily_map: dict[str, StockDaily] = await self.stock_daily_service.get_latest_map(session, assets)
        current_stock_price_map = await self.stock_service.get_current_stock_price_by_code(
            redis_client, latest_stock_daily_map, [asset.asset_stock.stock.code for asset in assets]
        )
        exchange_rate_map = await self.exchange_rate_service.get_exchange_rate_map(redis_client)

        assets_by_date = defaultdict(list)
        for asset in assets:
            assets_by_date[asset.asset_stock.trade_date].append(asset)

        cumulative_assets = []
        result = {}

        current_profit = 0.0

        for market_date in sorted(market_analysis_result):
            if market_date in assets_by_date:
                assets_for_date = assets_by_date[market_date]
                cumulative_assets.extend(assets_for_date)

                total_asset_amount = self.asset_stock_service.get_total_asset_amount(
                    cumulative_assets, current_stock_price_map, exchange_rate_map
                )
                total_invest_amount = self.asset_stock_service.get_total_investment_amount(
                    cumulative_assets, stock_daily_map, exchange_rate_map
                )
                current_profit = (
                    ((total_asset_amount - total_invest_amount) / total_invest_amount) * 100
                    if total_invest_amount > 0.0 and total_asset_amount > 0.0
                    else 0.0
                )
                result[market_date] = (
                    ((total_asset_amount - total_invest_amount) / total_invest_amount) * 100
                    if total_invest_amount > 0.0 and total_asset_amount > 0.0
                    else 0.0
                )
            else:
                result[market_date] = current_profit

        return result

    async def get_user_analysis_single_month(
        self,
        session: AsyncSession,
        redis_client: Redis,
        user_id: int,
        interval: IntervalType,
        market_analysis_result: dict[date, float],
    ) -> dict[date, float]:
        assets: list[Asset] = await AssetRepository.get_eager(session, user_id, AssetType.STOCK)
        assets_by_date: dict = self.asset_service.asset_list_from_days(assets, interval.get_days())
        exchange_rate_map = await self.exchange_rate_service.get_exchange_rate_map(redis_client)

        # 7일 정도 더 date을 추가해야만, 주말과 긴 공휴일이 있는 날에 데이터가 없는 경우인 상황을 회피합니다.
        dates = sorted(market_analysis_result.keys())
        if dates:
            oldest_date = dates[0]
            previous_dates = [oldest_date - timedelta(days=i) for i in range(1, 8)]
            dates = previous_dates + dates

        sorted_dates = sorted(dates)

        stock_daily_date_map = await self.stock_daily_service.get_date_map_dates(session, assets, sorted_dates)

        result = {}

        for market_date in sorted(market_analysis_result):
            if market_date not in assets_by_date:
                continue
            current_assets = assets_by_date[market_date]
            current_investment_amount = await self.asset_service.get_total_investment_amount(
                session, redis_client, current_assets
            )
            if current_assets is None or current_investment_amount == 0.0:
                result[market_date] = 0.0
                continue

            currnet_total_amount = self.asset_service.get_total_asset_amount_with_date_with_map(
                current_assets, exchange_rate_map, stock_daily_date_map, market_date
            )

            current_profit_rate = ((currnet_total_amount - current_investment_amount) / current_investment_amount) * 100

            result[market_date] = current_profit_rate

        return result

    async def get_user_analysis_short(
        self,
        session: AsyncSession,
        redis_client: Redis,
        interval_start: datetime,
        interval_end: datetime,
        user_id: int,
        interval: IntervalType,
        market_analysis_result: dict[datetime, float],
    ) -> dict[datetime, float]:
        assets: list[Asset] = await AssetRepository.get_eager(session, user_id, AssetType.STOCK)
        stock_datetime_price_map = await self.stock_minutely_service.get_datetime_interval_map(
            session, interval_start, interval_end, assets, interval.get_interval()
        )

        assets_by_date: dict = self.asset_service.asset_list_from_days(assets, interval.get_days())
        exchange_rate_map = await self.exchange_rate_service.get_exchange_rate_map(redis_client)
        stock_daily_map = await self.stock_daily_service.get_map_range(session, assets)

        result = {}
        current_assets = None
        current_investment_amount = None

        for market_datetime in sorted(market_analysis_result):
            if market_datetime.date() not in assets_by_date:
                continue

            current_loop_assets = assets_by_date[market_datetime.date()]
            if current_assets is not current_loop_assets:
                current_assets = current_loop_assets
                current_investment_amount = await self.asset_service.get_total_investment_amount(
                    session, redis_client, current_assets
                )
            if current_assets is None or current_investment_amount is None:
                result[market_datetime] = 0.0
                continue

            currnet_total_amount = self.asset_service.get_total_asset_amount_with_datetime(
                current_assets, exchange_rate_map, stock_datetime_price_map, market_datetime, stock_daily_map
            )

            current_profit_rate = 0.0

            if current_investment_amount > 0:
                current_profit_rate = (
                    (currnet_total_amount - current_investment_amount) / current_investment_amount
                ) * 100

            result[market_datetime] = current_profit_rate

        return result

    async def get_market_analysis_short(
        self,
        session: AsyncSession,
        redis_client: Redis,
        interval_start: datetime,
        interval_end: datetime,
        interval: IntervalType,
    ) -> dict[datetime, float]:
        market_index_minutely_map: dict[
            datetime, MarketIndexMinutely
        ] = await self.index_minutely_service.get_index_range_interval_map(
            session, MarketIndex.KOSPI, (interval_start, interval_end), interval
        )
        current_kospi_price = await self.realtime_index_service.get_current_index_price(redis_client, MarketIndex.KOSPI)

        result = {}

        minutes_offset = interval_start.minute % interval.get_interval()

        if minutes_offset != 0:
            adjusted_minutes = floor(interval_start.minute / interval.get_interval()) * interval.get_interval()
            interval_start = interval_start.replace(minute=adjusted_minutes, second=0, microsecond=0)

        current_datetime = interval_start

        current_profit = 0.0

        while current_datetime <= interval_end:
            if current_datetime.weekday() in [5, 6]:
                current_datetime += timedelta(minutes=interval.get_interval())
                continue

            naive_current_datetime = current_datetime.replace(tzinfo=None)
            if naive_current_datetime in market_index_minutely_map:
                market_index = market_index_minutely_map[naive_current_datetime]
                current_profit = ((current_kospi_price - market_index.current_price) / market_index.current_price) * 100

            result[naive_current_datetime] = current_profit
            current_datetime += timedelta(minutes=interval.get_interval())

        return result
