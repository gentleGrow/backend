from sqlalchemy import BigInteger, Column, Enum, String
from sqlalchemy.orm import relationship

from app.common.mixin.timestamp import TimestampMixin
from app.module.auth.enum import UserRoleEnum
from database.config import MySQLBase


class User(TimestampMixin, MySQLBase):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    social_id = Column(String(255), index=True, nullable=False)
    provider = Column(String(50), nullable=False)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER)
    nickname = Column(String(255), nullable=True, unique=True)
    email = Column(String(255), nullable=True, unique=True)
