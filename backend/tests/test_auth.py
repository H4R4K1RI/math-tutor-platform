import pytest
from httpx import AsyncClient


# ==================== REGISTER ====================


@pytest.mark.asyncio
async def test_register_teacher(client: AsyncClient):
    """Регистрация учителя — без инвайта."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "new_teacher@test.com",
            "full_name": "New Teacher",
            "password": "password123",
            "role": "teacher",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "new_teacher@test.com"
    assert data["role"] == "teacher"
    assert data["full_name"] == "New Teacher"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, teacher_user):
    """Регистрация с существующим email → 400."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "teacher@test.com",
            "full_name": "Duplicate",
            "password": "password123",
            "role": "teacher",
        },
    )
    assert response.status_code == 400
    assert "уже зарегистрирован" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_student_without_invite(client: AsyncClient):
    """Регистрация ученика без инвайта → 400."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "new_student@test.com",
            "full_name": "New Student",
            "password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 400
    assert "приглашени" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_student_with_invite(
    client: AsyncClient, teacher_client
):
    """Регистрация ученика по инвайту от учителя."""
    # 1. Учитель генерирует инвайт
    inv_response = await teacher_client.post("/api/invitations/generate")
    assert inv_response.status_code == 200
    invite_code = inv_response.json()["code"]

    # 2. Новый клиент регистрируется по инвайту
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "invited_student@test.com",
            "full_name": "Invited Student",
            "password": "password123",
            "role": "student",
            "invite_code": invite_code,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "invited_student@test.com"
    assert data["role"] == "student"


# ==================== LOGIN ====================


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, teacher_user):
    """Успешный логин."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "teacher@test.com", "password": "teacher123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, teacher_user):
    """Неверный пароль → 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "teacher@test.com", "password": "wrong_password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Несуществующий email → 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@test.com", "password": "password123"},
    )
    assert response.status_code == 401


# ==================== /ME ====================


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient):
    """GET /me без токена → 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authorized(teacher_client, teacher_user):
    """GET /me с токеном → данные пользователя."""
    response = await teacher_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "teacher@test.com"
    assert data["role"] == "teacher"
    assert data["id"] == teacher_user.id


# ==================== LOGOUT ====================


@pytest.mark.asyncio
async def test_logout(teacher_client):
    """Logout — куки удаляются."""
    response = await teacher_client.post("/api/auth/logout")
    assert response.status_code == 200

    # После logout — /me возвращает 401
    me_response = await teacher_client.get("/api/auth/me")
    assert me_response.status_code == 401


# ==================== REFRESH ====================


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, teacher_user):
    """Refresh access token через refresh_token."""
    # 1. Логинимся
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "teacher@test.com", "password": "teacher123"},
    )
    assert login_response.status_code == 200

    # 2. Refresh
    refresh_response = await client.post("/api/auth/refresh")
    assert refresh_response.status_code == 200


@pytest.mark.asyncio
async def test_refresh_without_token(client: AsyncClient):
    """Refresh без refresh_token → 401."""
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401