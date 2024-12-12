from collections import defaultdict
from datetime import date

from pytest import approx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.module.asset.dependencies.dividend_dependency import get_dividend_service
from app.module.asset.enum import TradeType
from app.module.asset.model import Asset, AssetStock, Stock
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.services.dividend_service import DividendService
from app.module.auth.constant import DUMMY_USER_ID


class TestDividendService:
    async def test_get_last_year_dividends(self, setup_all, session: AsyncSession):
        # Given
        dividend_service: DividendService = get_dividend_service()
        assets = await AssetRepository.get_assets(session, DUMMY_USER_ID)
        asset = assets[0]

        dividend_map = {
            ("AAPL", date(2024, 8, 13)): 1.5,
            ("AAPL", date(2024, 8, 14)): 1.6,
            ("AAPL", date(2023, 8, 13)): 1.4,
            ("AAPL", date(2023, 11, 14)): 1.5,
        }
        won_exchange_rate = 1300.0
        last_dividend_date = date(2024, 8, 14)

        # When
        result = dividend_service.get_last_year_dividends(
            asset=asset,
            dividend_map=dividend_map,
            won_exchange_rate=won_exchange_rate,
            last_dividend_date=last_dividend_date,
        )

        # Then
        expected_result = defaultdict(
            float,
            {
                date(2024, 11, 14): 1.5 * 1300 * asset.asset_stock.quantity,
            },
        )

        for key in expected_result:
            assert result[key] == approx(expected_result[key])

    def test_get_asset_total_dividend(
        self,
        setup_all,
    ):
        # Given
        dividend_service: DividendService = get_dividend_service()
        asset = Asset(
            asset_stock=AssetStock(
                trade_date=date(2024, 8, 13), stock=Stock(code="AAPL"), quantity=10, trade=TradeType.BUY
            )
        )

        won_exchange_rate = 1300.0

        dividend_map = {
            ("AAPL", date(2024, 8, 13)): 1.5,
            ("AAPL", date(2024, 8, 14)): 1.6,
            ("TSLA", date(2024, 8, 14)): 0.9,
        }

        # When
        result, last_dividend_date = dividend_service.get_asset_total_dividend(
            won_exchange_rate=won_exchange_rate,
            dividend_map=dividend_map,
            asset=asset,
        )

        # Then
        expected_result = defaultdict(float)
        expected_result[date(2024, 8, 13)] = 1.5 * won_exchange_rate * asset.asset_stock.quantity
        expected_result[date(2024, 8, 14)] = 1.6 * won_exchange_rate * asset.asset_stock.quantity
        expected_last_dividend_date = date(2024, 8, 14)

        assert result == expected_result
        assert last_dividend_date == expected_last_dividend_date

    async def test_get_dividend_map(self, session: AsyncSession, setup_all):
        # Given
        dividend_service: DividendService = get_dividend_service()
        assets = await session.execute(select(Asset).filter(Asset.user_id == DUMMY_USER_ID))
        assets = assets.scalars().all()

        # When
        dividend_map = await dividend_service.get_dividend_map(session, assets)

        # Then
        expected_dividend_map = {
            ("AAPL", date(2024, 8, 13)): 1.5,
            ("AAPL", date(2024, 8, 14)): 1.6,
            ("TSLA", date(2024, 8, 13)): 0.8,
            ("TSLA", date(2024, 8, 14)): 0.9,
            ("005930", date(2024, 8, 13)): 100.0,
            ("005930", date(2024, 8, 14)): 105.0,
        }

        assert dividend_map == expected_dividend_map

    async def test_get_recent_map(self, session: AsyncSession, setup_dividend, setup_asset):
        # Given
        dividend_service: DividendService = get_dividend_service()
        assets = await session.execute(select(Asset).filter(Asset.user_id == DUMMY_USER_ID))
        assets = assets.scalars().all()

        # When
        result = await dividend_service.get_recent_map(session, assets)

        # Then
        assert result["AAPL"] == 1.60
        assert result["TSLA"] == 0.90
