from freezegun import freeze_time
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.module.chart.constant import FULL_PERCENTAGE_RATE
from app.module.auth.constant import DUMMY_USER_ID
from app.module.chart.facade.summary_facade import SummaryFacade
from app.module.asset.dependencies.asset_dependency import get_asset_service


class TestSummaryFacade:
    @freeze_time("2024-10-01")
    async def test_get_today_review_rate_assets_older_than_30_days(
        self, setup_all, redis_client: Redis, session: AsyncSession
    ):
        # Given
        asset_service = get_asset_service()

        # When
        result = await SummaryFacade.get_today_review_rate(
            session=session,
            redis_client=redis_client,
            user_id=DUMMY_USER_ID,
            asset_service=asset_service
        )
             
        # Then
        assert result == -54.24460431654676


    @freeze_time("2024-09-01")
    async def test_get_today_review_rate_no_assets_older_than_30_days(
        self, setup_all, redis_client: Redis, session: AsyncSession
    ):
        # Given
        asset_service = get_asset_service()

        # When
        result = await SummaryFacade.get_today_review_rate(
            session=session,
            redis_client=redis_client,
            user_id=DUMMY_USER_ID,
            asset_service=asset_service
        )

        # Then
        assert result == FULL_PERCENTAGE_RATE



