from app.module.chart.services.portfolio_service import PortfolioService


def get_portfolio_service() -> PortfolioService:
    return PortfolioService()
