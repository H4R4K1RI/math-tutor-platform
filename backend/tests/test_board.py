import pytest
from httpx import AsyncClient

from app.auth.models import User


# ==================== GET ====================


@pytest.mark.asyncio
async def test_get_board_creates_empty(
    teacher_client: AsyncClient, teacher_lesson
):
    """GET создаёт пустую доску, если её нет."""
    response = await teacher_client.get(f"/api/board/{teacher_lesson.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["lesson_id"] == teacher_lesson.id
    assert data["state"] == {}
    assert data["updated_at"] is not None


@pytest.mark.asyncio
async def test_get_board_returns_same(
    teacher_client: AsyncClient, teacher_lesson
):
    """Повторный GET возвращает ту же доску (не создаёт новую)."""
    r1 = await teacher_client.get(f"/api/board/{teacher_lesson.id}")
    assert r1.status_code == 200

    r2 = await teacher_client.get(f"/api/board/{teacher_lesson.id}")
    assert r2.status_code == 200

    assert r1.json()["lesson_id"] == r2.json()["lesson_id"]


@pytest.mark.asyncio
async def test_get_board_student_ok(
    student_client: AsyncClient, teacher_lesson
):
    """Ученик тоже может читать доску своего урока."""
    response = await student_client.get(f"/api/board/{teacher_lesson.id}")
    assert response.status_code == 200
    assert response.json()["lesson_id"] == teacher_lesson.id


@pytest.mark.asyncio
async def test_get_board_not_found(teacher_client: AsyncClient):
    """Несуществующий lesson_id → 404."""
    response = await teacher_client.get("/api/board/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_board_foreign_teacher(
    teacher_client: AsyncClient,
    db_session,
    student_user: User,
):
    """Учитель не может читать доску чужого урока → 403."""
    from datetime import datetime, timedelta, timezone

    from app.auth.models import User as UserModel
    from app.lessons.models import Lesson
    from app.shared.security import get_password_hash

    # Второй учитель
    teacher2 = UserModel(
        email="teacher2_board@test.com",
        full_name="Teacher 2",
        hashed_password=get_password_hash("password123"),
        role="teacher",
        is_active=True,
        is_verified=True,
    )
    db_session.add(teacher2)
    await db_session.commit()
    await db_session.refresh(teacher2)

    # Его урок
    now = datetime.now(timezone.utc)
    lesson2 = Lesson(
        teacher_id=teacher2.id,
        student_id=student_user.id,
        title="Foreign Lesson",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=1),
        price=0,
        status="scheduled",
    )
    db_session.add(lesson2)
    await db_session.commit()
    await db_session.refresh(lesson2)

    # teacher_client (первый учитель) пытается читать чужой урок
    response = await teacher_client.get(f"/api/board/{lesson2.id}")
    assert response.status_code == 403


# ==================== UPDATE ====================


@pytest.mark.asyncio
async def test_update_board(teacher_client: AsyncClient, teacher_lesson):
    """PUT сохраняет state."""
    payload = {
        "state": {
            "shapes": [
                {"id": "1", "type": "rect", "x": 10, "y": 20},
                {"id": "2", "type": "text", "text": "Hello"},
            ],
            "version": 1,
        }
    }

    response = await teacher_client.put(
        f"/api/board/{teacher_lesson.id}", json=payload
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["lesson_id"] == teacher_lesson.id
    assert data["state"] == payload["state"]

    # Проверяем, что сохранилось
    get_response = await teacher_client.get(f"/api/board/{teacher_lesson.id}")
    assert get_response.status_code == 200
    assert get_response.json()["state"] == payload["state"]


@pytest.mark.asyncio
async def test_update_board_student(
    student_client: AsyncClient, teacher_lesson
):
    """Ученик тоже может обновлять доску своего урока."""
    payload = {"state": {"shapes": [{"id": "1", "type": "circle"}]}}

    response = await student_client.put(
        f"/api/board/{teacher_lesson.id}", json=payload
    )
    assert response.status_code == 200
    assert response.json()["state"] == payload["state"]


@pytest.mark.asyncio
async def test_update_board_foreign_teacher(
    teacher_client: AsyncClient,
    db_session,
    student_user: User,
):
    """Учитель не может писать в чужой урок → 403."""
    from datetime import datetime, timedelta, timezone

    from app.auth.models import User as UserModel
    from app.lessons.models import Lesson
    from app.shared.security import get_password_hash

    teacher2 = UserModel(
        email="teacher3_board@test.com",
        full_name="Teacher 3",
        hashed_password=get_password_hash("password123"),
        role="teacher",
        is_active=True,
        is_verified=True,
    )
    db_session.add(teacher2)
    await db_session.commit()
    await db_session.refresh(teacher2)

    now = datetime.now(timezone.utc)
    lesson2 = Lesson(
        teacher_id=teacher2.id,
        student_id=student_user.id,
        title="Foreign Lesson 2",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=1),
        price=0,
        status="scheduled",
    )
    db_session.add(lesson2)
    await db_session.commit()
    await db_session.refresh(lesson2)

    response = await teacher_client.put(
        f"/api/board/{lesson2.id}",
        json={"state": {"hacked": True}},
    )
    assert response.status_code == 403


# ==================== CLEAR ====================


@pytest.mark.asyncio
async def test_clear_board(teacher_client: AsyncClient, teacher_lesson):
    """DELETE сбрасывает state в {}."""
    # Сначала что-то запишем
    await teacher_client.put(
        f"/api/board/{teacher_lesson.id}",
        json={"state": {"shapes": [{"id": "1"}]}},
    )

    # Проверим, что записано
    r = await teacher_client.get(f"/api/board/{teacher_lesson.id}")
    assert r.json()["state"] == {"shapes": [{"id": "1"}]}

    # Очистим
    response = await teacher_client.delete(f"/api/board/{teacher_lesson.id}")
    assert response.status_code == 200
    assert response.json()["state"] == {}

    # Проверим, что пусто
    r2 = await teacher_client.get(f"/api/board/{teacher_lesson.id}")
    assert r2.json()["state"] == {}