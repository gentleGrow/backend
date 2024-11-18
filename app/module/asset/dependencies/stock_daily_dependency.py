from app.module.asset.services.stock_daily_service import StockDailyService


def get_stock_daily_service() -> StockDailyService:
    return StockDailyService()
