from datetime import datetime as dt
from typing import List
from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.mixin.timestamp import TimestampMixin
from database.config import MySQLBase

class AssetField(TimestampMixin, MySQLBase):
    __tablename__ = "asset_field"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    field_preference: Mapped[JSON] = mapped_column(JSON, nullable=False, default=list)


class Dividend(TimestampMixin, MySQLBase):
    __tablename__ = "dividend"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dividend: Mapped[float] = mapped_column(Float, nullable=False, info={"description": "배당금"})
    code: Mapped[str] = mapped_column(String(255), ForeignKey("stock.code"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, info={"description": "배당일자"})

    stock: Mapped["Stock"] = relationship(back_populates="dividend")

    __table_args__ = (UniqueConstraint("code", "date", name="uq_code_date"),)


class AssetStock(TimestampMixin, MySQLBase):
    __tablename__ = "asset_stock"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_type: Mapped[str] = mapped_column(String(255), nullable=True, info={"description": "계좌 종류"})
    investment_bank: Mapped[str] = mapped_column(String(255), nullable=True, info={"description": "증권사"})
    purchase_currency_type: Mapped[str] = mapped_column(String(255), nullable=True, info={"description": "구매 통화"})
    trade_date: Mapped[Date] = mapped_column(Date, nullable=True, info={"description": "매매일자"})
    trade_price: Mapped[float] = mapped_column(Float, nullable=True, info={"description": "거래가"})
    quantity: Mapped[int] = mapped_column(Integer, nullable=True, info={"description": "구매수량"})
    trade: Mapped[str] = mapped_column(String(255), nullable=True, info={"description": "매매, 매수/매도"}, default="BUY")

    stock_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("stock.id"), primary_key=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), primary_key=True)

    asset: Mapped["Asset"] = relationship(back_populates="asset_stock", uselist=False, overlaps="stock,asset", lazy="selectin")
    stock: Mapped["Stock"] = relationship(back_populates="asset_stock", overlaps="asset,stock", lazy="selectin")


class Asset(TimestampMixin, MySQLBase):
    __tablename__ = "asset"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_type: Mapped[str] = mapped_column(String(255), nullable=False, info={"description": "자산 종류"})
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    stock: Mapped[List["Stock"]] = relationship(
        secondary="asset_stock", back_populates="asset", overlaps="asset_stock", lazy="selectin"
    )
    asset_stock: Mapped["AssetStock"] = relationship(
        back_populates="asset", uselist=False, overlaps="stock", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_user_id_asset_type_deleted_at", "user_id", "asset_type", "deleted_at"),
    )


class Stock(TimestampMixin, MySQLBase):
    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    country: Mapped[str] = mapped_column(String(255), nullable=False)
    market_index: Mapped[str] = mapped_column(String(255), nullable=False)
    name_kr: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)

    asset: Mapped[List["Asset"]] = relationship(
        secondary="asset_stock", back_populates="stock", overlaps="asset_stock", lazy="select"
    )
    asset_stock: Mapped[List["AssetStock"]] = relationship(
        back_populates="stock", overlaps="asset", lazy="select"
    )
    dividend: Mapped[List["Dividend"]] = relationship(back_populates="stock")
    stock_daily: Mapped[List["StockDaily"]] = relationship(back_populates="stock")

    __table_args__ = (
        Index("idx_country", "country"),
    )


class StockDaily(TimestampMixin, MySQLBase):
    __tablename__ = "stock_daily"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    adj_close_price: Mapped[float] = mapped_column(Float, nullable=False, info={"description": "Adjusted closing price of the stock"})
    close_price: Mapped[float] = mapped_column(Float, nullable=False, info={"description": "Closing price of the stock"})
    code: Mapped[str] = mapped_column(String(255), ForeignKey("stock.code"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, info={"description": "stock closing day"})
    highest_price: Mapped[float] = mapped_column(Float, nullable=False, info={"description": "Highest price of the stock"})
    lowest_price: Mapped[float] = mapped_column(Float, nullable=False, info={"description": "Lowest price of the stock"})
    opening_price: Mapped[float] = mapped_column(Float, nullable=False, info={"description": "Opening price of the stock"})
    trade_volume: Mapped[int] = mapped_column(BigInteger, nullable=False, info={"description": "Volume of stock traded"})

    stock: Mapped["Stock"] = relationship(back_populates="stock_daily")

    __table_args__ = (
        UniqueConstraint("code", "date", name="uq_code_date"),
        Index("idx_code_date", "code", text("date DESC")),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "adj_close_price": self.adj_close_price,
            "close_price": self.close_price,
            "code": self.code,
            "date": self.date.isoformat() if self.date else None,
            "highest_price": self.highest_price,
            "lowest_price": self.lowest_price,
            "opening_price": self.opening_price,
            "trade_volume": self.trade_volume,
        }

    @staticmethod
    def from_dict(stock_daily_dict: dict) -> "StockDaily":
        date_value = stock_daily_dict.get("date")

        return StockDaily(
            id=stock_daily_dict.get("id"),
            adj_close_price=stock_daily_dict.get("adj_close_price"),
            close_price=stock_daily_dict.get("close_price"),
            code=stock_daily_dict.get("code"),
            date=dt.fromisoformat(date_value) if isinstance(date_value, str) else None,
            highest_price=stock_daily_dict.get("highest_price"),
            lowest_price=stock_daily_dict.get("lowest_price"),
            opening_price=stock_daily_dict.get("opening_price"),
            trade_volume=stock_daily_dict.get("trade_volume"),
        )


class MarketIndexDaily(TimestampMixin, MySQLBase):
    __tablename__ = "market_index_daily"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False)
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "date", name="uq_name_date"),
        Index("idx_name_date_desc", "name", text("date DESC")),
    )


class StockMinutely(TimestampMixin, MySQLBase):
    """비용적 문제로 인해 중단된 코드입니다.
    추후 분당 데이터 수집 시 사용될 엔티티입니다.
    """

    __tablename__ = "stock_minutely"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(255), nullable=False)
    datetime: Mapped[dt] = mapped_column(DateTime, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("code", "datetime", name="uq_code_name_datetime"),
        Index("idx_code", "code"),
        Index("idx_code_datetime_desc", "code", text("datetime DESC")),
    )


class MarketIndexMinutely(TimestampMixin, MySQLBase):
    """비용적 문제로 인해 중단된 코드입니다.
    추후 분당 데이터 수집 시 사용될 엔티티입니다.
    """

    __tablename__ = "market_index_minutely"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    datetime: Mapped[dt] = mapped_column(DateTime, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "datetime", name="uq_name_datetime"),
        Index("idx_name", "name"),
        Index("idx_name_datetime", "name", text("datetime DESC")),
    )
