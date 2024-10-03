import json

from redis.asyncio import Redis

from app.module.asset.enum import MarketIndex
from app.module.asset.schema import MarketIndexData
from app.module.chart.redis_repository import RedisMarketIndiceRepository


class IndexService:
    @staticmethod
    async def get_current_market_index_value(redis_client: Redis):
        market_index_keys = [market_index.value for market_index in MarketIndex]
        market_index_values_str = await RedisMarketIndiceRepository.gets(redis_client, market_index_keys)
        return [
            MarketIndexData(**json.loads(value)) if value is not None else None for value in market_index_values_str
        ]
