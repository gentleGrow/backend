from collections import defaultdict

from app.module.asset.model import Asset
from app.module.chart.schema import PeoplePortfolioValue, PortfolioStockData


class PortfolioService:
    def get_porfolio_value(self, users_assets: dict[str, list[Asset]]) -> list[PeoplePortfolioValue]:
        result = []
        stock_quantities: defaultdict[str, int] = defaultdict(int)
        portfolio_data = []

        for user_name, assets in users_assets.items():
            for asset in assets:
                stock_quantities[asset.asset_stock.stock.name_kr] += asset.asset_stock.quantity

        total_quantity = sum(asset.asset_stock.quantity for asset in assets)

        for stock_name, total_quantity in stock_quantities.items():
            portfolio_data.append(
                PortfolioStockData(name=stock_name, percent_ratio=(total_quantity / total_quantity) * 100)
            )

        result.append(PeoplePortfolioValue(name=user_name, data=portfolio_data))

        return result
