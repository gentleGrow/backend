import json
from collections import defaultdict

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.investing.sources.enum import RicePeople
from app.module.asset.enum import AssetType
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.auth.repository import UserRepository
from app.module.chart.constant import REDIS_RICH_PICK_KEY, REDIS_RICH_PICK_NAME_KEY, RICH_PICK_SECOND
from app.module.chart.redis_repository import RedisRichPickRepository


class RichFacade:
    @staticmethod
    async def get_rich_top_10_pick(session: AsyncSession, redis_client: Redis) -> tuple[list[str], dict[str, str]]:
        top_10_stock_codes: list[str] | None = await RedisRichPickRepository.get(redis_client, REDIS_RICH_PICK_KEY)  # type: ignore
        stock_name_map: dict[str, str] | None = await RedisRichPickRepository.get(  # type: ignore
            redis_client, REDIS_RICH_PICK_NAME_KEY
        )

        if top_10_stock_codes is None or stock_name_map is None:
            stock_count: defaultdict = defaultdict(int)
            new_stock_name_map: dict[str, str] = {}
            for person in RicePeople:
                user = await UserRepository.get_by_name(session, person)
                if user is None:
                    continue
                assets = await AssetRepository.get_eager(session, user.id, AssetType.STOCK)
                for asset in assets:
                    stock_code = asset.asset_stock.stock.code
                    stock_count[stock_code] += 1
                    new_stock_name_map[stock_code] = asset.asset_stock.stock.name

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
