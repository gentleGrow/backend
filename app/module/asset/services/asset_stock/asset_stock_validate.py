from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.constant import KOREA
from app.module.asset.enum import PurchaseCurrencyType
from app.module.asset.repository.stock_repository import StockRepository


class AssetStockValidate:
    async def check_stock_purchase_type(self, session: AsyncSession, code: str, purchase_type: str) -> bool:
        stock = await StockRepository.get_by_code(session, code)
        if stock.country == KOREA:
            return purchase_type == PurchaseCurrencyType.KOREA
        else:
            return True
