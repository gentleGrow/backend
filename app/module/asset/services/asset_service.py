from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import pandas
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import get_now_date
from app.module.asset.constant import REQUIRED_ASSET_FIELD
from app.module.asset.enum import ASSETNAME, AmountUnit, PurchaseCurrencyType, StockAsset, StockAsset_v1, TradeType
from app.module.asset.model import Asset, Stock, StockDaily
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import (
    AggregateStockAsset,
    AssetStockPutRequest,
    AssetStockPutRequest_v1,
    StockAssetGroup,
    StockAssetSchema,
    TodayTempStockDaily,
)
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_service import StockService


class AssetService:
    def __init__(
        self,
        stock_daily_service: StockDailyService,
        exchange_rate_service: ExchangeRateService,
        stock_service: StockService,
        dividend_service: DividendService,
    ):
        self.stock_daily_service = stock_daily_service
        self.exchange_rate_service = exchange_rate_service
        self.stock_service = stock_service
        self.dividend_service = dividend_service

    def filter_undone_asset(self, assets: list[Asset]) -> list[Asset]:
        return [
            asset
            for asset in assets
            if all(
                [
                    asset.asset_stock.trade_date,
                    asset.asset_stock.quantity,
                    asset.asset_stock.trade,
                    asset.asset_stock.stock,
                    asset.asset_stock.stock.code,
                ]
            )
        ]

    def asset_list_from_days(self, assets: list[Asset], days: int) -> dict:
        assets_by_date = defaultdict(list)

        current_date = get_now_date()
        for day_offset in range(days):
            target_date = current_date - timedelta(days=day_offset)

            for asset in assets:
                purchase_date = asset.asset_stock.trade_date

                if purchase_date <= target_date:
                    assets_by_date[target_date].append(asset)

        return assets_by_date

    def calculate_trend_values(
        self,
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
            values1["values"] = [v / 10000 for v in values1["values"]]
            values2["values"] = [v / 10000 for v in values2["values"]]
            unit = AmountUnit.MILLION_WON

        return values1, values2, unit

    async def get_asset_map(self, session: AsyncSession, asset_id: int) -> dict[int, Asset] | None:
        asset = await AssetRepository.get_asset_by_id(session, asset_id)
        return {asset.id: asset} if asset else None

    # 확인 후 삭제하겠습니다.
    async def save_asset_by_put_v1(
        self, session: AsyncSession, request_data: AssetStockPutRequest_v1, asset: Asset, stock: Stock | None
    ):
        if request_data.account_type is not None:
            asset.asset_stock.account_type = request_data.account_type

        if request_data.investment_bank is not None:
            asset.asset_stock.investment_bank = request_data.investment_bank

        if request_data.purchase_currency_type is not None:
            asset.asset_stock.purchase_currency_type = request_data.purchase_currency_type

        if request_data.buy_date is not None:
            asset.asset_stock.trade_date = request_data.buy_date

        if request_data.purchase_price is not None:
            asset.asset_stock.trade_price = request_data.purchase_price

        if request_data.quantity is not None:
            asset.asset_stock.quantity = request_data.quantity

        if stock is not None:
            asset.asset_stock.stock_id = stock.id

        asset.asset_stock.trade = request_data.trade if request_data.trade else TradeType.BUY

        await AssetRepository.save(session, asset)

    ###########################

    async def save_asset_by_put(
        self, session: AsyncSession, request_data: AssetStockPutRequest, asset: Asset, stock: Stock | None
    ):
        if request_data.account_type:
            asset.asset_stock.account_type = request_data.account_type

        if request_data.investment_bank:
            asset.asset_stock.investment_bank = request_data.investment_bank

        if request_data.purchase_currency_type:
            asset.asset_stock.purchase_currency_type = request_data.purchase_currency_type

        if request_data.trade_date is not None:
            asset.asset_stock.trade_date = request_data.trade_date

        if request_data.trade_price is not None:
            asset.asset_stock.trade_price = request_data.trade_price

        if request_data.quantity is not None:
            asset.asset_stock.quantity = request_data.quantity

        if stock:
            asset.asset_stock.stock_id = stock.id

        asset.asset_stock.trade = request_data.trade if request_data.trade else TradeType.BUY

        await AssetRepository.save(session, asset)

    def get_total_asset_amount_with_datetime(
        self,
        assets: list[Asset],
        exchange_rate_map: dict[str, float],
        stock_datetime_price_map: dict[str, float],
        current_datetime: datetime,
        stock_daily_map: dict[tuple[str, date], StockDaily],
    ):
        result = 0.0

        for asset in assets:
            current_value = stock_datetime_price_map.get(f"{asset.asset_stock.stock.code}_{current_datetime}", None)

            if current_value is None:
                current_stock_daily = stock_daily_map.get(
                    (asset.asset_stock.stock.code, asset.asset_stock.trade_date), None
                )
                current_value = current_stock_daily.adj_close_price if current_stock_daily is not None else 1.0

            result += (
                current_value
                * asset.asset_stock.quantity
                * self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return result

    def find_closest_stock_daily(
        self, stock_code: str, purchase_date: date, stock_daily_map: dict[tuple[str, date], StockDaily]
    ) -> StockDaily | None:
        available_dates = [date for (code, date) in stock_daily_map.keys() if code == stock_code]
        if not available_dates:
            return None
        closest_date = max([d for d in available_dates if d <= purchase_date], default=None)

        return stock_daily_map.get((stock_code, closest_date), None) if closest_date else None

    def get_average_investment_with_dividend_year(
        self, total_invest_amount: float, total_dividend_amount: float, months: float
    ) -> float:
        average_invest_amount_month = total_invest_amount / months if total_invest_amount > 0.0 else 0.0
        average_dividend_month = total_dividend_amount / months if total_dividend_amount > 0.0 else 0.0
        return (
            (average_invest_amount_month + average_dividend_month) * 12
            if average_invest_amount_month + average_dividend_month > 0
            else 0.0
        )

    async def filter_required_assets(self, assets: list[Asset]) -> list[Asset]:
        return [asset for asset in assets if await self._check_required_field(asset)]

    async def get_total_investment_amount(
        self, session: AsyncSession, redis_client: Redis, assets: list[Asset]
    ) -> float:
        stock_daily_map = await self.stock_daily_service.get_map_range(session, assets)
        exchange_rate_map = await self.exchange_rate_service.get_exchange_rate_map(redis_client)
        lastest_stock_daily_map = await self.stock_daily_service.get_latest_map(session, assets)

        result = 0.0

        for asset in assets:
            stock_daily = stock_daily_map.get((asset.asset_stock.stock.code, asset.asset_stock.trade_date), None)
            if stock_daily is None:
                stock_daily = lastest_stock_daily_map.get(asset.asset_stock.stock.code, None)

                if stock_daily is None:
                    continue

            invest_price = (
                asset.asset_stock.trade_price
                * self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
                if asset.asset_stock.purchase_currency_type == PurchaseCurrencyType.USA
                and asset.asset_stock.trade_price
                else asset.asset_stock.trade_price
                if asset.asset_stock.trade_price
                else stock_daily.adj_close_price
                * self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            )

            result += invest_price * asset.asset_stock.quantity

        return result

    def get_total_asset_amount_with_date_with_map(
        self,
        assets: list[Asset],
        exchange_rate_map: dict[str, float],
        stock_daily_date_map: dict[tuple[str, date], StockDaily],
        market_date: date,
    ) -> float:
        result = 0.0

        for asset in assets:
            current_stock_daily = stock_daily_date_map.get((asset.asset_stock.stock.code, market_date), None)

            if current_stock_daily is None:
                current_stock_daily = self.find_closest_stock_daily(
                    asset.asset_stock.stock.code, market_date, stock_daily_date_map
                )
                current_value = current_stock_daily.close_price if current_stock_daily else 1.0
            else:
                current_value = current_stock_daily.adj_close_price

            result += (
                current_value
                * asset.asset_stock.quantity
                * self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return result

    async def get_total_asset_amount_with_date(
        self, session: AsyncSession, redis_client: Redis, assets: list[Asset], past_date: date
    ) -> float:
        result = 0.0

        exchange_rate_map = await self.exchange_rate_service.get_exchange_rate_map(redis_client)
        stock_daily_date_map = await self.stock_daily_service.get_date_map(session, assets, past_date)

        for asset in assets:
            current_stock_daily = stock_daily_date_map.get((asset.asset_stock.stock.code, past_date), None)
            current_value = current_stock_daily.adj_close_price if current_stock_daily else 1.0

            result += (
                current_value
                * asset.asset_stock.quantity
                * self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            )

        return result

    async def get_total_asset_amount(self, session: AsyncSession, redis_client: Redis, assets: list[Asset]) -> float:
        lastest_stock_daily_map = await self.stock_daily_service.get_latest_map(session, assets)
        current_stock_price_map = await self.stock_service.get_current_stock_price(
            redis_client, lastest_stock_daily_map, assets
        )
        exchange_rate_map = await self.exchange_rate_service.get_exchange_rate_map(redis_client)

        result = 0.0

        for asset in assets:
            result += (
                current_stock_price_map.get(asset.asset_stock.stock.code)
                * asset.asset_stock.quantity
                * self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            )
        return result

    async def _check_required_field(self, asset: Asset) -> bool:
        return bool(asset.asset_stock.trade_date and asset.asset_stock.quantity and asset.stock.code)

    def group_stock_assets(
        self, stock_asset_elements: list[StockAssetSchema], aggregate_stock_assets: list[AggregateStockAsset]
    ) -> list[StockAssetGroup]:
        result = []

        parent_stock_asset_dict = {
            parent_stock_asset.종목명: parent_stock_asset for parent_stock_asset in aggregate_stock_assets
        }

        stock_elements_by_name = defaultdict(list)
        for stock_asset in stock_asset_elements:
            stock_name = stock_asset.종목명.value
            if isinstance(stock_name, str):
                stock_elements_by_name[stock_name].append(stock_asset)

        for stock_name, sub_stock_assets in stock_elements_by_name.items():
            if stock_name in parent_stock_asset_dict:
                stock_asset_group = StockAssetGroup(parent=parent_stock_asset_dict[stock_name], sub=sub_stock_assets)
                result.append(stock_asset_group)

        return result

    def aggregate_stock_assets(self, stock_assets: list[StockAssetSchema]) -> list[AggregateStockAsset]:
        stock_asset_dataframe = pandas.DataFrame(
            {
                "stock_name": [stock_asset.종목명.value for stock_asset in stock_assets],
                "profit_rate": [stock_asset.수익률.value for stock_asset in stock_assets],
                "profit_amount": [stock_asset.수익금.value for stock_asset in stock_assets],
                "dividend": [stock_asset.배당금.value for stock_asset in stock_assets],
            }
        )

        aggregated_df = (
            stock_asset_dataframe.groupby("stock_name")
            .agg(
                avg_profit_rate=("profit_rate", "mean"),
                total_profit_amount=("profit_amount", "sum"),
                total_dividend=("dividend", "sum"),
            )
            .reset_index()
        )

        return [
            AggregateStockAsset(
                종목명=row["stock_name"],
                수익률=row["avg_profit_rate"],
                수익금=row["total_profit_amount"],
                배당금=row["total_dividend"],
            )
            for _, row in aggregated_df.iterrows()
        ]

    # 수정 확인 후 삭제하겠습니다 ####
    async def get_stock_assets_v1(
        self, session: AsyncSession, redis_client: Redis, assets: list[Asset], asset_fields: list
    ) -> list[dict]:
        stock_daily_map = await self.stock_daily_service.get_map_range(session, assets)
        lastest_stock_daily_map = await self.stock_daily_service.get_latest_map(session, assets)
        dividend_map = await self.dividend_service.get_recent_map(session, assets)
        exchange_rate_map = await self.exchange_rate_service.get_exchange_rate_map(redis_client)
        current_stock_price_map = await self.stock_service.get_current_stock_price(
            redis_client, lastest_stock_daily_map, assets
        )

        result = []

        for asset in assets:
            apply_exchange_rate = self._get_apply_exchange_rate(asset, exchange_rate_map)
            stock_daily = self._get_matching_stock_daily(
                asset, stock_daily_map, lastest_stock_daily_map, current_stock_price_map
            )
            purchase_price = self._get_purchase_price(asset, stock_daily)

            stock_asset_data = self._build_stock_asset_v1(
                asset, stock_daily, apply_exchange_rate, current_stock_price_map, dividend_map, purchase_price
            )

            stock_asset_formatted_data = self._apply_require_sign(stock_asset_data, asset_fields)

            result.append(stock_asset_formatted_data)

        return result

    ################

    async def get_stock_assets(
        self, session: AsyncSession, redis_client: Redis, assets: list[Asset], asset_fields: list
    ) -> list[StockAssetSchema]:
        stock_daily_map = await self.stock_daily_service.get_map_range(session, assets)
        lastest_stock_daily_map = await self.stock_daily_service.get_latest_map(session, assets)
        dividend_map = await self.dividend_service.get_recent_map(session, assets)
        exchange_rate_map = await self.exchange_rate_service.get_exchange_rate_map(redis_client)
        current_stock_price_map = await self.stock_service.get_current_stock_price(
            redis_client, lastest_stock_daily_map, assets
        )

        stock_assets = []

        for asset in assets:
            apply_exchange_rate = self._get_apply_exchange_rate(asset, exchange_rate_map)
            stock_daily = self._get_matching_stock_daily(
                asset, stock_daily_map, lastest_stock_daily_map, current_stock_price_map
            )
            purchase_price = self._get_purchase_price(asset, stock_daily)

            stock_asset_data = self._build_stock_asset(
                asset, stock_daily, apply_exchange_rate, current_stock_price_map, dividend_map, purchase_price
            )

            stock_asset_formatted_data = self._apply_require_sign(stock_asset_data, asset_fields)

            stock_asset_schema = StockAssetSchema(**stock_asset_formatted_data)

            stock_assets.append(stock_asset_schema)

        return stock_assets

    def _get_apply_exchange_rate(self, asset: Asset, exchange_rate_map: dict) -> float:
        asset_purchase_currency_type = asset.asset_stock.purchase_currency_type

        return (
            self.exchange_rate_service.get_dollar_exchange_rate(asset, exchange_rate_map)
            if asset_purchase_currency_type == PurchaseCurrencyType.USA
            else self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
        )

    def _get_current_price(self, asset: Asset, current_stock_price_map: dict, apply_exchange_rate: float) -> float:
        return current_stock_price_map.get(asset.asset_stock.stock.code, 1.0) * apply_exchange_rate

    def _get_dividend(self, asset: Asset, dividend_map: dict, apply_exchange_rate: float) -> float:
        return dividend_map.get(asset.asset_stock.stock.code, 1.0) * asset.asset_stock.quantity * apply_exchange_rate

    def _get_profit_rate(
        self, asset: Asset, current_stock_price_map: dict, purchase_price: float, apply_exchange_rate: float
    ) -> float:
        if asset.asset_stock.trade_price:
            return (
                (
                    (current_stock_price_map.get(asset.asset_stock.stock.code, 1.0) * apply_exchange_rate)
                    - purchase_price
                )
                / purchase_price
                * 100
            )
        else:
            purchase_price_rated = purchase_price * apply_exchange_rate
            return (
                (
                    (current_stock_price_map.get(asset.asset_stock.stock.code, 1.0) * apply_exchange_rate)
                    - purchase_price_rated
                )
                / purchase_price_rated
                * 100
            )

    def _get_purchase_amount(self, asset: Asset, purchase_price: float, apply_exchange_rate: float) -> float:
        if asset.asset_stock.trade_price:
            return purchase_price * asset.asset_stock.quantity
        else:
            return purchase_price * asset.asset_stock.quantity * apply_exchange_rate

    def _get_profit_amount(
        self, asset: Asset, current_stock_price_map: dict, purchase_price: float, apply_exchange_rate: float
    ):
        if asset.asset_stock.trade_price:
            return (
                (current_stock_price_map.get(asset.asset_stock.stock.code, 1.0) * apply_exchange_rate) - purchase_price
            ) * asset.asset_stock.quantity
        else:
            return (
                current_stock_price_map.get(asset.asset_stock.stock.code, 1.0) * apply_exchange_rate
                - purchase_price * apply_exchange_rate
            ) * asset.asset_stock.quantity

    ### 확인 후 수정하겠습니다!!!!!
    def _build_stock_asset_v1(
        self,
        asset: Asset,
        stock_daily: TodayTempStockDaily,
        apply_exchange_rate: float,
        current_stock_price_map: dict,
        dividend_map: dict,
        purchase_price: float,
    ) -> dict:
        current_price = self._get_current_price(asset, current_stock_price_map, apply_exchange_rate)
        dividend = self._get_dividend(asset, dividend_map, apply_exchange_rate)
        profit_rate = self._get_profit_rate(asset, current_stock_price_map, purchase_price, apply_exchange_rate)
        purchase_amount = self._get_purchase_amount(asset, purchase_price, apply_exchange_rate)
        profit_amount = self._get_profit_amount(asset, current_stock_price_map, purchase_price, apply_exchange_rate)

        return {
            StockAsset_v1.ID.value: asset.id,
            StockAsset_v1.ACCOUNT_TYPE.value: asset.asset_stock.account_type or None,
            StockAsset_v1.BUY_DATE.value: asset.asset_stock.trade_date,
            StockAsset_v1.CURRENT_PRICE.value: current_price,
            StockAsset_v1.DIVIDEND.value: dividend,
            StockAsset_v1.HIGHEST_PRICE.value: stock_daily.highest_price * apply_exchange_rate
            if stock_daily.highest_price
            else None,
            StockAsset_v1.INVESTMENT_BANK.value: asset.asset_stock.investment_bank or None,
            StockAsset_v1.LOWEST_PRICE.value: stock_daily.lowest_price * apply_exchange_rate
            if stock_daily.lowest_price
            else None,
            StockAsset_v1.OPENING_PRICE.value: stock_daily.opening_price * apply_exchange_rate
            if stock_daily.opening_price
            else None,
            StockAsset_v1.PROFIT_RATE.value: profit_rate,
            StockAsset_v1.PROFIT_AMOUNT.value: profit_amount,
            StockAsset_v1.PURCHASE_AMOUNT.value: purchase_amount,
            StockAsset_v1.PURCHASE_PRICE.value: asset.asset_stock.trade_price or None,
            StockAsset_v1.PURCHASE_CURRENCY_TYPE.value: asset.asset_stock.purchase_currency_type or None,
            StockAsset_v1.QUANTITY.value: asset.asset_stock.quantity,
            StockAsset_v1.STOCK_CODE.value: asset.asset_stock.stock.code,
            StockAsset_v1.STOCK_NAME.value: asset.asset_stock.stock.name_kr,
            StockAsset_v1.STOCK_VOLUME.value: stock_daily.trade_volume if stock_daily.trade_volume else None,
        }

    #######################

    def _build_stock_asset(
        self,
        asset: Asset,
        stock_daily: TodayTempStockDaily,
        apply_exchange_rate: float,
        current_stock_price_map: dict,
        dividend_map: dict,
        purchase_price: float,
    ) -> dict:
        current_price = self._get_current_price(asset, current_stock_price_map, apply_exchange_rate)
        dividend = self._get_dividend(asset, dividend_map, apply_exchange_rate)
        profit_rate = self._get_profit_rate(asset, current_stock_price_map, purchase_price, apply_exchange_rate)
        purchase_amount = self._get_purchase_amount(asset, purchase_price, apply_exchange_rate)
        profit_amount = self._get_profit_amount(asset, current_stock_price_map, purchase_price, apply_exchange_rate)

        return {
            StockAsset.ID.value: asset.id,
            StockAsset.ACCOUNT_TYPE.value: asset.asset_stock.account_type or None,
            StockAsset.TRADE_DATE.value: asset.asset_stock.trade_date,
            StockAsset.CURRENT_PRICE.value: current_price,
            StockAsset.DIVIDEND.value: dividend,
            StockAsset.HIGHEST_PRICE.value: stock_daily.highest_price * apply_exchange_rate
            if stock_daily.highest_price
            else None,
            StockAsset.INVESTMENT_BANK.value: asset.asset_stock.investment_bank or None,
            StockAsset.LOWEST_PRICE.value: stock_daily.lowest_price * apply_exchange_rate
            if stock_daily.lowest_price
            else None,
            StockAsset.OPENING_PRICE.value: stock_daily.opening_price * apply_exchange_rate
            if stock_daily.opening_price
            else None,
            StockAsset.PROFIT_RATE.value: profit_rate,
            StockAsset.PROFIT_AMOUNT.value: profit_amount,
            StockAsset.TRADE_AMOUNT.value: purchase_amount,
            StockAsset.TRADE_PRICE.value: asset.asset_stock.trade_price or None,
            StockAsset.PURCHASE_CURRENCY_TYPE.value: asset.asset_stock.purchase_currency_type or None,
            StockAsset.QUANTITY.value: asset.asset_stock.quantity,
            StockAsset.STOCK_CODE.value: asset.asset_stock.stock.code,
            StockAsset.STOCK_NAME.value: asset.asset_stock.stock.name_kr,
            StockAsset.STOCK_VOLUME.value: stock_daily.trade_volume if stock_daily.trade_volume else None,
        }

    def _get_matching_stock_daily(
        self, asset: Asset, stock_daily_map: dict, lastest_stock_daily_map: dict, current_stock_price_map: dict
    ) -> TodayTempStockDaily:
        stock_daily = stock_daily_map.get((asset.asset_stock.stock.code, asset.asset_stock.trade_date), None)
        if stock_daily is None:
            recent_stockdaily = lastest_stock_daily_map.get(asset.asset_stock.stock.code, None)
            open_price = (
                recent_stockdaily.adj_close_price
                if recent_stockdaily
                else current_stock_price_map.get(asset.asset_stock.stock.code, 1.0)
            )
            stock_daily = TodayTempStockDaily(
                adj_close_price=current_stock_price_map.get(asset.asset_stock.stock.code, 1.0),
                highest_price=current_stock_price_map.get(asset.asset_stock.stock.code, 1.0),
                lowest_price=current_stock_price_map.get(asset.asset_stock.stock.code, 1.0),
                opening_price=open_price,
                trade_volume=1,
            )
        return stock_daily

    def _get_purchase_price(self, asset: Asset, stock_daily: TodayTempStockDaily) -> float:
        return asset.asset_stock.trade_price if asset.asset_stock.trade_price else stock_daily.adj_close_price

    def _apply_require_sign(self, stock_asset_data: dict, asset_fields: list) -> dict:
        result = {
            field: {"isRequired": field in REQUIRED_ASSET_FIELD, "value": value}
            for field, value in stock_asset_data.items()
        }

        result[StockAsset.ID.value] = stock_asset_data[StockAsset.ID.value]
        result[StockAsset.PURCHASE_CURRENCY_TYPE.value] = stock_asset_data[StockAsset.PURCHASE_CURRENCY_TYPE.value]
        return result
