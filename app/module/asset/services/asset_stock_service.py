from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.enum import AssetType, CurrencyType, PurchaseCurrencyType, TradeType
from app.module.asset.model import Asset, AssetStock, StockDaily
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AssetStockPostRequest, AssetStockPostRequest_v1
from app.module.asset.services.exchange_rate_service import ExchangeRateService


class AssetStockService:
    def __init__(self, exchange_rate_service: ExchangeRateService):
        self.exchange_rate_service = exchange_rate_service

    def get_total_profit_rate(
        self,
        current_amount: float,
        past_amount: float,
    ) -> float:
        return ((current_amount - past_amount) / past_amount) * 100 if past_amount > 0 else 0.0

    def get_total_profit_rate_real(
        self, total_asset_amount: float, total_invest_amount: float, real_value_rate: float
    ) -> float:
        return (
            (((total_asset_amount - total_invest_amount) / total_invest_amount) * 100) - real_value_rate
            if total_invest_amount > 0
            else 0.0
        )

    def get_total_asset_amount(
        self,
        assets: list[Asset],
        current_stock_price_map: dict[str, float],
        exchange_rate_map: dict[str, float],
    ) -> float:
        result = 0.0

        for asset in assets:
            result += (
                current_stock_price_map.get(asset.asset_stock.stock.code)
                * asset.asset_stock.quantity
                * self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            )
        return result

    # 확인 후 수정하겠습니다.
    async def save_asset_stock_by_post_v1(
        self, session: AsyncSession, request_data: AssetStockPostRequest_v1, stock_id: int, user_id: int
    ) -> None:
        result = []

        new_asset = Asset(
            asset_type=AssetType.STOCK,
            user_id=user_id,
            asset_stock=AssetStock(
                account_type=request_data.account_type,
                investment_bank=request_data.investment_bank,
                purchase_currency_type=request_data.purchase_currency_type,
                trade_date=request_data.buy_date,
                trade_price=request_data.purchase_price,
                quantity=request_data.quantity,
                trade=request_data.trade if request_data.trade else TradeType.BUY,
                stock_id=stock_id,
            ),
        )
        result.append(new_asset)

        await AssetRepository.save_assets(session, result)

    #############################

    async def save_asset_stock_by_post(
        self, session: AsyncSession, request_data: AssetStockPostRequest, stock_id: int, user_id: int
    ) -> None:
        result = []

        new_asset = Asset(
            asset_type=AssetType.STOCK,
            user_id=user_id,
            asset_stock=AssetStock(
                account_type=request_data.account_type,
                investment_bank=request_data.investment_bank,
                purchase_currency_type=request_data.purchase_currency_type,
                trade_date=request_data.trade_date,
                trade_price=request_data.trade_price,
                quantity=request_data.quantity,
                trade=request_data.trade if request_data.trade else TradeType.BUY,
                stock_id=stock_id,
            ),
        )
        result.append(new_asset)

        await AssetRepository.save_assets(session, result)

    def get_total_asset_amount_minute(
        self,
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
            won_exchange_rate = self.exchange_rate_service.get_exchange_rate(
                source_currency, CurrencyType.KOREA, exchange_rate_map
            )

            current_price *= won_exchange_rate
            result += current_price * asset.asset_stock.quantity
        return result

    def get_total_investment_amount(
        self,
        assets: list[Asset],
        stock_daily_map: dict[tuple[str, date], StockDaily],
        exchange_rate_map: dict[str, float],
    ) -> float:
        total_invest_amount = 0.0

        for asset in assets:
            stock_daily = stock_daily_map.get((asset.asset_stock.stock.code, asset.asset_stock.trade_date), None)
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

            total_invest_amount += invest_price * asset.asset_stock.quantity

        return total_invest_amount
