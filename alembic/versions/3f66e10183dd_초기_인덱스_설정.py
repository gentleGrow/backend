"""초기 인덱스 설정

Revision ID: 3f66e10183dd
Revises: 
Create Date: 2024-11-25 19:31:52.549532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f66e10183dd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'dividend', 'stock', ['stock_code'], ['code'])
    # op.create_index('idx_name_date_desc', 'market_index_daily', ['name', sa.text('date DESC')], unique=False)
    op.drop_index('idx_name_datetime', table_name='market_index_minutely')
    op.create_index('idx_name_datetime', 'market_index_minutely', ['name', sa.text('datetime DESC')], unique=False)
    op.drop_index('idx_code_date', table_name='stock_daily')
    op.create_index('idx_code_date', 'stock_daily', ['code', sa.text('date DESC')], unique=False)
    # op.create_index('idx_code', 'stock_minutely', ['code'], unique=False)
    op.create_index('idx_code_datetime_desc', 'stock_minutely', ['code', sa.text('datetime DESC')], unique=False)
    op.create_unique_constraint('uq_code_name_datetime', 'stock_minutely', ['code', 'datetime'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('uq_code_name_datetime', 'stock_minutely', type_='unique')
    op.drop_index('idx_code_datetime_desc', table_name='stock_minutely')
    op.drop_index('idx_code', table_name='stock_minutely')
    op.drop_index('idx_code_date', table_name='stock_daily')
    op.create_index('idx_code_date', 'stock_daily', ['code', 'date'], unique=False)
    op.drop_index('idx_name_datetime', table_name='market_index_minutely')
    op.create_index('idx_name_datetime', 'market_index_minutely', ['name', 'datetime'], unique=False)
    op.drop_index('idx_name_date_desc', table_name='market_index_daily')
    op.drop_constraint(None, 'dividend', type_='foreignkey')
    op.drop_table('invest_tip')
    # ### end Alembic commands ###
