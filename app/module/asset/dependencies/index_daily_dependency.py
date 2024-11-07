from app.module.asset.services.index_daily_service import IndexDailyService


def get_index_daily_service() -> IndexDailyService:
    return IndexDailyService()