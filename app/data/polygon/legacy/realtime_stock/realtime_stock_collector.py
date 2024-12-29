import asyncio
import itertools
from datetime import datetime
from os import getenv

import ray
import requests
from dotenv import load_dotenv
from requests.models import Response

from app.common.util.time import (
    get_current_unix_timestamp,
    make_minute_to_milisecond_timestamp,
    transform_timestamp_datetime,
)
from app.data.common.constant import STOCK_CACHE_SECOND
from app.data.polygon.legacy.constant import STOCK_COLLECT_END_TIME_MINUTE, STOCK_COLLECT_START_TIME_MINUTE
from app.module.asset.model import StockMinutely
from app.module.asset.redis_repository import RedisRealTimeStockRepository
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_mysql_session, get_redis_pool

load_dotenv()
POLYGON_API_KEY = getenv("POLYGON_API_KEY", None)


@ray.remote(max_task_retries=1)
class RealtimeStockCollector:
    def __init__(self, stock_code_list: list[StockInfo]):
        self.stock_code_list = stock_code_list
        self.redis_client = None
        self.session = None
        self._is_running = False

    async def collect(self):
        while True:
            await self._collect_data()

    async def _setup(self):
        self.redis_client = get_redis_pool()
        async with get_mysql_session() as session:
            self.session = session

    async def _collect_data(self) -> None:
        if self.redis_client is None or self.session is None:
            await self._setup()

        self._is_running = True
        try:
            code_price_pairs = []
            db_bulk_data = []
            fetch_tasks = []

            event_loop = asyncio.get_event_loop()

            for stockinfo in self.stock_code_list:
                try:
                    fetch_tasks.append(event_loop.run_in_executor(None, self._fetch_stock_price, stockinfo.code))
                except Exception:
                    continue

            task_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            code_price_pairs = list(
                itertools.chain.from_iterable(result for result in task_results if not isinstance(result, Exception))
            )

            redis_bulk_data = [(code, price) for code, _, price in code_price_pairs if price]

            for code, current_datetime, price in code_price_pairs:
                current_stock_data = StockMinutely(code=code, datetime=current_datetime, price=price)
                db_bulk_data.append(current_stock_data)

            if redis_bulk_data:
                await RedisRealTimeStockRepository.bulk_save(
                    self.redis_client, redis_bulk_data, expire_time=STOCK_CACHE_SECOND
                )

            if db_bulk_data:
                await StockMinutelyRepository.bulk_upsert(self.session, db_bulk_data)
        finally:
            self._is_running = False

    def is_running(self) -> bool:
        return self._is_running

    def _fetch_stock_price(self, code: str) -> list[tuple[str, datetime, float]]:
        try:
            now = get_current_unix_timestamp()
            end_time = now - make_minute_to_milisecond_timestamp(STOCK_COLLECT_END_TIME_MINUTE)
            start_time = now - make_minute_to_milisecond_timestamp(STOCK_COLLECT_START_TIME_MINUTE)

            url = f"https://api.polygon.io/v2/aggs/ticker/{code}/range/1/minute/{start_time}/{end_time}"

            params = {"adjusted": "true", "sort": "asc", "limit": 5000, "apiKey": POLYGON_API_KEY}
            response = requests.get(url, params=params)
            return self._parse_response_data(response, code)
        except Exception:
            return []

    def _parse_response_data(self, response: Response, code: str) -> list[tuple[str, datetime, float]]:
        if response.status_code != 200:
            return []

        stock_data = response.json()

        result = []
        stocks = stock_data.get("results", [])

        for record in stocks:
            current_datetime = transform_timestamp_datetime(record["t"])
            result.append((code, current_datetime, record["c"]))

        return result
