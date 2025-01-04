import logging
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from app.common.util.time import get_now_datetime
from app.module.asset.enum import Country, MarketIndex
from app.module.asset.model import MarketIndexMinutely
from app.module.asset.schema import MarketIndexData
from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", None)

logger = logging.getLogger("current_index")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_index.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


class IndexKoreaCollector:
    async def get_current_index(self) -> tuple[list[tuple[str, str]], list[MarketIndexMinutely]] | tuple[None, None]:
        url = "https://finance.naver.com/"
        response = await requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        redis_kospi_data, db_kospi_data = await self._parse_kospi(soup)
        redis_kosdaq_data, db_kosdaq_data = await self._parse_kosdaq(soup)
        return [data for data in [redis_kospi_data, redis_kosdaq_data] if data], [
            data for data in [db_kospi_data, db_kosdaq_data] if data
        ]

    async def _parse_kosdaq(
        self, soup: BeautifulSoup
    ) -> tuple[tuple[str, str], MarketIndexMinutely] | tuple[None, None]:
        try:
            section_stock_market = soup.find("div", {"class": "section_stock_market"})
            kosdaq_area = section_stock_market.find("div", {"class": "kosdaq_area"})
            kosdaq_current_value = kosdaq_area.find("span", {"class": "num"}).text.strip().replace(",", "")
            kosdaq_change_value = kosdaq_area.find("span", {"class": "num2"}).text.strip().replace(",", "")
            num3_span = kosdaq_area.find("span", {"class": "num3"})
            percent_change = "".join(num3_span.stripped_strings).replace("%", "").strip()

            now = get_now_datetime()

            market_index_data = MarketIndexData(
                country=Country.KOREA,
                name=MarketIndex.KOSDAQ,
                current_value=float(kosdaq_current_value),
                change_value=float(kosdaq_change_value),
                change_percent=float(percent_change),
                update_time="",
            )

            market_index_db = MarketIndexMinutely(name=MarketIndex.KOSDAQ, datetime=now, price=kosdaq_current_value)
            return (MarketIndex.KOSDAQ, market_index_data.model_dump_json()), market_index_db
        except Exception as e:
            logger.error(e)
            return None, None

    async def _parse_kospi(
        self, soup: BeautifulSoup
    ) -> tuple[tuple[str, str], MarketIndexMinutely] | tuple[None, None]:
        try:
            kospi_area = soup.find("div", {"class": "kospi_area"})
            kospi_current_value = kospi_area.find("span", {"class": "num"}).text.strip().replace(",", "")
            kospi_change_value = kospi_area.find("span", {"class": "num2"}).text.strip().replace(",", "")
            num3_span = kospi_area.find("span", {"class": "num3"})
            percent_change = (
                num3_span.text.replace(num3_span.find("span", {"class": "blind"}).text, "").strip().replace("%", "")
            )
            now = get_now_datetime()

            market_index_data = MarketIndexData(
                country=Country.KOREA,
                name=MarketIndex.KOSPI,
                current_value=kospi_current_value,
                change_value=kospi_change_value,
                change_percent=percent_change,
                update_time="",
            )

            market_index_db = MarketIndexMinutely(name=MarketIndex.KOSPI, datetime=now, price=kospi_current_value)

            return (MarketIndex.KOSPI, market_index_data.model_dump_json()), market_index_db
        except Exception as e:
            logger.error(e)
            return None, None
