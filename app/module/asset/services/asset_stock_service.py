from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.enum import AssetType, CurrencyType, PurchaseCurrencyType
from app.module.asset.model import Asset, AssetStock, StockDaily
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AssetStockPostRequest
from app.module.asset.services.exchange_rate_service import ExchangeRateService


class AssetStockService:
    @staticmethod
    def get_total_profit_rate(
        total_asset_amount: float,
        total_invest_amount: float,
    ) -> float:
        return (
            ((total_asset_amount - total_invest_amount) / total_invest_amount) * 100 if total_invest_amount > 0 else 0.0
        )

    @staticmethod
    def get_total_profit_rate_real(
        total_asset_amount: float, total_invest_amount: float, real_value_rate: float
    ) -> float:
        return (
            (((total_asset_amount - total_invest_amount) / total_invest_amount) * 100) - real_value_rate
            if total_invest_amount > 0
            else 0.0
        )

    @staticmethod
    def get_total_asset_amount(
        assets: list[Asset],
        current_stock_price_map: dict[str, float],
        exchange_rate_map: dict[str, float],
    ) -> float:
        result = 0.0

        for asset in assets:
            result += (
                current_stock_price_map.get(asset.asset_stock.stock.code)
                * asset.asset_stock.quantity
                * ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            )
        return result

    @staticmethod
    async def check_asset_stock_exist(session: AsyncSession, buy_date: date, stock_id: int):
        pass

    @staticmethod
    async def save_asset_stock_by_post(
        session: AsyncSession, request_data: AssetStockPostRequest, stock_id: int, user_id: int
    ) -> None:
        result = []

        new_asset = Asset(
            asset_type=AssetType.STOCK,
            user_id=user_id,
            asset_stock=AssetStock(
                account_type=request_data.account_type,
                investment_bank=request_data.investment_bank,
                purchase_currency_type=request_data.purchase_currency_type,
                purchase_date=request_data.buy_date,
                purchase_price=request_data.purchase_price,
                quantity=request_data.quantity,
                stock_id=stock_id,
            ),
        )
        result.append(new_asset)

        await AssetRepository.save_assets(session, result)

    @staticmethod
    def get_total_asset_amount_minute(
        assets: list[Asset],
        stock_interval_date_price_map: dict[str, float],
        exchange_rate_map: dict[str, float],
        current_datetime: datetime,
    ) -> float:
        result = 0.0

        for asset in assets:
            current_price = stock_interval_date_price_map.get(f"{asset.asset_stock.stock.code}_{current_datetime}")

            if current_price is None:
                continue

            source_country = asset.asset_stock.stock.country.upper().strip()
            source_currency = CurrencyType[source_country]
            won_exchange_rate = ExchangeRateService.get_exchange_rate(
                source_currency, CurrencyType.KOREA, exchange_rate_map
            )

            current_price *= won_exchange_rate
            result += current_price * asset.asset_stock.quantity
        return result

    @staticmethod
    def get_total_investment_amount(
        assets: list[Asset],
        stock_daily_map: dict[tuple[str, date], StockDaily],
        exchange_rate_map: dict[str, float],
    ) -> float:
        total_invest_amount = 0.0

        for asset in assets:
            stock_daily = stock_daily_map.get((asset.asset_stock.stock.code, asset.asset_stock.purchase_date), None)
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

            total_invest_amount += invest_price * asset.asset_stock.quantity

        return total_invest_amount
