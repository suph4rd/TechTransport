from alembic import context
from sqlalchemy import create_engine, pool
from app.core.config import get_settings
from app.core.db import Base
from app.auth import models  # Register domain metadata for Alembic.

config = context.config
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=get_settings().database_url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(get_settings().database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
