import json

from redis.asyncio import Redis

from app.module.asset.constant import MARKET_INDEX_KR_MAPPING
from app.module.asset.enum import MarketIndex
from app.module.asset.schema import MarketIndexData
from app.module.chart.redis_repository import RedisMarketIndiceRepository
from app.module.chart.schema import MarketIndiceValue


class RealtimeIndexService:
    async def get_current_index_price(self, redis_client: Redis, market_type: MarketIndex) -> float:
        curent_index: MarketIndexData | None = await RedisMarketIndiceRepository.get(redis_client, market_type)
        return float(curent_index.current_value) if curent_index else 2417.0

    async def get_current_market_index_value(self, redis_client: Redis):
        market_index_keys = [market_index.value for market_index in MarketIndex]
        market_index_values: list[str] = await RedisMarketIndiceRepository.gets(redis_client, market_index_keys)

        filtered_market_index_values = [json.loads(value) for value in market_index_values if value]

        return [
            MarketIndiceValue(
                name=market_index_value["name"],
                name_kr=MARKET_INDEX_KR_MAPPING.get(market_index_value["name"]),
                current_value=float(market_index_value["current_value"]),
                change_percent=float(market_index_value["change_percent"]),
            )
            for market_index_value in filtered_market_index_values
            if market_index_value and MARKET_INDEX_KR_MAPPING.get(market_index_value["name"])
        ]
