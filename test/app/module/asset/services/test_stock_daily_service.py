from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.module.asset.dependencies.stock_daily_dependency import get_stock_daily_service
from app.module.asset.model import Asset
from app.module.asset.services.stock_daily_service import StockDailyService
from app.module.auth.constant import DUMMY_USER_ID


class TestStockDailyService:
    async def test_get_latest_map(self, session: AsyncSession, setup_stock_daily, setup_asset):
        # Given
        stock_daily_service: StockDailyService = get_stock_daily_service()

        assets = await session.execute(select(Asset).filter(Asset.user_id == DUMMY_USER_ID))
        assets = assets.scalars().all()

        # When
        result = await stock_daily_service.get_latest_map(session, assets)

        # Then
        assert len(result) == 3

        assert "AAPL" in result
        latest_aapl = result["AAPL"]
        assert latest_aapl.code == "AAPL"
        assert latest_aapl.date == date(2024, 9, 1)

        assert "TSLA" in result
        latest_tsla = result["TSLA"]
        assert latest_tsla.code == "TSLA"
        assert latest_tsla.date == date(2024, 9, 1)

    async def test_get_map_range(self, session: AsyncSession, setup_stock_daily, setup_asset):
        # Given
        stock_daily_service: StockDailyService = get_stock_daily_service()

        assets = await session.execute(select(Asset).filter(Asset.user_id == DUMMY_USER_ID))
        assets = assets.scalars().all()

        # When
        result = await stock_daily_service.get_map_range(session, assets)

        # Then
        assert len(result) == 3

        assert ("AAPL", date(2024, 8, 13)) in result
        stock_daily_aapl = result[("AAPL", date(2024, 8, 13))]
        assert stock_daily_aapl.code == "AAPL"
        assert stock_daily_aapl.date == date(2024, 8, 13)

        assert ("TSLA", date(2024, 8, 14)) in result
        stock_daily_tsla = result[("TSLA", date(2024, 8, 14))]
        assert stock_daily_tsla.code == "TSLA"
        assert stock_daily_tsla.date == date(2024, 8, 14)
