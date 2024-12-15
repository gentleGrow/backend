from app.module.asset.services.asset.asset_query import AssetQuery
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.asset.services.index_daily_service import IndexDailyService
from app.module.asset.services.index_minutely_service import IndexMinutelyService
from app.module.asset.services.realtime_index_service import RealtimeIndexService
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.asset.services.stock_minutely_service import StockMinutelyService
from app.module.asset.services.stock_service import StockService
from app.module.chart.services.rich_service import RichService

exchange_rate_service = ExchangeRateService()
realtime_index_service = RealtimeIndexService()
index_daily_service = IndexDailyService()
index_minutely_service = IndexMinutelyService()
stock_daily_service = StockDailyService()
stock_minutely_service = StockMinutelyService()

asset_stock_service = AssetStockService(exchange_rate_service=exchange_rate_service)
dividend_service = DividendService(exchange_rate_service=exchange_rate_service)
stock_service = StockService(asset_stock_service=asset_stock_service)

asset_service = AssetService(
    stock_daily_service=stock_daily_service,
    asset_stock_service=asset_stock_service,
    exchange_rate_service=exchange_rate_service,
    stock_service=stock_service,
    dividend_service=dividend_service,
)

asset_query = AssetQuery(
    stock_daily_service=stock_daily_service,
    exchange_rate_service=exchange_rate_service,
    stock_service=stock_service,
    dividend_service=dividend_service,
)


def get_rich_service() -> RichService:
    return RichService(
        asset_service=asset_service, 
        asset_query=asset_query,
        stock_service=stock_service,
        exchange_rate_service=exchange_rate_service
    )
