from datetime import date, datetime, timedelta
from enum import StrEnum

import pandas as pd

from app.common.util.time import get_now_date, get_now_datetime
from app.module.asset.model import Asset


class EstimateDividendType(StrEnum):
    EVERY = "every"
    TYPE = "type"


class CompositionType(StrEnum):
    COMPOSITION = "composition"
    ACCOUNT = "account"

class IntervalType(StrEnum):
    ONEMONTH = "1month"
    THREEMONTH = "3month"
    SIXMONTH = "6month"
    ONEYEAR = "1year"

    def filter_assets_by_date(self, assets: list[Asset]) -> list[Asset]:
        start_date = self._get_start_date()
        if not len(assets):
            return []
        else:
            return [asset for asset in assets if asset.asset_stock.trade_date > start_date]

    def get_chart_month_interval(self) -> list[date]:
        if self == IntervalType.THREEMONTH:
            interval_months = 3
        elif self == IntervalType.SIXMONTH:
            interval_months = 6
        elif self == IntervalType.ONEYEAR:
            interval_months = 12
        else:
            interval_months = 12

        today = pd.Timestamp.today().normalize()
        start_date = (today - pd.DateOffset(months=interval_months - 1)).replace(day=1)

        dates = pd.date_range(start=start_date, end=today, freq="B")

        valid_months = {(start_date + pd.DateOffset(months=i)).month for i in range(interval_months)}

        return [d.date() for d in dates if d.month in valid_months]

    def get_chart_date_interval(self) -> list[date]:
        start_date = self._get_start_date()
        end_date = get_now_date()
        result = []

        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() not in (5, 6):
                result.append(current_date)
            current_date += timedelta(days=1)

        return result

    def _get_start_date(self) -> date:
        result = get_now_date() - timedelta(days=30)
        days_between = [(result + timedelta(days=i)).weekday() for i in range(5)]
        if 5 in days_between:
            result -= timedelta(days=1)
        if 6 in days_between:
            result -= timedelta(days=1)

        return result
