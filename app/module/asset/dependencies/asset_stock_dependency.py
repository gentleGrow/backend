from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.exchange_rate_service import ExchangeRateService

exchange_rate_service = ExchangeRateService()


def get_asset_stock_service():
    return AssetStockService(exchange_rate_service=exchange_rate_service)
