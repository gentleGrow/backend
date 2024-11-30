from app.module.asset.services.stock_service import StockService
from app.module.asset.services.stock.stock_validate import StockValidate

def get_stock_service() -> StockService:
    return StockService()


def get_stock_validate() -> StockValidate:
    return StockValidate()