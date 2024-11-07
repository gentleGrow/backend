from app.module.asset.services.asset_field_service import AssetFieldService


def get_asset_field_service() -> AssetFieldService:
    return AssetFieldService()