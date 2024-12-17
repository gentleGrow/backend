from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock.stock_validate import StockValidate
from app.module.asset.services.stock_service import StockService

exchange_rate_service = ExchangeRateService()
asset_stock_service = AssetStockService(exchange_rate_service=exchange_rate_service)


def get_stock_service() -> StockService:
    return StockService(asset_stock_service=asset_stock_service)


def get_stock_validate() -> StockValidate:
    return StockValidate()
