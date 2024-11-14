import asyncio
import ray
import requests
import re
from bs4 import BeautifulSoup

from app.common.util.time import get_now_datetime
from app.data.common.constant import STOCK_CACHE_SECOND
from app.module.asset.model import StockMinutely
from app.module.asset.redis_repository import RedisRealTimeStockRepository
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_mysql_session, get_redis_pool

from icecream import ic

@ray.remote
class KoreaRealtimeStockCollector:
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
            now = get_now_datetime()
            code_price_pairs = []
            db_bulk_data = []
            fetch_tasks = []

            event_loop = asyncio.get_event_loop()

            for stockinfo in self.stock_code_list:
                try:
                    fetch_tasks.append(
                        event_loop.run_in_executor(None, self._fetch_stock_price, stockinfo.code)
                    )
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

    def _fetch_stock_price(self, code: str) -> tuple[str, float]:
        try:
            url = f"https://finance.naver.com/item/main.naver?code={code}"
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            current_price = self._parse_content(soup)
            return code, current_price
        except Exception:
            return code, 0.0


    def _parse_content(self, soup:BeautifulSoup) -> int:
        try:
            middle_content = soup.find(id="middle")
            content_area = middle_content.find(id="content")
            chart_area = content_area.find(id="chart_area")
            rate_info = chart_area.find(class_="rate_info")
            today_info = rate_info.find(class_="today")
            no_today = today_info.find("p", class_="no_today")
            
            em_price = no_today.find("em", class_=["no_up", "no_down"])
            blind_span = em_price.find("span", class_="blind")
            filtered_text = re.sub(r"\D", "", blind_span.get_text())
            return int(filtered_text)
        except Exception:
            return 0