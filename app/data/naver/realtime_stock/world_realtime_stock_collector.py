import asyncio

import ray
from icecream import ic
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from app.common.util.time import get_now_datetime
from app.data.common.constant import STOCK_CACHE_SECOND
from app.data.yahoo.source.service import format_stock_code_naver
from app.module.asset.enum import Country
from app.module.asset.model import StockMinutely
from app.module.asset.redis_repository import RedisRealTimeStockRepository
from app.module.asset.repository.stock_minutely_repository import StockMinutelyRepository
from app.module.asset.schema import StockInfo
from database.dependency import get_mysql_session, get_redis_pool


@ray.remote
class WorldRealtimeStockCollector:
    def __init__(self, stock_code_list: list[StockInfo]):
        self.stock_code_list = stock_code_list
        self.redis_client = None
        self.session = None
        self._is_running = False
        self.driver: webdriver.Chrome = None

    async def collect(self):
        while True:
            await self._collect_data()

    async def _init_webdriver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    async def _setup(self):
        self.redis_client = get_redis_pool()
        async with get_mysql_session() as session:
            self.session = session

    async def _collect_data(self) -> None:
        if self.redis_client is None or self.session is None:
            await self._setup()

        if self.driver is None:
            # if self.driver is None or self.display is None:
            await self._init_webdriver()

        self._is_running = True
        try:
            now = get_now_datetime()
            code_price_pairs = []
            db_bulk_data = []
            fetch_tasks = []

            event_loop = asyncio.get_event_loop()

            for stockinfo in self.stock_code_list:
                try:
                    country = Country[stockinfo.country.upper().replace(" ", "_")]

                    stock_code = format_stock_code_naver(
                        stockinfo.code,
                        country,
                        stockinfo.market_index.upper(),
                    )

                    fetch_tasks.append(
                        event_loop.run_in_executor(None, self._fetch_stock_price, stock_code, stockinfo.code)
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

    def _fetch_stock_price(self, stock_code: str, code: str) -> tuple[str, float]:
        try:
            url = f"https://m.stock.naver.com/worldstock/stock/{stock_code}/total"
            self.driver.get(url)

            WebDriverWait(self.driver, 10).until(EC.text_to_be_present_in_element((By.ID, "content"), "종합"))

            element = self.driver.find_element(By.ID, "content")
            stock_price = self._parse_element(element)
            return code, stock_price
        except Exception:
            return code, 0.0

    def _parse_element(self, element: WebElement) -> float:
        try:
            div_children = element.find_elements(By.XPATH, "./div")
            table = div_children[0]
            text_items = table.text.splitlines()
            target_value = float(text_items[2].replace(",", ""))
            ic(target_value)
            float_values = []
            for item in text_items[:15]:
                value = float(item.replace(",", ""))

                if value != target_value and abs(value - target_value) / target_value <= 0.5:
                    float_values.append(value)

            closest_value = min(float_values, key=lambda x: abs(x - target_value)) if float_values else target_value
            return float(closest_value)
        except Exception:
            return 0.0
