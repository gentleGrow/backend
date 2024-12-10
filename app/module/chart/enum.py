from datetime import date, datetime, timedelta
from enum import StrEnum

from dateutil.relativedelta import relativedelta
from app.module.asset.model import Asset
from app.common.util.time import get_now_date, get_now_datetime


class EstimateDividendType(StrEnum):
    EVERY = "every"
    TYPE = "type"


class CompositionType(StrEnum):
    COMPOSITION = "composition"
    ACCOUNT = "account"


class IntervalType(StrEnum):
    FIVEDAY = "5day"
    ONEMONTH = "1month"
    THREEMONTH = "3month"
    SIXMONTH = "6month"
    ONEYEAR = "1year"

    def filter_assets_by_date(self, assets:list[Asset]) -> list[Asset]:
        start_date = self._get_start_date()
        if not len(assets):
            return []
        else:
            return [asset for asset in assets if asset.asset_stock.trade_date > start_date]

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
        if self == IntervalType.FIVEDAY:
            timediff = 4
        elif self == IntervalType.ONEMONTH:
            timediff = 30
        elif self == IntervalType.THREEMONTH:
            timediff = 90
        elif self == IntervalType.SIXMONTH:
            timediff = 180
        elif self == IntervalType.ONEYEAR:
            timediff = 365
        else:
            timediff = 30

        result = get_now_date() - timedelta(days=timediff)
        days_between = [(result + timedelta(days=i)).weekday() for i in range(5)]
        if 5 in days_between:
            result -= timedelta(days=1)
        if 6 in days_between:
            result -= timedelta(days=1)

        return result


    def get_chart_datetime_interval(self) -> list[datetime]:
        start_datetime = self._get_start_datetime()
        end_datetime = get_now_datetime().replace(hour=0, minute=0)
        result = []

        current_datetime = start_datetime
        while current_datetime <= end_datetime:
            if current_datetime.weekday() not in (5, 6):
                result.append(current_datetime)
            current_datetime += timedelta(minutes=30)
    
        return result


    def _get_start_datetime(self) -> date:
        if self == IntervalType.FIVEDAY:
            timediff = 4
        elif self == IntervalType.ONEMONTH:
            timediff = 30
        elif self == IntervalType.THREEMONTH:
            timediff = 90
        elif self == IntervalType.SIXMONTH:
            timediff = 180
        elif self == IntervalType.ONEYEAR:
            timediff = 365
        else:
            timediff = 30

        result = get_now_datetime().replace(hour=0, minute=0) - timedelta(days=timediff)
        days_between = [(result + timedelta(days=i)).weekday() for i in range(5)]
        if 5 in days_between:
            result -= timedelta(days=1)
        if 6 in days_between:
            result -= timedelta(days=1)

        return result



    def get_days(self) -> int:
        if self == IntervalType.FIVEDAY:
            return 7
        elif self == IntervalType.ONEMONTH:
            return 30
        return 5

    def get_start_end_time(self) -> tuple[date | datetime, date | datetime]:
        if self == IntervalType.FIVEDAY:
            end_datetime = get_now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
            start_datetime = end_datetime - timedelta(days=4)
            days_between = [(start_datetime + timedelta(days=i)).weekday() for i in range(5)]
            if 5 in days_between:
                start_datetime -= timedelta(days=1)
            if 6 in days_between:
                start_datetime -= timedelta(days=1)
            return start_datetime, end_datetime
        elif self == IntervalType.ONEMONTH:
            end_date = get_now_date()
            return end_date - timedelta(days=(7 * 4) + 1), end_date
        elif self == IntervalType.THREEMONTH:
            end_date = get_now_date()
            return end_date - relativedelta(months=2), end_date
        elif self == IntervalType.SIXMONTH:
            end_date = get_now_date()
            return end_date - relativedelta(months=5), end_date
        elif self == IntervalType.ONEYEAR:
            end_date = get_now_date()
            return end_date - relativedelta(months=11), end_date
        return get_now_date(), get_now_date()

    def get_interval(self) -> int:
        if self == IntervalType.FIVEDAY:
            return 30
        elif self == IntervalType.ONEMONTH:
            return 60 * 24 * 30
        elif self == IntervalType.THREEMONTH:
            return 60 * 24 * 30
        elif self == IntervalType.SIXMONTH:
            return 60 * 24 * 30
        elif self == IntervalType.ONEYEAR:
            return 60 * 24 * 30
        return 1

