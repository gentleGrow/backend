import asyncio
import json
import logging
from datetime import date
from os import getenv

from celery import shared_task
from dotenv import load_dotenv
from redis.asyncio import Redis
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy.ext.asyncio import AsyncSession
from webdriver_manager.chrome import ChromeDriverManager

from app.data.investing.sources.enum import RicePeople
from app.module.asset.enum import AssetType, PurchaseCurrencyType, TradeType
from app.module.asset.model import Asset, AssetStock
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_repository import StockRepository
from app.module.asset.services.stock_service import StockService
from app.module.auth.enum import ProviderEnum
from app.module.auth.model import User
from app.module.auth.repository import UserRepository
from app.module.chart.constant import TIP_EXPIRE_SECOND
from app.module.chart.redis_repository import RedisRichPortfolioRepository
from database.dependency import get_mysql_session, get_redis_pool

load_dotenv()
ENVIRONMENT = getenv("ENVIRONMENT", None)


logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",  
    handlers=[
        logging.FileHandler("rich_portfolio.log"), 
        logging.StreamHandler(),  
    ],
)


async def fetch_rich_porfolio(redis_client: Redis, session: AsyncSession, person: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(f"https://kr.investing.com/pro/ideas/{person}")

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//div[@id='root']//table//tr//th[contains(text(),'Ticker')]"))
    )

    tbody = driver.find_element(By.XPATH, "//div[@id='root']//table//tbody")
    rows = tbody.find_elements(By.TAG_NAME, "tr")

    stock_codes = []
    percentages = {}

    for row in rows:
        columns = row.find_elements(By.TAG_NAME, "td")

        for index, column in enumerate(columns):
            try:
                a_tag = column.find_element(By.TAG_NAME, "a")
                if a_tag:
                    if index == 0:
                        code = a_tag.get_attribute("textContent")
                        stock_codes.append(code)
                    elif index == 3:
                        percentage = a_tag.get_attribute("textContent")
                        percentages[code] = percentage
            except Exception:
                continue

    stock_service = StockService()
    stock_name_map = await stock_service.get_stock_name_map_by_codes(session, stock_codes)

    name_percentage = {}

    for code, percentage in percentages.items():
        stock_name = stock_name_map.get(code)
        if stock_name:
            name_percentage[stock_name] = percentages[code]

    await RedisRichPortfolioRepository.save(redis_client, person, json.dumps(name_percentage), TIP_EXPIRE_SECOND)

    user = await UserRepository.get_by_name(session, person)

    if user is None:
        person_user = User(social_id=f"{person}_id", provider=ProviderEnum.GOOGLE, nickname=person)
        user = await UserRepository.create(session, person_user)

    eager_assets = await AssetRepository.get_eager(session, user.id, AssetType.STOCK)

    for remove_asset in eager_assets:
        await AssetRepository.delete_asset(session, remove_asset.id)

    stock_list = await StockRepository.get_by_codes(session, stock_codes)
    stock_dict = {stock.code: stock for stock in stock_list}

    bulk_assets = []

    for stock in stock_codes:
        stock = stock_dict.get(stock)

        if not stock:
            continue

        asset = Asset(
            asset_type=AssetType.STOCK.value,
            user_id=user.id,
        )

        AssetStock(
            trade_price=None,
            trade_date=date(2024, 9, 13),
            purchase_currency_type=PurchaseCurrencyType.USA.value,
            quantity=1,
            trade=TradeType.BUY,
            investment_bank=None,
            account_type=None,
            asset=asset,
            stock=stock,
        )
        bulk_assets.append(asset)

    await AssetRepository.save_assets(session, bulk_assets)

    driver.quit()


async def execute_async_task():
    logging.info('부자 포트폴리오 수집을 시작합니다.')
    redis_client = get_redis_pool()
    async with get_mysql_session() as session:
        for person in RicePeople:
            await fetch_rich_porfolio(redis_client, session, person.value)

        logging.info('부자 포트폴리오 수집을 마칩니다.')

@shared_task
def main():
    asyncio.run(execute_async_task())


if __name__ == "__main__":
    asyncio.run(execute_async_task())
