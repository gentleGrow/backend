from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Boolean, Column, DateTime

KST = ZoneInfo("Asia/Seoul")


def current_time_kst():
    return datetime.now(KST)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=current_time_kst, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=current_time_kst,
        onupdate=current_time_kst,
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
