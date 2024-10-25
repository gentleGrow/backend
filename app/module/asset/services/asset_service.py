from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import get_now_date
from app.module.asset.enum import ASSETNAME, AmountUnit
from app.module.asset.model import Asset, StockDaily
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AssetStockPutRequest
from app.module.asset.services.exchange_rate_service import ExchangeRateService


class AssetService:
    @staticmethod
    def asset_list_from_days(assets: list[Asset], days: int) -> defaultdict:
        assets_by_date = defaultdict(list)

        current_date = get_now_date()
        for day_offset in range(days):
            target_date = current_date - timedelta(days=day_offset)

            for asset in assets:
                purchase_date = asset.asset_stock.purchase_date

                if purchase_date <= target_date:
                    assets_by_date[target_date].append(asset)

        return assets_by_date

    @staticmethod
    def get_average_investment_with_dividend_year(
        total_invest_amount: float, total_dividend_amount: float, months: float
    ) -> float:
        average_invest_amount_month = total_invest_amount / months if total_invest_amount > 0.0 else 0.0
        average_dividend_month = total_dividend_amount / months if total_dividend_amount > 0.0 else 0.0
        return (
            (average_invest_amount_month + average_dividend_month) * 12
            if average_invest_amount_month + average_dividend_month > 0
            else 0.0
        )

    @staticmethod
    def calculate_trend_values(
        total_asset_amount: float,
        increase_invest_year: float,
        total_profit_rate: float,
        total_profit_rate_real: float,
        years: int,
    ) -> tuple[dict[str, list[float]], dict[str, list[float]], str]:
        values1: dict[str, Any] = {"values": [], "name": ASSETNAME.ESTIMATE_ASSET}
        values2: dict[str, Any] = {"values": [], "name": ASSETNAME.REAL_ASSET}

        current_value1 = total_asset_amount
        current_value2 = total_asset_amount

        for _ in range(years):
            current_value1 += increase_invest_year
            current_value1 *= 1 + total_profit_rate / 100
            values1["values"].append(current_value1)

            current_value2 += increase_invest_year
            current_value2 *= 1 + total_profit_rate_real / 100
            values2["values"].append(current_value2)

        if total_asset_amount >= 100000000:
            values1["values"] = [v / 100000000 for v in values1["values"]]
            values2["values"] = [v / 100000000 for v in values2["values"]]
            unit = AmountUnit.BILLION_WON
        else:
            unit = AmountUnit.MILLION_WON

        return values1, values2, unit

    @staticmethod
    async def get_asset_map(session: AsyncSession, asset_id: int) -> dict[int, Asset] | None:
        asset = await AssetRepository.get_asset_by_id(session, asset_id)
        return {asset.id: asset} if asset else None

    @staticmethod
    async def save_asset_by_put(
        session: AsyncSession, request_data: AssetStockPutRequest, asset: Asset, stock_id: int
    ) -> None:
        if request_data.account_type is not None:
            asset.asset_stock.account_type = request_data.account_type

        if request_data.investment_bank is not None:
            asset.asset_stock.investment_bank = request_data.investment_bank

        if request_data.purchase_currency_type is not None:
            asset.asset_stock.purchase_currency_type = request_data.purchase_currency_type

        if request_data.buy_date is not None:
            asset.asset_stock.purchase_date = request_data.buy_date

        if request_data.purchase_price is not None:
            asset.asset_stock.purchase_price = request_data.purchase_price

        if request_data.quantity is not None:
            asset.asset_stock.quantity = request_data.quantity

        asset.asset_stock.stock_id = stock_id

        await AssetRepository.save(session, asset)

    @staticmethod
    def get_total_asset_amount_with_datetime(
        assets: list[Asset],
        exchange_rate_map: dict[str, float],
        stock_datetime_price_map: dict[str, float],
        current_datetime: datetime,
        stock_daily_map: dict[tuple[str, date], StockDaily],
    ) -> float:
        result = 0.0

        for asset in assets:
            current_value = stock_datetime_price_map.get(f"{asset.asset_stock.stock.code}_{current_datetime}", None)

            if current_value is None:
                current_stock_daily = stock_daily_map.get(
                    (asset.asset_stock.stock.code, asset.asset_stock.purchase_date), None
                )
                current_value = current_stock_daily.adj_close_price if current_stock_daily is not None else 1.0

            result += (
                current_value
                * asset.asset_stock.quantity
                * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return result

    @staticmethod
    def get_total_asset_amount_with_date(
        assets: list[Asset],
        exchange_rate_map: dict[str, float],
        stock_daily_map: dict[tuple[str, date], StockDaily],
    ) -> float:
        result = 0.0

        for asset in assets:
            current_stock_daily = stock_daily_map.get(
                (asset.asset_stock.stock.code, asset.asset_stock.purchase_date), None
            )

            if current_stock_daily is None:
                current_stock_daily = AssetService.find_closest_stock_daily(
                    asset.asset_stock.stock.code, asset.asset_stock.purchase_date, stock_daily_map
                )

                current_value = current_stock_daily.close_price if current_stock_daily else 1.0
            else:
                current_value = current_stock_daily.adj_close_price

            result += (
                current_value
                * asset.asset_stock.quantity
                * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return result

    @staticmethod
    def find_closest_stock_daily(
        stock_code: str, purchase_date: date, stock_daily_map: dict[tuple[str, date], StockDaily]
    ) -> StockDaily | None:
        available_dates = [date for (code, date) in stock_daily_map.keys() if code == stock_code]
        if not available_dates:
            return None
        closest_date = max([d for d in available_dates if d <= purchase_date], default=None)

        return stock_daily_map.get((stock_code, closest_date), None) if closest_date else None
