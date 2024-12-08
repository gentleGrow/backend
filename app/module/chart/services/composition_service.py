from collections import defaultdict

from app.module.asset.enum import AccountType
from app.module.asset.model import Asset
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.chart.schema import CompositionResponseValue


class CompositionService:
    def __init__(self, exchange_rate_service: ExchangeRateService):
        self.exchange_rate_service = exchange_rate_service

    def get_asset_stock_composition(
        self, assets: list[Asset], current_stock_price_map: dict[str, float], exchange_rate_map: dict[str, float]
    ) -> list[CompositionResponseValue]:
        total_portfolio_value = 0.0
        stock_composition: defaultdict = defaultdict(lambda: {"name": "", "total_value": 0.0})

        for asset in assets:
            stock_code = asset.asset_stock.stock.code
            stock_name = asset.asset_stock.stock.name_kr
            quantity = asset.asset_stock.quantity
            current_price = current_stock_price_map.get(stock_code, 1.0)
            won_exchange_rate: float = self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            stock_value = quantity * won_exchange_rate * current_price

            stock_composition[stock_code]["name"] = stock_name
            stock_composition[stock_code]["total_value"] += stock_value

            total_portfolio_value += stock_value

        result = []
        for stock_data in stock_composition.values():
            proportion = (stock_data["total_value"] / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0

            result.append(
                CompositionResponseValue(
                    name=stock_data["name"], percent_rate=proportion, current_amount=stock_data["total_value"]
                )
            )

        return result

    def get_asset_stock_account(
        self, assets: list[Asset], current_stock_price_map: dict[str, float], exchange_rate_map: dict[str, float]
    ) -> list[CompositionResponseValue]:
        total_portfolio_value = 0.0
        stock_composition: defaultdict = defaultdict(lambda: {"name": "", "total_value": 0.0})

        for asset in assets:
            stock_code = asset.asset_stock.stock.code
            account_type = asset.asset_stock.account_type if asset.asset_stock.account_type else AccountType.NONE
            quantity = asset.asset_stock.quantity
            current_price = current_stock_price_map.get(stock_code, 1.0)
            won_exchange_rate: float = self.exchange_rate_service.get_won_exchange_rate(asset, exchange_rate_map)
            stock_value = quantity * won_exchange_rate * current_price

            stock_composition[account_type]["name"] = account_type
            stock_composition[account_type]["total_value"] += stock_value

            total_portfolio_value += stock_value

        result = []
        for stock_data in stock_composition.values():
            proportion = (stock_data["total_value"] / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0

            result.append(
                CompositionResponseValue(
                    name=stock_data["name"], percent_rate=proportion, current_amount=stock_data["total_value"]
                )
            )

        return result
