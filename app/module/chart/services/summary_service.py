from datetime import datetime, timedelta

from app.module.asset.model import Asset
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.chart.constant import FULL_PERCENTAGE_RATE, PAST_MONTH_DAY


class SummaryService:
    def __init__(self, asset_stock_service: AssetStockService, asset_service: AssetService):
        self.asset_stock_service = asset_stock_service
        self.asset_service = asset_service

    def get_today_review_rate(
        self, assets: list[Asset], current_stock_price_map: dict[str, float], exchange_rate_map: dict[str, float]
    ) -> tuple[float, float]:
        past_assets = [
            asset
            for asset in assets
            if asset.asset_stock.trade_date <= datetime.now().date() - timedelta(days=PAST_MONTH_DAY)
        ]

        if not len(past_assets):
            return (FULL_PERCENTAGE_RATE, 0.0)

        past_total_amount = self.asset_service.get_total_asset_amount(
            past_assets, current_stock_price_map, exchange_rate_map
        )
        current_total_amount = self.asset_service.get_total_asset_amount(
            assets, current_stock_price_map, exchange_rate_map
        )

        return (
            self.asset_stock_service.get_total_profit_rate(current_total_amount, past_total_amount),
            current_total_amount - past_total_amount,
        )
