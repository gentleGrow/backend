from collections import defaultdict
from datetime import date

from pytest import approx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.module.asset.dependencies.dividend_dependency import get_dividend_service
from app.module.asset.enum import AssetType
from app.module.asset.model import Asset, AssetStock, Stock
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.auth.constant import DUMMY_USER_ID


class TestDividendService:
    def test_process_dividends_by_year_month(self, setup_all):
        # Given
        total_dividends = {
            date(2024, 1, 15): 100.0,
            date(2024, 3, 20): 200.0,
            date(2024, 7, 5): 300.0,
            date(2023, 12, 25): 150.0,
            date(2023, 2, 10): 50.0,
        }

        expected_result = {
            "2023": {
                1: 0.0,
                2: 50.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 150.0,
            },
            "2024": {
                1: 100.0,
                2: 0.0,
                3: 200.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 300.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
            },
        }

        # When
        result = DividendService.process_dividends_by_year_month(total_dividends)

        # Then
        assert result == expected_result

    async def test_get_last_year_dividends(self, setup_all, session: AsyncSession):
        # Given
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
        result = DividendService.get_last_year_dividends(
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
        asset = Asset(asset_stock=AssetStock(purchase_date=date(2024, 8, 13), stock=Stock(code="AAPL"), quantity=10))

        won_exchange_rate = 1300.0

        dividend_map = {
            ("AAPL", date(2024, 8, 13)): 1.5,
            ("AAPL", date(2024, 8, 14)): 1.6,
            ("TSLA", date(2024, 8, 14)): 0.9,
        }

        # When
        result, last_dividend_date = DividendService.get_asset_total_dividend(
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
        assets = await session.execute(select(Asset).filter(Asset.user_id == DUMMY_USER_ID))
        assets = assets.scalars().all()

        # When
        dividend_map = await DividendService.get_dividend_map(session, assets)

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
        assets = await session.execute(select(Asset).filter(Asset.user_id == DUMMY_USER_ID))
        assets = assets.scalars().all()

        # When
        result = await DividendService.get_recent_map(session, assets)

        # Then
        assert result["AAPL"] == 1.60
        assert result["TSLA"] == 0.90

    async def test_get_total_dividend(
        self, session: AsyncSession, redis_client: Redis, setup_exchange_rate, setup_asset, setup_dividend
    ):
        # Given
        assets: list[Asset] = await AssetRepository.get_eager(session, DUMMY_USER_ID, AssetType.STOCK)
        dividend_map = await DividendService.get_recent_map(session, assets)
        exchange_rate_map = await ExchangeRateService.get_exchange_rate_map(redis_client)

        # When
        dividend_service = get_dividend_service()
        total_dividend = await dividend_service.get_total_dividend(
            session=session, redis_client=redis_client, assets=assets
        )
        expected_total_dividend = 0.0
        for asset in assets:
            dividend_per_stock = dividend_map.get(asset.asset_stock.stock.code, 0.0)
            exchange_rate = ExchangeRateService.get_won_exchange_rate(asset, exchange_rate_map)
            expected_total_dividend += dividend_per_stock * asset.asset_stock.quantity * exchange_rate

        # Then
        assert total_dividend == approx(expected_total_dividend)
