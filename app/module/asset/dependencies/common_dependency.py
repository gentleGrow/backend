from app.module.asset.services.asset_common.asset_common_validate import AssetCommonValidate
from app.module.asset.services.asset_stock.asset_stock_validate import AssetStockValidate
from app.module.asset.services.stock.stock_validate import StockValidate

stock_validate = StockValidate()
asset_stock_validate = AssetStockValidate()


def get_asset_common_validate() -> AssetCommonValidate:
    return AssetCommonValidate(stock_validate=stock_validate, asset_stock_validate=asset_stock_validate)
