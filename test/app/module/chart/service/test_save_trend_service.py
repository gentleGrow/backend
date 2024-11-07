from app.common.util.time import get_now_datetime
from app.module.chart.services.save_trend_service import SaveTrendService
from app.module.chart.dependencies.save_trend_dependency import get_save_trend_service

class TestSaveTrendService:
    def test_get_x_axises(self):
        # Given
        save_trend_service:SaveTrendService = get_save_trend_service()
        years = 5
        current_year_short = int(str(get_now_datetime().year)[-2:])

        # When
        x_axises = save_trend_service.get_x_axises(years)

        # Then
        expected_x_axises = [f"{i + current_year_short + 1}" for i in range(years)]
        assert x_axises == expected_x_axises

    def test_get_dates(self):
        # Given
        save_trend_service:SaveTrendService = get_save_trend_service()
        years = 5

        # When
        dates = save_trend_service.get_dates(years)

        # Then
        expected_dates = [f"{i + 1}년후" for i in range(years)]
        assert dates == expected_dates, f"Expected {expected_dates}, but got {dates}"
