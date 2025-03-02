from redis.asyncio import Redis

from app.module.asset.constant import CURRENCY_PAIRS, DEFAULT_DOLLAR_EXCHANGE_RATE, DEFAULT_WON_EXCHANGE_RATE
from app.module.asset.enum import CurrencyType
from app.module.asset.model import Asset
from app.module.asset.redis_repository import RedisExchangeRateRepository


class ExchangeRateService:
    def get_won_exchange_rate(self, asset: Asset, exchange_rate_map: dict[str, float]) -> float:
        source_country = asset.asset_stock.stock.country.upper().strip()
        source_currency = CurrencyType[source_country]
        if source_currency == CurrencyType.KOREA:
            return 1.0
        else:
            return float(exchange_rate_map.get(f"{source_currency}_{CurrencyType.KOREA}", DEFAULT_WON_EXCHANGE_RATE))

    def get_dollar_exchange_rate(self, asset: Asset, exchange_rate_map: dict[str, float]) -> float:
        source_country = asset.asset_stock.stock.country.upper().strip()
        source_currency = CurrencyType[source_country]
        if source_currency == CurrencyType.USA:
            return 1.0
        else:
            return float(exchange_rate_map.get(f"{source_currency}_{CurrencyType.USA}", DEFAULT_DOLLAR_EXCHANGE_RATE))

    async def get_exchange_rate_map(self, redis_client: Redis) -> dict[str, float]:
        result = {}
        keys = [f"{source_currency}_{target_currency}" for source_currency, target_currency in CURRENCY_PAIRS]
        exchange_rates: list[float] = await RedisExchangeRateRepository.bulk_get(redis_client, keys)

        for i, key in enumerate(keys):
            rate = exchange_rates[i]
            result[key] = float(rate) if rate else 0.0

        if result.get(f"{CurrencyType.USA}_{CurrencyType.KOREA}", 0.0) == 0.0:
            result[f"{CurrencyType.USA}_{CurrencyType.KOREA}"] = 1400.0
        if result.get(f"{CurrencyType.KOREA}_{CurrencyType.USA}", 0.0) == 0.0:
            result[f"{CurrencyType.KOREA}_{CurrencyType.USA}"] = 0.00068

        return result

    def get_exchange_rate(
        self, source: CurrencyType, target: CurrencyType, exchange_rate_map: dict[str, float]
    ) -> float:
        if source == target:
            return 1.0

        if source == CurrencyType.USA and target == CurrencyType.KOREA:
            return exchange_rate_map.get(f"{source}_{target}", 1400.0)
        if source == CurrencyType.KOREA and target == CurrencyType.USA:
            return exchange_rate_map.get(f"{source}_{target}", 0.00068)

        return float(exchange_rate_map.get(f"{source}_{target}", 0.0))
