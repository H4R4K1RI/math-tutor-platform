import pytest
from httpx import AsyncClient


# ==================== GENERATE ====================


@pytest.mark.asyncio
async def test_generate_invitation_teacher(teacher_client):
    """Учитель генерирует инвайт."""
    response = await teacher_client.post("/api/invitations/generate")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "code" in data
    assert "url" in data
    assert "/register?invite=" in data["url"]


@pytest.mark.asyncio
async def test_generate_invitation_student_forbidden(student_client):
    """Ученик не может генерировать инвайт → 403."""
    response = await student_client.post("/api/invitations/generate")
    assert response.status_code == 403


# ==================== VALIDATE ====================


@pytest.mark.asyncio
async def test_validate_invitation(client: AsyncClient, teacher_client):
    """Валидный инвайт → 200."""
    gen_response = await teacher_client.post("/api/invitations/generate")
    code = gen_response.json()["code"]

    response = await client.post(f"/api/invitations/validate/{code}")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "teacher_id" in data


@pytest.mark.asyncio
async def test_validate_invitation_invalid(client: AsyncClient):
    """Невалидный код → 404."""
    response = await client.post("/api/invitations/validate/invalid_code_123")
    assert response.status_code == 404


# ==================== ACCEPT ====================


@pytest.mark.asyncio
async def test_accept_invitation(
    client: AsyncClient, teacher_client, db_session
):
    """Ученик принимает инвайт → создаётся чат."""
    from app.shared.security import get_password_hash
    from app.auth.models import User

    # 1. Учитель генерирует инвайт
    gen_response = await teacher_client.post("/api/invitations/generate")
    code = gen_response.json()["code"]

    # 2. Создаём ученика
    student = User(
        email="new_student@test.com",
        full_name="New Student",
        hashed_password=get_password_hash("password123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    # 3. Логин ученика
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "new_student@test.com", "password": "password123"},
    )
    assert login_response.status_code == 200

    # 4. Accept
    accept_response = await client.post(f"/api/invitations/accept/{code}")
    assert accept_response.status_code == 200, accept_response.text
    assert "success" in accept_response.json()["message"].lower()


@pytest.mark.asyncio
async def test_accept_invitation_twice(
    client: AsyncClient, teacher_client, db_session
):
    """Повторное принятие инвайта → 400."""
    from app.shared.security import get_password_hash
    from app.auth.models import User

    gen_response = await teacher_client.post("/api/invitations/generate")
    code = gen_response.json()["code"]

    student = User(
        email="new_student2@test.com",
        full_name="New Student 2",
        hashed_password=get_password_hash("password123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    await client.post(
        "/api/auth/login",
        json={"email": "new_student2@test.com", "password": "password123"},
    )

    # Первый accept — успех
    first = await client.post(f"/api/invitations/accept/{code}")
    assert first.status_code == 200

    # Второй accept — 400
    second = await client.post(f"/api/invitations/accept/{code}")
    assert second.status_code == 400