from app.common.util.time import get_now_datetime


class SaveTrendService:
    @staticmethod
    def get_x_axises(years: int) -> list[str]:
        current_year_short = int(str(get_now_datetime().year)[-2:])
        return [f"{i + current_year_short + 1}" for i in range(years)]

    @staticmethod
    def get_dates(years: int) -> list[str]:
        return [f"{i + 1}년후" for i in range(years)]
