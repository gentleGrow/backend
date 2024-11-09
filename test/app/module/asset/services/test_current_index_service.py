from redis.asyncio import Redis

from app.module.asset.dependencies.realtime_index_dependency import get_realtime_index_service
from app.module.asset.enum import MarketIndex
from app.module.asset.services.realtime_index_service import RealtimeIndexService


class TestCurrentIndexService:
    async def test_get_current_index_price(
        self,
        redis_client: Redis,
        setup_all,
    ):
        # Given
        realtime_index_service: RealtimeIndexService = get_realtime_index_service()

        market_type = MarketIndex.KOSPI

        # When
        result = await realtime_index_service.get_current_index_price(redis_client, market_type)

        # Then
        assert result == 3250.0

    async def test_get_current_index_price_no_data(self, redis_client: Redis, setup_all):
        # Given
        realtime_index_service: RealtimeIndexService = get_realtime_index_service()
        market_type = MarketIndex.DOW_JONES

        # When
        result = await realtime_index_service.get_current_index_price(redis_client, market_type)

        # Then
        assert result == 1.0
