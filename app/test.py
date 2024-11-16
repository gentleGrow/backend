import asyncio

import ray
import yfinance
from aiolimiter import AsyncLimiter

from app.common.util.time import get_now_datetime
from app.data.common.constant import STOCK_CACHE_SECOND
from app.data.yahoo.source.service import format_stock_code
from app.module.asset.enum import Country
from app.module.asset.model import StockMinutely
from app.module.asset.redis_repository import RedisRealTimeStockRepository
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_mysql_session, get_redis_pool


@ray.remote
class RealtimeStockCollector:
    def __init__(self, stock_code_list: list[StockInfo], rate_limit: int = 5):
        """
        Args:
            stock_code_list (list[StockInfo]): 대상 주식 코드 리스트
            rate_limit (int): 초당 최대 요청 수
        """
        self.stock_code_list = stock_code_list
        self.redis_client = None
        self.session = None
        self._is_running = False
        self.rate_limiter = AsyncLimiter(rate_limit, time_period=1)  # 초당 최대 요청 수 설정

    async def _setup(self):
        self.redis_client = get_redis_pool()
        async with get_mysql_session() as session:
            self.session = session

    async def collect(self):
        while True:
            await self._collect_data()

    async def _collect_data(self) -> None:
        if self.redis_client is None or self.session is None:
            await self._setup()

        self._is_running = True
        try:
            now = get_now_datetime()
            code_price_pairs = []
            db_bulk_data = []
            fetch_tasks = []

            for stockinfo in self.stock_code_list:
                try:
                    country = Country[stockinfo.country.upper().replace(" ", "_")]
                    stock_code = format_stock_code(
                        stockinfo.code,
                        country,
                        stockinfo.market_index.upper(),
                    )
                    # 비동기 작업 생성 시 rate limiter 적용
                    fetch_tasks.append(self._fetch_stock_price_with_limit(stock_code, stockinfo.code))
                except Exception:
                    continue

            task_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            code_price_pairs = [result for result in task_results if not isinstance(result, Exception)]
            redis_bulk_data = [(code, price) for code, price in code_price_pairs if price]

            for code, price in redis_bulk_data:
                current_stock_data = StockMinutely(code=code, datetime=now, current_price=price)
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

    async def _fetch_stock_price_with_limit(self, stock_code: str, code: str) -> tuple[str, float]:
        """Rate Limit을 적용한 비동기 요청"""
        async with self.rate_limiter:
            return await asyncio.to_thread(self._fetch_stock_price, stock_code, code)

    def _fetch_stock_price(self, stock_code: str, code: str) -> tuple[str, float]:
        try:
            stock = yfinance.Ticker(stock_code)

            info_currentPrice = stock.info.get("currentPrice")
            info_bid = stock.info.get("bid")
            info_ask = stock.info.get("ask")
            current_price = info_currentPrice or info_bid or info_ask

            return code, current_price if current_price is not None else 0.0
        except Exception:
            return code, 0.0
