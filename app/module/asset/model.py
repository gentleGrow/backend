from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from app.common.mixin.timestamp import TimestampMixin
from database.config import MySQLBase


class AssetField(TimestampMixin, MySQLBase):
    __tablename__ = "asset_field"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    field_preference = Column(JSON, nullable=False, default=list)


class Dividend(TimestampMixin, MySQLBase):
    __tablename__ = "dividend"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dividend = Column(Float, nullable=False, info={"description": "배당금"})
    stock_code = Column(String(255), ForeignKey("stock.code"), nullable=False)
    date = Column(Date, nullable=False, info={"description": "배당일자"})

    stock = relationship("Stock", back_populates="dividend")
    __table_args__ = (UniqueConstraint("stock_code", "date", name="uq_code_date"),)


class AssetStock(TimestampMixin, MySQLBase):
    __tablename__ = "asset_stock"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_type = Column(String(255), nullable=True, info={"description": "계좌 종류"})
    investment_bank = Column(String(255), nullable=True, info={"description": "증권사"})
    purchase_currency_type = Column(String(255), nullable=True, info={"description": "구매 통화"})
    trade_date = Column(Date, nullable=True, info={"description": "매매일자"})
    trade_price = Column(Float, nullable=True, info={"description": "거래가"})
    quantity = Column(Integer, nullable=True, info={"description": "구매수량"})
    trade = Column(String(255), nullable=True, info={"description": "매매, 매수/매도"}, default="BUY")

    stock_id = Column(BigInteger, ForeignKey("stock.id"), primary_key=True)
    asset_id = Column(BigInteger, ForeignKey("asset.id", ondelete="CASCADE"), primary_key=True)
    asset = relationship("Asset", back_populates="asset_stock", uselist=False, overlaps="stock,asset", lazy="selectin")
    stock = relationship("Stock", back_populates="asset_stock", overlaps="asset,stock", lazy="selectin")


class Asset(TimestampMixin, MySQLBase):
    __tablename__ = "asset"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(255), nullable=False, info={"description": "자산 종류"})

    user_id = Column(BigInteger, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    stock = relationship(
        "Stock", secondary="asset_stock", back_populates="asset", overlaps="asset_stock", lazy="selectin"
    )
    asset_stock = relationship("AssetStock", back_populates="asset", uselist=False, overlaps="stock", lazy="selectin")

    __table_args__ = (Index("idx_user_id_asset_type_deleted_at", "user_id", "asset_type", "deleted_at"),)


class Stock(TimestampMixin, MySQLBase):
    __tablename__ = "stock"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(255), nullable=False, unique=True)
    country = Column(String(255), nullable=False)
    market_index = Column(String(255), nullable=False)
    name_kr = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=False)

    asset = relationship(
        "Asset", secondary="asset_stock", back_populates="stock", overlaps="asset_stock", lazy="selectin"
    )
    asset_stock = relationship("AssetStock", back_populates="stock", overlaps="asset", lazy="selectin")
    dividend = relationship("Dividend", back_populates="stock")


class StockDaily(MySQLBase):
    __tablename__ = "stock_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    adj_close_price = Column(Float, nullable=False, info={"description": "Adjusted closing price of the stock"})
    close_price = Column(Float, nullable=False, info={"description": "Closing price of the stock"})
    code = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, info={"description": "stock closing day"})
    highest_price = Column(Float, nullable=False, info={"description": "Highest price of the stock"})
    lowest_price = Column(Float, nullable=False, info={"description": "Lowest price of the stock"})
    opening_price = Column(Float, nullable=False, info={"description": "Opening price of the stock"})
    trade_volume = Column(BigInteger, nullable=False, info={"description": "Volume of stock traded"})

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
            date=datetime.fromisoformat(date_value) if isinstance(date_value, str) else None,
            highest_price=stock_daily_dict.get("highest_price"),
            lowest_price=stock_daily_dict.get("lowest_price"),
            opening_price=stock_daily_dict.get("opening_price"),
            trade_volume=stock_daily_dict.get("trade_volume"),
        )


class MarketIndexDaily(MySQLBase):
    __tablename__ = "market_index_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "date", name="uq_name_date"),
        Index("idx_name_date_desc", "name", text("date DESC")),
    )


class StockMinutely(MySQLBase):
    """비용적 문제로 인해 중단된 코드입니다.
    추후 분당 데이터 수집 시 사용될 엔티티입니다.
    """

    __tablename__ = "stock_minutely"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(255), nullable=False)
    datetime = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("code", "datetime", name="uq_code_name_datetime"),
        Index("idx_code", "code"),
        Index("idx_code_datetime_desc", "code", text("datetime DESC")),
    )


class MarketIndexMinutely(MySQLBase):
    """비용적 문제로 인해 중단된 코드입니다.
    추후 분당 데이터 수집 시 사용될 엔티티입니다.
    """

    __tablename__ = "market_index_minutely"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    datetime = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "datetime", name="uq_name_datetime"),
        Index("idx_name", "name"),
        Index("idx_name_datetime", "name", text("datetime DESC")),
    )
