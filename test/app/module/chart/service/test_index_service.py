import json

from redis.asyncio import Redis

from app.module.asset.enum import Country, MarketIndex
from app.module.asset.schema import MarketIndexData
from app.module.asset.services.realtime_index_service import RealtimeIndexService
from app.module.asset.dependencies.realtime_index_dependency import get_realtime_index_service


class TestIndexService:
    async def test_get_current_market_index_value(self, redis_client: Redis, setup_all):
        # Given
        realtime_index_service: RealtimeIndexService = get_realtime_index_service()
        
        expected_market_index_data = MarketIndexData(
            country=Country.KOREA,
            name=MarketIndex.KOSPI,
            current_value="3250.0",
            change_value="50.0",
            change_percent="1.56",
            update_time="2024-08-15 16:00:00",
        )

        await redis_client.set(
            MarketIndex.KOSPI,
            json.dumps(
                {
                    "country": Country.KOREA,
                    "name": MarketIndex.KOSPI,
                    "current_value": "3250.0",
                    "change_value": "50.0",
                    "change_percent": "1.56",
                    "update_time": "2024-08-15 16:00:00",
                }
            ),
        )

        # When
        result = await realtime_index_service.get_current_market_index_value(redis_client)

        # Then
        assert isinstance(result[0], MarketIndexData)
        assert result[0] == expected_market_index_data
