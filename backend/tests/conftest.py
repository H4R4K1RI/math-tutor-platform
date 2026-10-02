import os
from pathlib import Path

# 1. TESTING флаг — всегда
os.environ["TESTING"] = "1"

# 2. Локально (если есть .env.test) — ставим дефолты с setdefault.
#    В CI (.env.test нет) — оставляем DATABASE_URL из workflow.
_env_test = Path(__file__).parent.parent / ".env.test"
if _env_test.exists():
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:Bohirjon0102@localhost:5432/math_tutor_test"
    )
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32-characters-long")
    os.environ.setdefault("ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    os.environ.setdefault("COOKIE_SECURE", "False")
    os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
    os.environ.setdefault("DEBUG", "False")

# 3. Остальные импорты
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.shared.config import settings
from app.shared.db import Base, get_db
from app.main import app
from app.models.user import User
from app.shared.security import get_password_hash

# ==================== ENGINE / SESSION ====================


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncSession:
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session


# ==================== HTTP-КЛИЕНТ (АНОНИМНЫЙ) ====================


def _make_override(test_engine):
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    return override_get_db


@pytest_asyncio.fixture(scope="function")
async def client(test_engine) -> AsyncClient:
    """Анонимный клиент."""
    app.dependency_overrides[get_db] = _make_override(test_engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ==================== ФАБРИКИ ПОЛЬЗОВАТЕЛЕЙ ====================


@pytest_asyncio.fixture
async def teacher_user(db_session: AsyncSession) -> User:
    user = User(
        email="teacher@test.com",
        full_name="Test Teacher",
        hashed_password=get_password_hash("teacher123"),
        role="teacher",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession) -> User:
    user = User(
        email="student@test.com",
        full_name="Test Student",
        hashed_password=get_password_hash("student123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ==================== АВТОРИЗОВАННЫЕ КЛИЕНТЫ ====================


@pytest_asyncio.fixture
async def teacher_client(test_engine, teacher_user: User) -> AsyncClient:
    """Клиент, авторизованный как учитель."""
    app.dependency_overrides[get_db] = _make_override(test_engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"email": "teacher@test.com", "password": "teacher123"},
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        yield ac


@pytest_asyncio.fixture
async def student_client(test_engine, student_user: User) -> AsyncClient:
    """Клиент, авторизованный как ученик."""
    app.dependency_overrides[get_db] = _make_override(test_engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"email": "student@test.com", "password": "student123"},
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        yield ac


# ==================== ПАРА УЧИТЕЛЬ-УЧЕНИК ====================


@pytest_asyncio.fixture
async def teacher_student_pair(
    db_session: AsyncSession, teacher_user: User, student_user: User
):
    from app.models.chat import Chat

    chat = Chat(
        teacher_id=teacher_user.id,
        student_id=student_user.id,
        assignment_id=None,
    )
    db_session.add(chat)
    await db_session.commit()
    await db_session.refresh(chat)

    return {"teacher": teacher_user, "student": student_user, "chat": chat}