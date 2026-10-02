import pytest
from httpx import AsyncClient


# ==================== CREATE ====================


@pytest.mark.asyncio
async def test_create_chat_teacher(
    teacher_client, student_user, teacher_student_pair
):
    """Учитель создаёт чат — уже есть (из pair) → возвращает id."""
    response = await teacher_client.post(
        "/api/chats",
        json={"student_id": student_user.id, "assignment_id": None},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "chat_id" in data


@pytest.mark.asyncio
async def test_create_chat_student_forbidden(
    student_client, teacher_user, teacher_student_pair
):
    """Ученик не может создавать чаты → 403."""
    response = await student_client.post(
        "/api/chats",
        json={"student_id": teacher_user.id, "assignment_id": None},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_chat_foreign_student(
    teacher_client, db_session
):
    """Учитель не может создать чат с чужим учеником → 403."""
    from app.shared.security import get_password_hash
    from app.models.user import User

    foreign = User(
        email="foreign@test.com",
        full_name="Foreign Student",
        hashed_password=get_password_hash("password123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(foreign)
    await db_session.commit()
    await db_session.refresh(foreign)

    response = await teacher_client.post(
        "/api/chats",
        json={"student_id": foreign.id, "assignment_id": None},
    )
    assert response.status_code == 403


# ==================== LIST ====================


@pytest.mark.asyncio
async def test_get_chats_teacher(
    teacher_client, teacher_student_pair
):
    """Учитель видит свои чаты."""
    response = await teacher_client.get("/api/chats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_chats_student(
    student_client, teacher_student_pair
):
    """Ученик видит свои чаты."""
    response = await student_client.get("/api/chats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


# ==================== GET DETAIL ====================


@pytest.mark.asyncio
async def test_get_chat_detail_teacher(
    teacher_client, teacher_student_pair
):
    """Учитель получает детали чата."""
    chat_id = teacher_student_pair["chat"].id
    response = await teacher_client.get(f"/api/chats/{chat_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == chat_id


@pytest.mark.asyncio
async def test_get_chat_foreign(
    teacher_client, db_session, teacher_user
):
    """Учитель не видит чужой чат → 403."""
    from app.shared.security import get_password_hash
    from app.models.chat import Chat
    from app.models.user import User

    # Второй учитель и ученик
    teacher2 = User(
        email="teacher2@test.com",
        full_name="Teacher 2",
        hashed_password=get_password_hash("password123"),
        role="teacher",
        is_active=True,
        is_verified=True,
    )
    student2 = User(
        email="student2@test.com",
        full_name="Student 2",
        hashed_password=get_password_hash("password123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(teacher2)
    db_session.add(student2)
    await db_session.commit()
    await db_session.refresh(teacher2)
    await db_session.refresh(student2)

    foreign_chat = Chat(
        teacher_id=teacher2.id, student_id=student2.id, assignment_id=None
    )
    db_session.add(foreign_chat)
    await db_session.commit()
    await db_session.refresh(foreign_chat)

    response = await teacher_client.get(f"/api/chats/{foreign_chat.id}")
    assert response.status_code == 403


# ==================== MESSAGES ====================


@pytest.mark.asyncio
async def test_get_messages_empty(
    teacher_client, teacher_student_pair
):
    """GET /chats/{id}/messages — пустой список."""
    chat_id = teacher_student_pair["chat"].id
    response = await teacher_client.get(f"/api/chats/{chat_id}/messages")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_messages_foreign(
    student_client, db_session
):
    """Ученик не видит чужой чат → 403."""
    from app.shared.security import get_password_hash
    from app.models.chat import Chat
    from app.models.user import User

    teacher2 = User(
        email="teacher2@test.com",
        full_name="Teacher 2",
        hashed_password=get_password_hash("password123"),
        role="teacher",
        is_active=True,
        is_verified=True,
    )
    student2 = User(
        email="student2@test.com",
        full_name="Student 2",
        hashed_password=get_password_hash("password123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(teacher2)
    db_session.add(student2)
    await db_session.commit()
    await db_session.refresh(teacher2)
    await db_session.refresh(student2)

    foreign_chat = Chat(
        teacher_id=teacher2.id, student_id=student2.id, assignment_id=None
    )
    db_session.add(foreign_chat)
    await db_session.commit()
    await db_session.refresh(foreign_chat)

    response = await student_client.get(
        f"/api/chats/{foreign_chat.id}/messages"
    )
    assert response.status_code == 403


# ==================== DELETE ====================


@pytest.mark.asyncio
async def test_delete_chat_teacher(
    teacher_client, teacher_student_pair
):
    """Учитель удаляет свой чат."""
    chat_id = teacher_student_pair["chat"].id
    response = await teacher_client.delete(f"/api/chats/{chat_id}")
    assert response.status_code == 200

    # Проверяем, что удалён
    get_response = await teacher_client.get(f"/api/chats/{chat_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_chat_foreign(
    teacher_client, db_session
):
    """Учитель не может удалить чужой чат → 403."""
    from app.shared.security import get_password_hash
    from app.models.chat import Chat
    from app.models.user import User

    teacher2 = User(
        email="teacher2@test.com",
        full_name="Teacher 2",
        hashed_password=get_password_hash("password123"),
        role="teacher",
        is_active=True,
        is_verified=True,
    )
    student2 = User(
        email="student2@test.com",
        full_name="Student 2",
        hashed_password=get_password_hash("password123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(teacher2)
    db_session.add(student2)
    await db_session.commit()
    await db_session.refresh(teacher2)
    await db_session.refresh(student2)

    foreign_chat = Chat(
        teacher_id=teacher2.id, student_id=student2.id, assignment_id=None
    )
    db_session.add(foreign_chat)
    await db_session.commit()
    await db_session.refresh(foreign_chat)

    response = await teacher_client.delete(f"/api/chats/{foreign_chat.id}")
    assert response.status_code == 403