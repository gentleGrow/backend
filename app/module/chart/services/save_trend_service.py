from app.common.util.time import get_now_datetime


class SaveTrendService:
    def get_x_axises(self, years: int) -> list[str]:
        current_year_short = int(str(get_now_datetime().year)[-2:])
        return [f"{i + current_year_short + 1}" for i in range(years)]

    def get_dates(self, years: int) -> list[str]:
        return [f"{i + 1}년후" for i in range(years)]
