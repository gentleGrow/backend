from app.module.asset.services.asset.asset_validate import AssetValidate
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_service import StockService

exchange_rate_service = ExchangeRateService()
dividend_service = DividendService(exchange_rate_service=exchange_rate_service)


def get_asset_service() -> AssetService:
    return AssetService(
        stock_daily_service=StockDailyService(),
        exchange_rate_service=exchange_rate_service,
        stock_service=StockService(),
        dividend_service=dividend_service,
    )


def get_asset_validate() -> AssetValidate:
    return AssetValidate()
