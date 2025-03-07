"""stock 테이블 code 인덱스 추가

Revision ID: fa19dc8d0886
Revises: 276d2b3da188
Create Date: 2025-01-27 19:15:46.142717

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fa19dc8d0886"
down_revision: Union[str, None] = "276d2b3da188"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_name_date_desc", table_name="market_index_daily")
    op.create_index("idx_name_date_desc", "market_index_daily", ["name", sa.text("date DESC")], unique=False)
    op.drop_index("idx_name_datetime", table_name="market_index_minutely")
    op.create_index("idx_name_datetime", "market_index_minutely", ["name", sa.text("datetime DESC")], unique=False)
    op.create_index("idx_code", "stock", ["code"], unique=False)
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
    op.drop_index("idx_code", table_name="stock")
    op.drop_index("idx_name_datetime", table_name="market_index_minutely")
    op.create_index("idx_name_datetime", "market_index_minutely", ["name", "datetime"], unique=False)
    op.drop_index("idx_name_date_desc", table_name="market_index_daily")
    op.create_index("idx_name_date_desc", "market_index_daily", ["name", "date"], unique=False)
    # ### end Alembic commands ###
