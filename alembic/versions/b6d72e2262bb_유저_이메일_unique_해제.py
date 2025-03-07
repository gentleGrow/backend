"""유저 이메일 unique 해제

Revision ID: b6d72e2262bb
Revises: 38f2da5832c4
Create Date: 2025-02-07 18:49:38.411726

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6d72e2262bb"
down_revision: Union[str, None] = "38f2da5832c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_name_date_desc", table_name="market_index_daily")
    op.create_index("idx_name_date_desc", "market_index_daily", ["name", sa.text("date DESC")], unique=False)
    op.drop_index("idx_name_datetime", table_name="market_index_minutely")
    op.create_index("idx_name_datetime", "market_index_minutely", ["name", sa.text("datetime DESC")], unique=False)
    op.drop_index("idx_code_date", table_name="stock_daily")
    op.create_index("idx_code_date", "stock_daily", ["code", sa.text("date DESC")], unique=False)
    op.drop_index("idx_code_datetime_desc", table_name="stock_minutely")
    op.create_index("idx_code_datetime_desc", "stock_minutely", ["code", sa.text("datetime DESC")], unique=False)
    op.drop_index("email", table_name="user")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index("email", "user", ["email"], unique=True)
    op.drop_index("idx_code_datetime_desc", table_name="stock_minutely")
    op.create_index("idx_code_datetime_desc", "stock_minutely", ["code", "datetime"], unique=False)
    op.drop_index("idx_code_date", table_name="stock_daily")
    op.create_index("idx_code_date", "stock_daily", ["code", "date"], unique=False)
    op.drop_index("idx_name_datetime", table_name="market_index_minutely")
    op.create_index("idx_name_datetime", "market_index_minutely", ["name", "datetime"], unique=False)
    op.drop_index("idx_name_date_desc", table_name="market_index_daily")
    op.create_index("idx_name_date_desc", "market_index_daily", ["name", "date"], unique=False)
    # ### end Alembic commands ###
