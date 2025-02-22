from app.module.asset.services.asset_stock.asset_stock_service import AssetStockService
from app.module.asset.services.asset_stock.asset_stock_validate import AssetStockValidate
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock.stock_validate import StockValidate

exchange_rate_service = ExchangeRateService()
stock_validate = StockValidate()

def get_asset_stock_service() -> AssetStockService:
    return AssetStockService(exchange_rate_service=exchange_rate_service)


def get_asset_stock_validate() -> AssetStockValidate:
    return AssetStockValidate(stock_validate=stock_validate)
