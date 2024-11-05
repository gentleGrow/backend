from datetime import datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.util.time import get_date_past_day
from app.module.asset.enum import AssetType
from app.module.asset.model import Asset
from app.module.asset.repository.asset_repository import AssetRepository
from app.module.asset.services.asset_service import AssetService
from app.module.asset.services.asset_stock_service import AssetStockService
from app.module.chart.constant import PAST_MONTH_DAY, FULL_PERCENTAGE_RATE


class SummaryFacade:
    @staticmethod
    async def get_today_review_rate(
        session: AsyncSession, redis_client: Redis, user_id: int, asset_service: AssetService
    ) -> float:
        assets: list[Asset] = await AssetRepository.get_eager(session, user_id, AssetType.STOCK)
        past_assets = [
            asset
            for asset in assets
            if asset.asset_stock.purchase_date <= datetime.now().date() - timedelta(days=PAST_MONTH_DAY)
        ]

        if len(past_assets) == 0 and len(assets) > 0:
            return FULL_PERCENTAGE_RATE
 
        past_date = get_date_past_day(PAST_MONTH_DAY)

        past_total_amount = await asset_service.get_total_asset_amount_with_date_temp(
            session, redis_client, past_assets, past_date
        )
        
        current_total_amount = await asset_service.get_total_asset_amount(session, redis_client, assets)

        return AssetStockService.get_total_profit_rate(current_total_amount, past_total_amount)

