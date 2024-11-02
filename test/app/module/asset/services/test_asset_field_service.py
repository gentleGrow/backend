from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.constant import REQUIRED_ASSET_FIELD
from app.module.asset.services.asset_field_service import AssetFieldService
from app.module.auth.constant import DUMMY_USER_ID


class TestAssetFieldService:
    async def test_get_asset_field_exists(self, session: AsyncSession, setup_asset_field):
        # Given
        setup_asset_field

        # When
        result = await AssetFieldService.get_asset_field(session, DUMMY_USER_ID)

        # Then
        assert result == REQUIRED_ASSET_FIELD

    async def test_get_asset_field_create_new(self, session: AsyncSession, setup_user):
        # Given
        new_user_id = 2

        # When
        result = await AssetFieldService.get_asset_field(session, new_user_id)

        # Then
        expected_fields = [field for field in REQUIRED_ASSET_FIELD]
        assert result == expected_fields

        # And
        saved_asset_field = await AssetFieldService.get_asset_field(session, new_user_id)
        assert saved_asset_field is not None
        assert saved_asset_field == expected_fields
