import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импортируем настройки и Base
from app.shared.config import settings
from app.shared.db import Base

# Импортируем ВСЕ модели, чтобы Alembic их видел
from app.auth.models import User  # noqa: F401
from app.assignments.models import Assignment, Submission  # noqa: F401
from app.chat.models import Chat, Message  # noqa: F401
from app.groups.models import Group, GroupStudent  # noqa: F401
from app.invitations.models import Invitation  # noqa: F401
from app.tests.models import (  # noqa: F401
    AnswerOption,
    Question,
    Test,
    UserAnswer,
    UserTest,
)
from app.payments.models import Payment, StudentBalance  # noqa: F401
from app.lessons.models import Lesson, LessonRequest  # noqa: F401
from app.reviews.models import Review  # noqa: F401
from app.materials.models import (  # noqa: F401
    FolderAccess,
    Material,
    MaterialFolder,
)
from app.tutoring_requests.models import TutoringRequest  # noqa: F401
from app.notifications.models import SentReminder  # noqa: F401
from app.board.models import Board  # noqa: F401

# Alembic Config object
config = context.config

# Подставляем URL из settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()