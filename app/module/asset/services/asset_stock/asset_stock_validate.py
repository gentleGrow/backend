from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.constant import KOREA
from app.module.asset.enum import PurchaseCurrencyType, StockAsset
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.schema import AssetStockPostRequest, AssetStockPutRequest, AssetStockStatusResponse
from app.module.asset.services.stock.stock_validate import StockValidate


class AssetStockValidate:
    def __init__(self, stock_validate: StockValidate):
        self.stock_validate = stock_validate

    async def check_stock_purchase_type(self, session: AsyncSession, code: str, purchase_type: str) -> bool:
        stock = await StockRepository.get_by_code(session, code)
        if stock.country == KOREA:
            return purchase_type == PurchaseCurrencyType.KOREA
        else:
            return True

    async def check_asset_stock_request(
        self, session: AsyncSession, request_data: AssetStockPostRequest | AssetStockPutRequest
    ) -> AssetStockStatusResponse | None:
        if request_data.stock_code:
            stock_code_exist = await self.stock_validate.check_code_exist(session, request_data.stock_code)
            if not stock_code_exist:
                return AssetStockStatusResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{request_data.stock_code}를 찾지 못 했습니다.",
                    field=StockAsset.STOCK_NAME,
                )

        if request_data.stock_code and request_data.trade_date:
            stock_data_exist = await self.stock_validate.check_stock_data_exist(
                session, request_data.stock_code, request_data.trade_date
            )
            if not stock_data_exist:
                return AssetStockStatusResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{request_data.stock_code} 코드의 {request_data.trade_date} 날짜 데이터가 존재하지 않습니다.",
                    field=StockAsset.TRADE_DATE,
                )

        if request_data.stock_code and request_data.purchase_currency_type:
            stock_purchase_type_match = await self.check_stock_purchase_type(
                session, request_data.stock_code, request_data.purchase_currency_type
            )
            if not stock_purchase_type_match:
                return AssetStockStatusResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{request_data.stock_code}는 국내 주식이기에, 원화만 가능합니다.",
                    field=StockAsset.TRADE_PRICE,
                )

        return None
