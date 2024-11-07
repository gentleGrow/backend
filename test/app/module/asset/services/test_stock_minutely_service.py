from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.enum import AssetType
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.services.stock_minutely_service import StockMinutelyService
from app.module.auth.constant import DUMMY_USER_ID
from app.module.asset.dependencies.stock_minutely_dependency import get_stock_minutely_service


class TestStockMinutelyService:
    async def test_get_datetime_interval_map(self, session: AsyncSession, setup_all):
        # Given
        stock_minutely_service: StockMinutelyService = get_stock_minutely_service()
        
        interval_start = datetime(2024, 8, 13, 10, 0)
        interval_end = datetime(2024, 8, 13, 11, 0)
        assets = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        interval = 15

        # When
        result = await stock_minutely_service.get_datetime_interval_map(
            session=session, interval_start=interval_start, interval_end=interval_end, assets=assets, interval=interval
        )

        # Then
        assert len(result) == 4
