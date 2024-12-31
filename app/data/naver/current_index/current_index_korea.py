import asyncio
import os
from dotenv import load_dotenv
from app.module.asset.enum import MarketIndex
import requests
from bs4 import BeautifulSoup

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

logger = logging.getLogger("current_index")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_index.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)



class IndexKoreaCollector:
    async def get_current_index(self) -> list[tuple[str, float]]:
        # 경로는 환경 변수로 분리합니다
        url = "https://finance.naver.com/"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        kospi_data = self._parse_kospi(soup)
        kosdaq_data = self._parse_kosdaq(soup)
        return [data for data in [kospi_data, kosdaq_data] if data is not None]
    

    def _parse_kosdaq(self, soup: BeautifulSoup) -> tuple[str, float] | None:
        try:
            section_stock_market = soup.find("div", {"class": "section_stock_market"})
            kosdaq_area = section_stock_market.find("div", {"class": "kosdaq_area"})
            kosdaq_current_value = kosdaq_area.find("span", {"class": "num"}).text.strip().replace(",", "")

            return (MarketIndex.KOSDAQ, float(kosdaq_current_value))
        except Exception as e:
            logger.error(e)
            return None


    def _parse_kospi(self, soup: BeautifulSoup) -> tuple[str, float] | None:
        try:
            kospi_area = soup.find("div", {"class": "kospi_area"})
            kospi_current_value = kospi_area.find("span", {"class": "num"}).text.strip().replace(",", "")
            
            return (MarketIndex.KOSPI, float(kospi_current_value))
        except Exception as e:
            logger.error(e)
            return None





