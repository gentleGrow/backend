from sqlalchemy.ext.asyncio import AsyncSession
from app.module.asset.repository.asset_repository import AssetRepository
from icecream import ic

class AssetValidate:
    async def check_asset_exist(self, session:AsyncSession, asset_id:int, user_id:str) -> bool:
        asset = await AssetRepository.get_asset_by_id(session, asset_id)
        
        if asset is None:
            return False
        elif str(asset.user_id) != user_id:
            return False
        else:
            return True