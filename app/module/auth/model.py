from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.mixin.timestamp import TimestampMixin
from app.module.auth.enum import UserRoleEnum
from database.config import MySQLBase


class User(TimestampMixin, MySQLBase):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    social_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum), default=UserRoleEnum.USER)
    nickname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)

    event_consents: Mapped[List["UserEventConsent"]] = relationship("UserEventConsent", back_populates="user")


class UserEventConsent(TimestampMixin, MySQLBase):
    __tablename__ = "user_event_consent"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship("User", back_populates="event_consents")
