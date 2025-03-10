"""stock 테이블 country 인덱스 추가

Revision ID: 276d2b3da188
Revises: 0b4bb6eab923
Create Date: 2025-01-26 19:59:23.789136

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "276d2b3da188"
down_revision: Union[str, None] = "0b4bb6eab923"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_name_date_desc", table_name="market_index_daily")
    op.create_index("idx_name_date_desc", "market_index_daily", ["name", sa.text("date DESC")], unique=False)
    op.drop_index("idx_name_datetime", table_name="market_index_minutely")
    op.create_index("idx_name_datetime", "market_index_minutely", ["name", sa.text("datetime DESC")], unique=False)
    op.create_index("idx_country", "stock", ["country"], unique=False)
    op.drop_index("idx_code_date", table_name="stock_daily")
    op.create_index("idx_code_date", "stock_daily", ["code", sa.text("date DESC")], unique=False)
    op.drop_index("idx_code_datetime_desc", table_name="stock_minutely")
    op.create_index("idx_code_datetime_desc", "stock_minutely", ["code", sa.text("datetime DESC")], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_code_datetime_desc", table_name="stock_minutely")
    op.create_index("idx_code_datetime_desc", "stock_minutely", ["code", "datetime"], unique=False)
    op.drop_index("idx_code_date", table_name="stock_daily")
    op.create_index("idx_code_date", "stock_daily", ["code", "date"], unique=False)
    op.drop_index("idx_country", table_name="stock")
    op.drop_index("idx_name_datetime", table_name="market_index_minutely")
    op.create_index("idx_name_datetime", "market_index_minutely", ["name", "datetime"], unique=False)
    op.drop_index("idx_name_date_desc", table_name="market_index_daily")
    op.create_index("idx_name_date_desc", "market_index_daily", ["name", "date"], unique=False)
    # ### end Alembic commands ###
