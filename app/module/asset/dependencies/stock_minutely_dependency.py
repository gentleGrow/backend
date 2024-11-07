from app.module.asset.dependencies.stock_minutely_dependency import StockMinutelyService


def get_stock_minutely_service() -> StockMinutelyService:
    return StockMinutelyService()