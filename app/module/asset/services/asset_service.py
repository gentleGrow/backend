from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.schema import AssetStockPutRequest
from app.module.asset.enum import AmountUnit, ASSETNAME


class AssetService:
    @staticmethod
    def get_average_investment_with_dividend_year(
        total_invest_amount:float,
        total_dividend_amount:float,
        months:float
    ) -> float:
        average_invest_amount_month = total_invest_amount / months if total_invest_amount > 0.0 else 0.0
        average_dividend_month = total_dividend_amount / months if total_dividend_amount > 0.0 else 0.0
        return (average_invest_amount_month + average_dividend_month) * 12 if average_invest_amount_month + average_dividend_month > 0 else 0.0
    
    @staticmethod
    def calculate_trend_values(
        total_asset_amount: float,
        increase_invest_year: float,
        total_profit_rate: float,
        total_profit_rate_real: float,
        years: int,
    ) -> tuple[dict[str, list[float]], dict[str, list[float]], str]:
        values1 = {"values": [], "name": ASSETNAME.ESTIMATE_ASSET}
        values2 = {"values": [], "name": ASSETNAME.REAL_ASSET}
        
        current_value1 = total_asset_amount
        current_value2 = total_asset_amount

        for _ in range(years):
            current_value1 += increase_invest_year
            current_value1 *= 1 + total_profit_rate
            values1["values"].append(current_value1)

            current_value2 += increase_invest_year
            current_value2 *= 1 + total_profit_rate_real
            values2["values"].append(current_value2)

        if total_asset_amount >= 100000000:
            unit = AmountUnit.BILLION_WON
            values1["values"] = [v / 100000000 for v in values1["values"]]
            values2["values"] = [v / 100000000 for v in values2["values"]]
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
