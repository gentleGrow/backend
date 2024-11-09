from app.module.asset.services.index_minutely_service import IndexMinutelyService


def get_index_minutely_service() -> IndexMinutelyService:
    return IndexMinutelyService()
