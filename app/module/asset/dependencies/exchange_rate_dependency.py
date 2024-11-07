from app.module.asset.services.exchange_rate_service import ExchangeRateService


def get_exchange_rate_service()->ExchangeRateService:
    return ExchangeRateService()
