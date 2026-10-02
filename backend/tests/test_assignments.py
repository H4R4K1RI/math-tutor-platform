from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.auth.models import User


def _future_iso(days: int = 7) -> str:
    """ISO-дата в будущем."""
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


# ==================== CREATE ====================


@pytest.mark.asyncio
async def test_create_assignment_single(
    teacher_client, teacher_user, student_user, teacher_student_pair
):
    """Учитель создаёт одиночное задание."""
    response = await teacher_client.post(
        "/api/assignments",
        json={
            "title": "Test Assignment",
            "description": "Do this",
            "due_date": _future_iso(),
            "student_id": student_user.id,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["count"] == 1
    assert len(data["assignments"]) == 1
    assert data["assignments"][0]["title"] == "Test Assignment"
    assert data["assignments"][0]["teacher_id"] == teacher_user.id
    assert data["assignments"][0]["student_id"] == student_user.id


@pytest.mark.asyncio
async def test_create_assignment_short_title(teacher_client):
    """Title < 3 символов → 422."""
    response = await teacher_client.post(
        "/api/assignments",
        json={
            "title": "ab",
            "description": "Do this",
            "due_date": _future_iso(),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_assignment_student_forbidden(
    student_client, student_user, teacher_student_pair
):
    """Ученик не может создавать задания → 403."""
    response = await student_client.post(
        "/api/assignments",
        json={
            "title": "Student Assignment",
            "description": "Do this",
            "due_date": _future_iso(),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_assignment_for_group(
    teacher_client, teacher_user, student_user, db_session
):
    """Групповое задание — создаётся N заданий."""
    from app.groups.models import Group, GroupStudent

    # 1. Создаём второго ученика
    from app.shared.security import get_password_hash

    student2 = User(
        email="student2@test.com",
        full_name="Student Two",
        hashed_password=get_password_hash("password123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(student2)
    await db_session.commit()
    await db_session.refresh(student2)

    # 2. Группа с двумя учениками
    group = Group(teacher_id=teacher_user.id, name="Test Group")
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    db_session.add(GroupStudent(group_id=group.id, student_id=student_user.id))
    db_session.add(GroupStudent(group_id=group.id, student_id=student2.id))
    await db_session.commit()

    # 3. Создаём групповое задание
    response = await teacher_client.post(
        "/api/assignments",
        json={
            "title": "Group Assignment",
            "description": "Do this",
            "due_date": _future_iso(),
            "group_id": group.id,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["count"] == 2
    assert len(data["assignments"]) == 2


# ==================== GET LIST ====================


@pytest.mark.asyncio
async def test_get_assignments_teacher_sees_own(
    teacher_client, teacher_user, student_user, teacher_student_pair
):
    """Учитель видит только свои задания."""
    # Создаём 2 задания
    for i in range(2):
        await teacher_client.post(
            "/api/assignments",
            json={
                "title": f"Assignment {i}",
                "description": "Do this",
                "due_date": _future_iso(),
                "student_id": student_user.id,
            },
        )

    response = await teacher_client.get("/api/assignments")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_assignments_student_sees_own_and_common(
    teacher_client,
    student_client,
    teacher_user,
    student_user,
    teacher_student_pair,
):
    """Ученик видит свои + общие от своих учителей."""
    # 1. Личное задание
    await teacher_client.post(
        "/api/assignments",
        json={
            "title": "Personal",
            "description": "For you",
            "due_date": _future_iso(),
            "student_id": student_user.id,
        },
    )

    # 2. Общее задание (для всех)
    await teacher_client.post(
        "/api/assignments",
        json={
            "title": "Common",
            "description": "For all",
            "due_date": _future_iso(),
        },
    )

    # 3. Ученик видит оба
    response = await student_client.get("/api/assignments")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    titles = {a["title"] for a in data["items"]}
    assert titles == {"Personal", "Common"}


# ==================== GET DETAIL ====================


@pytest.mark.asyncio
async def test_get_assignment_detail(
    teacher_client, student_user, teacher_student_pair
):
    """GET /assignments/{id} — детали."""
    create_response = await teacher_client.post(
        "/api/assignments",
        json={
            "title": "Detail Test",
            "description": "Do this",
            "due_date": _future_iso(),
            "student_id": student_user.id,
        },
    )
    assignment_id = create_response.json()["assignments"][0]["id"]

    response = await teacher_client.get(f"/api/assignments/{assignment_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Detail Test"


@pytest.mark.asyncio
async def test_get_assignment_not_found(teacher_client):
    """GET /assignments/9999 → 404."""
    response = await teacher_client.get("/api/assignments/9999")
    assert response.status_code == 404


# ==================== UPDATE ====================


@pytest.mark.asyncio
async def test_update_assignment(
    teacher_client, student_user, teacher_student_pair
):
    """PUT /assignments/{id} — обновление."""
    create_response = await teacher_client.post(
        "/api/assignments",
        json={
            "title": "Old Title",
            "description": "Do this",
            "due_date": _future_iso(),
            "student_id": student_user.id,
        },
    )
    assignment_id = create_response.json()["assignments"][0]["id"]

    response = await teacher_client.put(
        f"/api/assignments/{assignment_id}",
        json={"title": "New Title"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_update_assignment_short_title(
    teacher_client, student_user, teacher_student_pair
):
    """PUT с title < 3 → 422."""
    create_response = await teacher_client.post(
        "/api/assignments",
        json={
            "title": "Valid",
            "description": "Do this",
            "due_date": _future_iso(),
            "student_id": student_user.id,
        },
    )
    assignment_id = create_response.json()["assignments"][0]["id"]

    response = await teacher_client.put(
        f"/api/assignments/{assignment_id}",
        json={"title": "ab"},
    )
    assert response.status_code == 422


# ==================== DELETE ====================


@pytest.mark.asyncio
async def test_delete_assignment(
    teacher_client, student_user, teacher_student_pair
):
    """DELETE /assignments/{id}."""
    create_response = await teacher_client.post(
        "/api/assignments",
        json={
            "title": "To Delete",
            "description": "Do this",
            "due_date": _future_iso(),
            "student_id": student_user.id,
        },
    )
    assignment_id = create_response.json()["assignments"][0]["id"]

    response = await teacher_client.delete(f"/api/assignments/{assignment_id}")
    assert response.status_code == 200

    # Проверяем, что удалено
    get_response = await teacher_client.get(f"/api/assignments/{assignment_id}")
    assert get_response.status_code == 404