import asyncio
import os
from dotenv import load_dotenv

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from app.module.asset.constant import COUNTRY_TRANSLATIONS, INDEX_NAME_TRANSLATIONS
from app.module.asset.schema import MarketIndexData

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)

logger = logging.getLogger("current_index")
logger.setLevel(logging.INFO)

if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/current_index.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


class IndexWorldCollector:
    def __init__(self):
        self.driver = None
        self.display = None


    async def get_current_index(self) -> list[tuple[str, str]]:
        if not self.display or not self.driver:
            await self._init_webdriver()

        return await self._fetch_market_data()


    async def _fetch_market_data(self) -> list[tuple[str, str]]:
        try:
            # 수집 경로는 별도 환경변수에 추가 할 예정입니다
            self.driver.get("https://finance.naver.com/world/")
            result = []

            america_index_table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "americaIndex"))
            )

            tr_rows = america_index_table.find_elements(By.XPATH, ".//thead/tr")

            for tr_row in tr_rows:
                try:
                    market_data = self._parse_tr_row(tr_row)
                    if market_data:
                        result.append(market_data)
                except Exception as e:
                    logger.error(e)
                    continue

            return result
        except Exception:
            return []


    def _parse_tr_row(self, tr_row) -> tuple[str, str] | None:
        tds = tr_row.find_elements(By.TAG_NAME, "td")
        tr_row_data = []

        for td in tds:
            if "graph" in td.get_attribute("class"):
                continue

            span = td.find_elements(By.TAG_NAME, "span")
            if span:
                tr_row_data.append(span[0].text)
            else:
                a_elements = td.find_elements(By.TAG_NAME, "a")
                if a_elements:
                    tr_row_data.append(a_elements[0].text)
                else:
                    tr_row_data.append(td.text)

        if tr_row_data:
            country_kr = tr_row_data[0]
            if country_kr in COUNTRY_TRANSLATIONS:
                country_en = COUNTRY_TRANSLATIONS[country_kr]
            else:
                return None

            name_kr = tr_row_data[1]
            name_en = INDEX_NAME_TRANSLATIONS.get(name_kr, name_kr)

            current_value = tr_row_data[2].strip().replace(",", "")
            change_value = tr_row_data[3].strip().replace(",", "")
            change_percent = tr_row_data[4].strip().replace("%", "")

            market_index = MarketIndexData(
                country=country_en,
                name=name_en,
                current_value=current_value,
                change_value=change_value,
                change_percent=change_percent,
                update_time=tr_row_data[5],
            )
        
            return (name_en, market_index.model_dump_json())
        return None


    async def _init_webdriver(self):
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()

        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument("--enable-automation")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

