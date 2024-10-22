import asyncio

import ray
import yfinance

from app.data.common.constant import STOCK_CACHE_SECOND
from app.data.yahoo.source.constant import EXCHANGE_RATE_COLLECTOR_WAIT_SECOND
from app.module.asset.constant import CURRENCY_PAIRS
from app.module.asset.redis_repository import RedisExchangeRateRepository
from database.dependency import get_redis_pool

# from icecream import ic


@ray.remote
class ExchangeRateCollector:
    def __init__(self):
        self.redis_client = get_redis_pool()
        self._is_running = False

    async def collect(self) -> None:
        # ic("환율 데이터 수집을 시작합니다.")
        self._is_running = True

        while True:
            for source_currency, target_currency in CURRENCY_PAIRS:
                rate = await self._fetch_exchange_rate(source_currency, target_currency)
                if rate is None:
                    continue

                cache_key = source_currency + "_" + target_currency
                await RedisExchangeRateRepository.save(
                    self.redis_client, cache_key, rate, expire_time=STOCK_CACHE_SECOND
                )
            self._is_running = False
            await asyncio.sleep(EXCHANGE_RATE_COLLECTOR_WAIT_SECOND)

    async def _fetch_exchange_rate(self, source_currency: str, target_currency: str) -> float | None:
        url = f"{source_currency}{target_currency}=X"
        try:
            ticker = yfinance.Ticker(url)
            exchange_rate_history = ticker.history(period="1d")
            if exchange_rate_history.empty:
                return None

            return exchange_rate_history["Close"].iloc[0]
        except Exception:
            return None

    def is_running(self) -> bool:
        return self._is_running
