from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.constant import REQUIRED_ASSET_FIELD
from app.module.asset.enum import PurchaseCurrencyType, StockAsset
from app.module.asset.model import Asset
from app.module.asset.schema import TodayTempStockDaily
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_service import StockService


class AssetFacade:
    @staticmethod
    async def get_stock_assets(
        session: AsyncSession, redis_client: Redis, assets: list[Asset], asset_fields: list
    ) -> list[dict]:
        stock_daily_map = await StockDailyService.get_map_range(session, assets)
        lastest_stock_daily_map = await StockDailyService.get_latest_map(session, assets)
        dividend_map: dict[str, float] = await DividendService.get_recent_map(session, assets)
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)
        current_stock_price_map = await StockService.get_current_stock_price(
            redis_client, lastest_stock_daily_map, assets
        )

        stock_assets = []

        for asset in assets:
            apply_exchange_rate: float = (
                ExchangeRateService.get_dollar_exchange_rate(asset, exchange_rate_map)
                if asset.asset_stock.purchase_currency_type == PurchaseCurrencyType.USA
                else ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )

            stock_daily = stock_daily_map.get((asset.asset_stock.stock.code, asset.asset_stock.purchase_date), None)

            if stock_daily is None:
                recent_stockdaily = lastest_stock_daily_map.get(asset.asset_stock.stock.code, None)
                open_price: float = (
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

                purchase_price = asset.asset_stock.purchase_price if asset.asset_stock.purchase_price else open_price
            else:
                purchase_price = (
                    asset.asset_stock.purchase_price
                    if asset.asset_stock.purchase_price
                    else stock_daily.adj_close_price
                )

            stock_asset_data = {
                StockAsset.ID.value: asset.id,
                StockAsset.ACCOUNT_TYPE.value: asset.asset_stock.account_type or None,
                StockAsset.BUY_DATE.value: asset.asset_stock.purchase_date,
                StockAsset.CURRENT_PRICE.value: (
                    current_stock_price_map.get(asset.asset_stock.stock.code, 1.0) * apply_exchange_rate
                ),
                StockAsset.DIVIDEND.value: (
                    dividend_map.get((asset.asset_stock.stock.code), 1.0)
                    * asset.asset_stock.quantity
                    * apply_exchange_rate
                ),
                StockAsset.HIGHEST_PRICE.value: (stock_daily.highest_price * apply_exchange_rate)
                if stock_daily.highest_price
                else None,
                StockAsset.INVESTMENT_BANK.value: asset.asset_stock.investment_bank or None,
                StockAsset.LOWEST_PRICE.value: (stock_daily.lowest_price * apply_exchange_rate)
                if stock_daily.lowest_price
                else None,
                StockAsset.OPENING_PRICE.value: (stock_daily.opening_price * apply_exchange_rate)
                if stock_daily.opening_price
                else None,
                StockAsset.PROFIT_RATE.value: (
                    (
                        current_stock_price_map.get(asset.asset_stock.stock.code, 1.0) * apply_exchange_rate
                        - (purchase_price * apply_exchange_rate)
                    )
                    / (purchase_price * apply_exchange_rate)
                    * 100
                )
                if purchase_price
                else None,
                StockAsset.PROFIT_AMOUNT.value: (
                    (
                        (current_stock_price_map.get(asset.asset_stock.stock.code, 1.0) * apply_exchange_rate)
                        - (purchase_price * apply_exchange_rate)
                    )
                    * asset.asset_stock.quantity
                )
                if purchase_price
                else None,
                StockAsset.PURCHASE_AMOUNT.value: (asset.asset_stock.purchase_price * asset.asset_stock.quantity)
                if asset.asset_stock.purchase_price
                else None,
                StockAsset.PURCHASE_PRICE.value: asset.asset_stock.purchase_price or None,
                StockAsset.PURCHASE_CURRENCY_TYPE.value: asset.asset_stock.purchase_currency_type or None,
                StockAsset.QUANTITY.value: asset.asset_stock.quantity,
                StockAsset.STOCK_CODE.value: asset.asset_stock.stock.code,
                StockAsset.STOCK_NAME.value: asset.asset_stock.stock.name_kr,
                StockAsset.STOCK_VOLUME.value: stock_daily.trade_volume if stock_daily.trade_volume else None,
            }

            stock_asset_data_filter = {
                field: {"isRequired": field in REQUIRED_ASSET_FIELD, "value": value}
                for field, value in stock_asset_data.items()
                if field in asset_fields
            }
            stock_asset_data_filter[StockAsset.ID.value] = stock_asset_data[StockAsset.ID.value]
            stock_asset_data_filter[StockAsset.PURCHASE_CURRENCY_TYPE.value] = stock_asset_data[
                StockAsset.PURCHASE_CURRENCY_TYPE.value
            ]
            stock_assets.append(stock_asset_data_filter)

        return stock_assets

    @staticmethod
    async def get_total_investment_amount(session: AsyncSession, redis_client: Redis, assets: list[Asset]) -> float:
        stock_daily_map = await StockDailyService.get_map_range(session, assets)
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)
        lastest_stock_daily_map = await StockDailyService.get_latest_map(session, assets)

        result = 0.0

        for asset in assets:
            stock_daily = stock_daily_map.get((asset.asset_stock.stock.code, asset.asset_stock.purchase_date), None)
            if stock_daily is None:
                stock_daily = lastest_stock_daily_map.get(asset.asset_stock.stock.code, None)

                if stock_daily is None:
                    continue

            invest_price = (
                asset.asset_stock.purchase_price * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
                if asset.asset_stock.purchase_currency_type == PurchaseCurrencyType.USA
                and asset.asset_stock.purchase_price
                else asset.asset_stock.purchase_price
                if asset.asset_stock.purchase_price
                else stock_daily.adj_close_price * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )

            result += invest_price * asset.asset_stock.quantity

        return result

    @staticmethod
    async def get_total_asset_amount(session: AsyncSession, redis_client: Redis, assets: list[Asset]) -> float:
        lastest_stock_daily_map = await StockDailyService.get_latest_map(session, assets)
        current_stock_price_map = await StockService.get_current_stock_price(
            redis_client, lastest_stock_daily_map, assets
        )
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)

        result = 0.0

        for asset in assets:
            result += (
                current_stock_price_map.get(asset.asset_stock.stock.code)
                * asset.asset_stock.quantity
                * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )
        return result
