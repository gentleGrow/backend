from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_service import StockService
from app.module.chart.services.summary_service import SummaryService

stock_daily_service = StockDailyService()
exchange_rate_service = ExchangeRateService()
stock_service = StockService()

dividend_service = DividendService(exchange_rate_service=exchange_rate_service)

asset_stock_service = AssetStockService(exchange_rate_service=exchange_rate_service)
asset_service = AssetService(
    stock_daily_service=stock_daily_service,
    exchange_rate_service=exchange_rate_service,
    stock_service=stock_service,
    dividend_service=dividend_service,
)


def get_summary_service() -> SummaryService:
    return SummaryService(asset_stock_service=asset_stock_service, asset_service=asset_service)
