import asyncio

import ray
import requests
from bs4 import BeautifulSoup

from app.common.util.time import get_now_datetime
from app.data.common.constant import MARKET_INDEX_CACHE_SECOND
from app.data.yahoo.source.constant import REALTIME_INDEX_COLLECTOR_WAIT_SECOND
from app.module.asset.enum import Country, MarketIndex
from app.module.asset.model import MarketIndexMinutely
from app.module.asset.redis_repository import RedisRealTimeMarketIndexRepository
from app.module.asset.repository.market_index_minutely_repository import MarketIndexMinutelyRepository
from app.module.asset.schema import MarketIndexData
from database.dependency import get_mysql_session, get_redis_pool


@ray.remote
class RealtimeIndexKoreaCollector:
    def __init__(self):
        self.redis_client = None
        self.session = None
        self._is_running = False

    async def _setup(self):
        self.redis_client = get_redis_pool()
        async with get_mysql_session() as session:
            self.session = session

    async def collect(self):
        if self.redis_client is None or self.session is None:
            await self._setup()
        try:
            while True:
                self._is_running = True
                kospi_data, kosdaq_data = await self._fetch_market_data()
                await self._save_market_data([kospi_data, kosdaq_data])
                await asyncio.sleep(REALTIME_INDEX_COLLECTOR_WAIT_SECOND)
                self._is_running = False
        except Exception:
            self._is_running = False

    async def _fetch_market_data(self):
        url = "https://finance.naver.com/"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        now = get_now_datetime()
        kospi_data = self._parse_kospi(soup, now)
        kosdaq_data = self._parse_kosdaq(soup, now)
        return kospi_data, kosdaq_data

    def _parse_kospi(self, soup: BeautifulSoup, now):
        try:
            kospi_area = soup.find("div", {"class": "kospi_area"})
            kospi_current_value = kospi_area.find("span", {"class": "num"}).text.strip().replace(",", "")
            kospi_change_value = kospi_area.find("span", {"class": "num2"}).text.strip().replace(",", "")
            num3_span = kospi_area.find("span", {"class": "num3"})
            percent_change = (
                num3_span.text.replace(num3_span.find("span", {"class": "blind"}).text, "").strip().replace("%", "")
            )

            market_index_data = MarketIndexData(
                country=Country.KOREA,
                name=MarketIndex.KOSPI,
                current_value=kospi_current_value,
                change_value=kospi_change_value,
                change_percent=percent_change,
                update_time="",
            )

            market_index_db = MarketIndexMinutely(
                name=MarketIndex.KOSPI, datetime=now, current_price=kospi_current_value
            )

            return {"db": market_index_db, "redis": market_index_data}
        except Exception:
            return

    def _parse_kosdaq(self, soup: BeautifulSoup, now):
        section_stock_market = soup.find("div", {"class": "section_stock_market"})
        kosdaq_area = section_stock_market.find("div", {"class": "kosdaq_area"})
        kosdaq_current_value = kosdaq_area.find("span", {"class": "num"}).text.strip().replace(",", "")
        kosdaq_change_value = kosdaq_area.find("span", {"class": "num2"}).text.strip().replace(",", "")
        num3_span = kosdaq_area.find("span", {"class": "num3"})
        percent_change = "".join(num3_span.stripped_strings).replace("%", "").strip()

        market_index_data = MarketIndexData(
            country=Country.KOREA,
            name=MarketIndex.KOSDAQ,
            current_value=kosdaq_current_value,
            change_value=kosdaq_change_value,
            change_percent=percent_change,
            update_time="",
        )

        market_index_db = MarketIndexMinutely(name=MarketIndex.KOSDAQ, datetime=now, current_price=kosdaq_current_value)

        return {"db": market_index_db, "redis": market_index_data}

    async def _save_market_data(self, market_data_list):
        db_bulk_data = []
        redis_bulk_data = []

        for market_data in market_data_list:
            db_bulk_data.append(market_data["db"])
            redis_bulk_data.append((market_data["redis"].name, market_data["redis"].model_dump_json()))

        await MarketIndexMinutelyRepository.bulk_upsert(self.session, db_bulk_data)
        await RedisRealTimeMarketIndexRepository.bulk_save(
            self.redis_client, redis_bulk_data, expire_time=MARKET_INDEX_CACHE_SECOND
        )

    def is_running(self) -> bool:
        return self._is_running
