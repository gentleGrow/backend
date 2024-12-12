from collections import defaultdict
from datetime import date, datetime
from statistics import mean

from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from app.module.asset.enum import MarketIndex
from app.module.asset.model import Asset, MarketIndexDaily, MarketIndexMinutely, StockDaily
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

    async def performance_analysis_chart_data(
        self,
        assets: list[Asset],
        session: AsyncSession,
        current_index_price: float,
        stock_daily_map,
        exchange_rate_map,
        current_stock_price_map,
        interval: IntervalType,
    ) -> tuple[dict[datetime, float], dict[datetime, float], list[datetime]] | tuple[
        dict[date, float], dict[date, float], list[date]
    ]:
        if interval is IntervalType.FIVEDAY:
            interval_datetimes = interval.get_chart_datetime_interval()
            market_index_minutely_map: dict[
                datetime, MarketIndexMinutely
            ] = await self.index_minutely_service.get_index_range_map(
                session, MarketIndex.KOSPI, (interval_datetimes[0], interval_datetimes[-1])
            )
            stock_datetime_price_map: dict[
                tuple[str, datetime], float
            ] = await self.stock_minutely_service.get_datetime_interval_map(
                session, interval_datetimes[0], interval_datetimes[-1], assets
            )

            market_analysis_data_short: dict[datetime, float] = self._get_market_analysis_short(
                market_index_minutely_map, current_index_price, interval_datetimes, interval.get_interval()
            )

            user_analysis_data_short: dict[datetime, float] = self._get_user_analysis_short(
                assets,
                stock_daily_map,
                stock_datetime_price_map,
                exchange_rate_map,
                interval_datetimes,
                current_stock_price_map,
                interval.get_interval(),
            )

            return market_analysis_data_short, user_analysis_data_short, interval_datetimes
        elif interval is IntervalType.ONEMONTH:
            interval_dates = interval.get_chart_date_interval()
            market_index_date_map = await self.index_daily_service.get_market_index_date_map(
                session, (interval_dates[0], interval_dates[-1]), MarketIndex.KOSPI
            )

            target_dates = self._get_target_dates(assets, interval_dates)

            stock_daily_map_full = await self.stock_daily_service.get_date_map_dates(session, assets, target_dates)

            market_analysis_data_days: dict[date, float] = self._get_market_analysis_days(
                market_index_date_map, current_index_price, interval_dates
            )
            
            user_analysis_data_days: dict[date, float] = self._get_user_analysis_days(
                assets, stock_daily_map_full, current_stock_price_map, exchange_rate_map, interval_dates
            )

            return market_analysis_data_days, user_analysis_data_days, interval_dates
        else:
            interval_dates = interval.get_chart_month_interval()
            
            market_index_date_map = await self.index_daily_service.get_market_index_date_map(
                session, (interval_dates[0], interval_dates[-1]), MarketIndex.KOSPI
            )

            target_dates = self._get_target_dates(assets, interval_dates)
            stock_daily_map_full = await self.stock_daily_service.get_date_map_dates(session, assets, target_dates)

            market_analysis_data: dict[tuple[int, int], float] = self._get_market_analysis(
                market_index_date_map, current_index_price, interval_dates
            )
            
            user_analysis_data: dict[tuple[int, int], float] = self._get_user_analysis(
                assets, stock_daily_map_full, current_stock_price_map, exchange_rate_map, interval_dates
            )

            return market_analysis_data, user_analysis_data, interval_dates
        
        
    def _get_user_analysis(
        self,
        assets: list[Asset],
        stock_daily_map: dict[tuple[str, date], StockDaily],
        current_stock_price_map: dict[str, float],
        exchange_rate_map: dict[str, float],
        interval_dates: list[date],
    ) -> dict[tuple[int, int], float]:
        assets_by_date = defaultdict(list)
        for asset in assets:
            assets_by_date[asset.asset_stock.trade_date].append(asset)
        current_assets = [asset for asset in assets if asset.asset_stock.trade_date <= interval_dates[0]]

        avg_profits = defaultdict(list)

        for interval_date in interval_dates:
            if interval_date in assets_by_date:
                interval_assets = assets_by_date[interval_date]
                current_assets.extend(interval_assets)

            interval_stock_price_map = self._get_date_interval_stock_price_map(
                current_assets, interval_date, stock_daily_map, current_stock_price_map
            )
            total_asset_amount = self.asset_stock_service.get_total_asset_amount(
                current_assets, interval_stock_price_map, exchange_rate_map
            )
            total_invest_amount = self.asset_stock_service.get_total_investment_amount(
                current_assets, stock_daily_map, exchange_rate_map
            )
            total_profit = self.asset_stock_service.get_total_profit_rate(
                            total_asset_amount, total_invest_amount
                        )

            avg_profits[(interval_date.year, interval_date.month)].append(total_profit)

        return {year_month: mean(profits) for year_month, profits in avg_profits.items()} 
    
    def _get_target_dates(self, assets: list[Asset], interval_dates: list[date]) -> list[date]:
        result = interval_dates.copy()
        oldest_date = result[0]
        for asset in assets:
            if asset.asset_stock.trade_date < oldest_date:
                result.append(asset.asset_stock.trade_date)
        return result
    
    
    def _get_market_analysis(
        self,
        market_index_date_map: dict[date, MarketIndexDaily],
        current_index_price: float,
        interval_dates: list[date],
    ) -> dict[tuple[int, int], float]:
        avg_profits = defaultdict(list)
        current_profit = 0.0

        for interval_date in interval_dates:
            if interval_date in market_index_date_map:
                market_index = market_index_date_map[interval_date]
                current_profit = self.asset_stock_service.get_total_profit_rate(
                    current_index_price, market_index.close_price
                )
                
                avg_profits[(interval_date.year, interval_date.month)].append(current_profit)
        
        return {year_month: mean(profits) for year_month, profits in avg_profits.items()}


    def _get_market_analysis_days(
        self,
        market_index_date_map: dict[date, MarketIndexDaily],
        current_index_price: float,
        interval_dates: list[date],
    ) -> dict[date, float]:
        result = {}
        current_profit = 0.0

        for interval_date in interval_dates:
            if interval_date in market_index_date_map:
                market_index = market_index_date_map[interval_date]
                current_profit = ((current_index_price - market_index.close_price) / market_index.close_price) * 100
                result[interval_date] = current_profit
            else:
                result[interval_date] = current_profit

        return result

    def _get_user_analysis_days(
        self,
        assets: list[Asset],
        stock_daily_map: dict[tuple[str, date], StockDaily],
        current_stock_price_map: dict[str, float],
        exchange_rate_map: dict[str, float],
        interval_dates: list[date],
    ) -> dict[date, float]:
        assets_by_date = defaultdict(list)
        for asset in assets:
            assets_by_date[asset.asset_stock.trade_date].append(asset)
        current_assets = [asset for asset in assets if asset.asset_stock.trade_date <= interval_dates[0]]

        result = {}

        for interval_date in interval_dates:
            if interval_date in assets_by_date:
                interval_assets = assets_by_date[interval_date]
                current_assets.extend(interval_assets)

            interval_stock_price_map = self._get_date_interval_stock_price_map(
                current_assets, interval_date, stock_daily_map, current_stock_price_map
            )
            total_asset_amount = self.asset_stock_service.get_total_asset_amount(
                current_assets, interval_stock_price_map, exchange_rate_map
            )

            total_invest_amount = self.asset_stock_service.get_total_investment_amount(
                current_assets, stock_daily_map, exchange_rate_map
            )

            result[interval_date] = self.asset_stock_service.get_total_profit_rate(
                total_asset_amount, total_invest_amount
            )

        return result

    def _get_date_interval_stock_price_map(
        self,
        assets: list[Asset],
        interval_date: date,
        stock_daily_map: dict[tuple[str, date], StockDaily],
        current_stock_price_map: dict[str, float],
    ) -> dict[str, float]:
        result = {}
        for asset in assets:
            code = asset.asset_stock.stock.code
            current_price = stock_daily_map.get((asset.asset_stock.stock.code, interval_date), None)
            result[code] = current_price.adj_close_price if current_price else current_stock_price_map.get(code)

        return result

    def _get_user_analysis_short(
        self,
        assets: list[Asset],
        stock_daily_map: dict[tuple[str, date], StockDaily],
        stock_datetime_price_map: dict[tuple[str, datetime], float],
        exchange_rate_map: dict[str, float],
        interval_datetimes: list[datetime],
        current_stock_price_map: dict[str, float],
        interval_minute: int,
    ) -> dict[datetime, float]:
        assets_by_date = defaultdict(list)
        for asset in assets:
            assets_by_date[asset.asset_stock.trade_date].append(asset)
        current_assets = [asset for asset in assets if asset.asset_stock.trade_date <= interval_datetimes[0].date()]

        result = {}
        avg_profits = []

        for interval_datetime in interval_datetimes:
            if (
                interval_datetime.hour == 0
                and interval_datetime.minute == 0
                and interval_datetime.date() in assets_by_date
            ):
                interval_assets = assets_by_date[interval_datetime.date()]
                current_assets.extend(interval_assets)

            interval_stock_price_map = self._get_datetime_interval_stock_price_map(
                current_assets, interval_datetime, stock_datetime_price_map, current_stock_price_map
            )
            total_asset_amount = self.asset_stock_service.get_total_asset_amount(
                current_assets, interval_stock_price_map, exchange_rate_map
            )
            total_invest_amount = self.asset_stock_service.get_total_investment_amount(
                current_assets, stock_daily_map, exchange_rate_map
            )
            current_profit = self.asset_stock_service.get_total_profit_rate(total_asset_amount, total_invest_amount)

            avg_profits.append(current_profit)

            if interval_datetime.minute % interval_minute == 0:
                current_avg_profits = mean(avg_profits)
                index_map_key = interval_datetime.replace(tzinfo=None)
                result[index_map_key] = current_avg_profits

        return result

    def _get_datetime_interval_stock_price_map(
        self,
        assets: list[Asset],
        interval_datetime: datetime,
        stock_datetime_price_map: dict[tuple[str, datetime], float],
        current_stock_price_map,
    ) -> dict[str, float]:
        result = {}
        index_map_key = interval_datetime.replace(tzinfo=None)
        for asset in assets:
            code = asset.asset_stock.stock.code
            current_price = stock_datetime_price_map.get((asset.asset_stock.stock.code, index_map_key), None)
            result[code] = current_price if current_price else current_stock_price_map.get(code)

        return result

    def _get_market_analysis_short(
        self,
        market_index_minutely_map: dict[datetime, MarketIndexMinutely],
        current_index_price: float,
        interval_datetimes: list[datetime],
        interval_minute: int,
    ) -> dict[datetime, float]:
        result = {}
        avg_prices = []

        for interval_datetime in interval_datetimes:
            index_map_key = interval_datetime.replace(tzinfo=None)
            if index_map_key in market_index_minutely_map:
                current_market_index = market_index_minutely_map[index_map_key]
                avg_prices.append(current_market_index.price)

            if interval_datetime.minute % interval_minute == 0:
                current_avg_price = mean(avg_prices)
                current_profit = self.asset_stock_service.get_total_profit_rate(current_index_price, current_avg_price)
                result[index_map_key] = current_profit
                avg_prices = []

        return result
