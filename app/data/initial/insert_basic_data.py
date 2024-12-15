import asyncio
from datetime import date

from icecream import ic
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.common.services.rich_portfolio_file_service import RichPortfolioFileReader
from app.module.asset.constant import (
    ACCOUNT_TYPES,
    ASSET_FIELD,
    INVESTMENT_BANKS,
    PURCHASE_CURRENCY_TYPES,
    PURCHASE_DATES,
    STOCK_CODES,
    STOCK_QUANTITIES,
)
from app.module.asset.enum import AssetType, PurchaseCurrencyType, RichPeople, TradeType, Country
from app.module.asset.model import Asset, AssetField, AssetStock
from app.module.asset.repository.asset_field_repository import AssetFieldRepository
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.repository.stock_repository import StockRepository
from app.module.auth.constant import ADMIN_USER_ID, DUMMY_USER_ID
from app.module.auth.enum import ProviderEnum, UserRoleEnum
from app.module.auth.model import User
from app.module.auth.repository import UserRepository
from database.dependency import get_mysql_session


async def create_initial_users(session: AsyncSession):
    check_admin_user = await UserRepository.get(session, ADMIN_USER_ID)
    check_dummy_user = await UserRepository.get(session, DUMMY_USER_ID)

    if check_admin_user and check_dummy_user:
        return False

    if check_admin_user is None:
        admin_user = User(
            id=ADMIN_USER_ID,
            social_id="admin_social_id",
            provider=ProviderEnum.GOOGLE,
            role=UserRoleEnum.ADMIN,
            nickname="admin_user",
        )
        await UserRepository.create(session, admin_user)

    if check_dummy_user is None:
        dummy_user = User(
            id=DUMMY_USER_ID,
            social_id="dummy_social_id",
            provider=ProviderEnum.GOOGLE,
            nickname="dummy_user",
        )

        await UserRepository.create(session, dummy_user)

    ic("[create_initial_users] 성공적으로 admin과 더미 유저를 생성 했습니다.")

    return True


async def create_dummy_assets(session: AsyncSession):
    assets_exist = await AssetRepository.get_assets(session, DUMMY_USER_ID)
    if assets_exist:
        ic("이미 dummy assets을 저장하였습니다.")
        return

    stock_list = await StockRepository.get_by_codes(session, STOCK_CODES)
    stock_dict = {stock.code: stock for stock in stock_list}

    assets = []

    for i in range(len(STOCK_CODES)):
        stock = stock_dict.get(STOCK_CODES[i])
        if not stock:
            continue

        asset = Asset(
            asset_type=AssetType.STOCK.value,
            user_id=DUMMY_USER_ID,
        )

        AssetStock(
            trade_price=None,
            trade_date=PURCHASE_DATES[i],
            purchase_currency_type=PURCHASE_CURRENCY_TYPES[i],
            quantity=STOCK_QUANTITIES[i],
            trade=TradeType.BUY,
            investment_bank=INVESTMENT_BANKS[i],
            account_type=ACCOUNT_TYPES[i],
            asset=asset,
            stock=stock,
        )

        assets.append(asset)

    await AssetRepository.save_assets(session, assets)
    ic("[create_dummy_assets] 더미 유저에 assets을 성공적으로 생성 했습니다.")


async def create_asset_field(session: AsyncSession):
    asset_field = await AssetFieldRepository.get(session, DUMMY_USER_ID)
    if asset_field:
        ic("이미 asset_field를 저장하였습니다.")
        return

    fields_to_disable = ["stock_volume", "purchase_price", "purchase_amount"]
    field_preference = [field for field in ASSET_FIELD if field not in fields_to_disable]

    asset_field = AssetField(user_id=DUMMY_USER_ID, field_preference=field_preference)

    await AssetFieldRepository.save(session, asset_field)


async def add_rich_people(session: AsyncSession):
    for person_name in RichPeople:
        user = await UserRepository.get_by_name(session, person_name)
        if user:
            continue

        new_user = User(
            social_id=person_name.value, provider=person_name.value, role=UserRoleEnum.USER, nickname=person_name.value
        )

        await UserRepository.create(session, new_user)

    return


async def add_rich_portfolio(session: AsyncSession):
    rich_bundle_object = RichPortfolioFileReader.get_rich_portfolio_object_bundle()

    for person_name in RichPeople:
        rich_portfolio = rich_bundle_object.get(person_name)
        stock_codes = [code for code, _ in rich_portfolio.items()]
        stock_list = await StockRepository.get_by_codes(session, stock_codes)
        stock_dict = {stock.code: stock for stock in stock_list}

        bulk_assets = []
        user = await UserRepository.get_by_name(session, person_name)

        if not user:
            continue
        assets_exist = await AssetRepository.get_assets(session, user.id)
        if assets_exist:
            ic(f"이미 {person_name} 포트폴리오를 저장하였습니다.")
            return

        for stock_code in stock_codes:
            stock_number = rich_portfolio.get(stock_code)
            stock = stock_dict.get(stock_code)
    
    
            if stock and stock.country ==  Country.USA:
                asset = Asset(
                    asset_type=AssetType.STOCK.value,
                    user_id=user.id,
                )

                AssetStock(
                    trade_price=None,
                    trade_date=date(2024, 8, 16),
                    purchase_currency_type=PurchaseCurrencyType.USA.value,
                    quantity=stock_number,
                    trade=TradeType.BUY,
                    investment_bank=None,
                    account_type=None,
                    asset=asset,
                    stock=stock,
                )

                bulk_assets.append(asset)

        await AssetRepository.save_assets(session, bulk_assets)


async def main():
    async with get_mysql_session() as session:
        try:
            await create_initial_users(session)
        except Exception as err:
            ic(f"유저 생성 중 에러가 생겼습니다. {err=}")

        try:
            await create_dummy_assets(session)
        except Exception as err:
            ic(f"dummy asset 생성 중 에러가 생겼습니다. {err=}")

        try:
            await create_asset_field(session)
        except Exception as err:
            ic(f"asset_field 생성 중 에러가 생겼습니다. {err=}")

        try:
            await add_rich_people(session)
        except Exception as err:
            ic(f"부자 유저 추가 중에 에러가 생겼습니다. {err=}")

        try:
            await add_rich_portfolio(session)
        except Exception as err:
            ic(f"부자 포트폴리오 추가 중에 에러가 생겼습니다. {err=}")


if __name__ == "__main__":
    asyncio.run(main())
