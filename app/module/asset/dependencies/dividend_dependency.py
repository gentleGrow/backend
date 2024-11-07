from app.module.asset.services.dividend_service import DividendService
from app.module.asset.services.exchange_rate_service import ExchangeRateService

exchange_rate_service = ExchangeRateService()


def get_dividend_service() -> DividendService:
    return DividendService(exchange_rate_service=exchange_rate_service)
