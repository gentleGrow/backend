from app.module.asset.services.stock_minutely_service import StockMinutelyService


def get_stock_minutely_service() -> StockMinutelyService:
    return StockMinutelyService()
