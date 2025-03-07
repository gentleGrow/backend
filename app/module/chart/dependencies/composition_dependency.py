from app.module.asset.services.exchange_rate_service import ExchangeRateService
from app.module.chart.services.composition_service import CompositionService

exchange_rate_service = ExchangeRateService()


def get_composition_service() -> CompositionService:
    return CompositionService(exchange_rate_service=exchange_rate_service)
