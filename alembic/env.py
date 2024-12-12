from logging.config import fileConfig
from os import getenv

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context
from app.module.asset.model import MySQLBase
from app.module.auth.model import User  # noqa > relationship purpose
from app.module.chart.model import InvestTip  # noqa > create table

load_dotenv()

ALEMBIC_MYSQL_URL = getenv("ALEMBIC_MYSQL_URL")


config = context.config


config.set_main_option("sqlalchemy.url", ALEMBIC_MYSQL_URL)
fileConfig(config.config_file_name)
target_metadata = MySQLBase.metadata


def run_migrations():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


run_migrations()
