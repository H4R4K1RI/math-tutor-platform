import os

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:Bohirjon0102@localhost:5432/math_tutor_test"
)
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32-characters-long"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["COOKIE_SECURE"] = "False"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["DEBUG"] = "False"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.db.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402


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