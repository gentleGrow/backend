from app.module.chart.services.save_trend_service import SaveTrendService


def get_save_trend_service() -> SaveTrendService:
    return SaveTrendService()