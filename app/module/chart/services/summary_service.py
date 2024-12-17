from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import check_date_weekend, get_date_past_day
from app.module.asset.model import Asset, StockDaily
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.chart.constant import FULL_PERCENTAGE_RATE, PAST_MONTH_DAY


class SummaryService:
    def __init__(
        self,
        asset_stock_service: AssetStockService,
        asset_service: AssetService,
        stock_daily_service: StockDailyService,
    ):
        self.asset_stock_service = asset_stock_service
        self.asset_service = asset_service
        self.stock_daily_service = stock_daily_service

    def get_today_review_rate(
        self,
        assets: list[Asset],
        current_stock_price_map: dict[str, float],
        exchange_rate_map: dict[str, float],
        past_stock_map: dict[str, float],
    ) -> tuple[float, float]:
        past_assets = [asset for asset in assets if asset.asset_stock.trade_date <= get_date_past_day(PAST_MONTH_DAY)]

        if not len(past_assets):
            return (FULL_PERCENTAGE_RATE, 0.0)

        past_total_amount = self.asset_service.get_total_asset_amount(past_assets, past_stock_map, exchange_rate_map)

        current_total_amount = self.asset_service.get_total_asset_amount(
            assets, current_stock_price_map, exchange_rate_map
        )

        return (
            self.asset_stock_service.get_total_profit_rate(current_total_amount, past_total_amount),
            current_total_amount - past_total_amount,
        )

    async def get_past_stock_map(
        self, session: AsyncSession, assets: list[Asset], lastest_stock_daily_map: dict[str, StockDaily]
    ) -> dict[str, float]:
        past_date = self._get_weekday_date(PAST_MONTH_DAY)
        past_stock_daily_map: dict[tuple[str, date], StockDaily] = await self.stock_daily_service.get_date_map(
            session, assets, past_date
        )
        stock_codes = [asset.asset_stock.stock.code for asset in assets]

        result = {}

        for stock_code in stock_codes:
            stock_daily = past_stock_daily_map.get((stock_code, past_date))
            if not stock_daily:
                stock_daily = lastest_stock_daily_map.get(stock_code)
            past_price = stock_daily.adj_close_price  # type: ignore # 앞단에서 검증이 되어서, None이 될 수 없습니다.
            result[stock_code] = float(past_price)

        return result

    def _get_weekday_date(self, days: int) -> date:
        past_date = get_date_past_day(days)
        while check_date_weekend(past_date):
            days = days + 1
            past_date = get_date_past_day(days)

        return past_date
