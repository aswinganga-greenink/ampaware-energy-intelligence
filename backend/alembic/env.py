# alembic/env.py
# ==============
# Alembic migration environment.
#
# Key design decisions:
# - Runs in ASYNC mode using asyncpg to stay consistent with the app's
#   async-first database access pattern.
# - Imports ALL ORM models via app.db.models_registry so that autogenerate
#   can detect schema changes correctly.
# - Uses the SYNC url (psycopg2) for the run_migrations_offline path
#   (offline SQL script generation doesn't need an actual connection).
# - table_args include explicit schema="public" in models, so alembic
#   operates cleanly in multi-schema databases.

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Load app config & models
from app.core.config import get_settings
from app.db.base import Base

# IMPORTANT: Import the model registry so Alembic autogenerate detects ALL tables.
# app.domain.models.__init__ imports every ORM model class.
import app.domain.models  # noqa: F401  # registers all models with Base.metadata

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData object for autogenerate
target_metadata = Base.metadata

# Override sqlalchemy.url from app settings (ignores alembic.ini value)
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database.sync_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL script without connecting to the database.
    Useful for reviewing migrations before applying them.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode using an async engine.

    The sync_url (psycopg2) is used here because Alembic's migration
    runner is not async-native; we wrap it using run_sync.
    """
    connectable = create_async_engine(
        settings.database.async_url,
        poolclass=pool.NullPool,  # no pooling needed for one-shot migrations
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
