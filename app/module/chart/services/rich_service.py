import json
from collections import defaultdict

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.module.asset.enum import AssetType, RichPeople
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.services.asset.asset_query import AssetQuery
from app.module.asset.services.asset_service import AssetService
from app.module.auth.repository import UserRepository
from app.module.chart.constant import REDIS_RICH_PICK_KEY, REDIS_RICH_PICK_NAME_KEY, RICH_PICK_SECOND
from app.module.chart.redis_repository import RedisRichPickRepository
from app.module.chart.schema import PortfolioStockData, RichPortfolioValue


class RichService:
    def __init__(self, asset_service: AssetService, asset_query: AssetQuery):
        self.asset_service = asset_service
        self.asset_query = asset_query

    async def get_rich_top_10_pick(self, session: AsyncSession, redis_client: Redis) -> tuple:
        top_10_stock_codes = await RedisRichPickRepository.get(redis_client, REDIS_RICH_PICK_KEY)
        stock_name_map = await RedisRichPickRepository.get(redis_client, REDIS_RICH_PICK_NAME_KEY)

        # 임시 변수 할당, 추후 변경 예정
        RichPeople = []  # type: ignore

        if top_10_stock_codes is None or stock_name_map is None:
            stock_count: defaultdict = defaultdict(int)
            new_stock_name_map: dict[str, str] = {}
            for person in RichPeople:
                user = await UserRepository.get_by_name(session, person)
                if user is None:
                    continue

                assets = await AssetRepository.get_eager(session, user.id, AssetType.STOCK)
                for asset in assets:
                    stock_code = asset.asset_stock.stock.code
                    stock_count[stock_code] += 1
                    new_stock_name_map[stock_code] = asset.asset_stock.stock.name_kr

            new_top_10_stock_codes: list[str] = [
                stock[0] for stock in sorted(stock_count.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            await RedisRichPickRepository.save(
                redis_client, REDIS_RICH_PICK_KEY, json.dumps(new_top_10_stock_codes), RICH_PICK_SECOND
            )
            await RedisRichPickRepository.save(
                redis_client, REDIS_RICH_PICK_NAME_KEY, json.dumps(new_stock_name_map), RICH_PICK_SECOND
            )
            return new_top_10_stock_codes, new_stock_name_map
        else:
            return top_10_stock_codes, stock_name_map

    async def get_rich_portfolio_chart_data(
        self, session: AsyncSession, redis_client: Redis
    ) -> list[PortfolioStockData]:
        result = []
        for person_name in RichPeople:
            user = await UserRepository.get_by_name(session, person_name)
            if not user:
                continue

            assets = await AssetRepository.get_assets(session, user.id)
            if not len(assets):
                continue

            (
                stock_daily_map,
                lastest_stock_daily_map,
                dividend_map,
                exchange_rate_map,
                current_stock_price_map,
            ) = await self.asset_query.get_all_data(session, redis_client, assets)

            asset_percentage = self.asset_service.get_asset_percentages(
                assets, current_stock_price_map, exchange_rate_map
            )

            result.append(
                RichPortfolioValue(
                    name=person_name,
                    data=[PortfolioStockData(name=code, percent_ratio=rate) for code, rate in asset_percentage.items()],
                )
            )

        return result
