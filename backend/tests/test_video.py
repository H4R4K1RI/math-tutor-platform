import pytest
from httpx import AsyncClient

from app.auth.models import User


@pytest.mark.asyncio
async def test_get_video_token_teacher(
    teacher_client: AsyncClient, teacher_lesson
):
    """Учитель получает JWT — moderator=True."""
    response = await teacher_client.post(
        f"/api/video/token/{teacher_lesson.id}"
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert "token" in data
    assert data["domain"] == "meet.tutor-platform.localhost"
    assert data["room"] == f"lesson-{teacher_lesson.id}"

    # Расшифруем JWT
    from jose import jwt

    from app.shared.config import settings

    payload = jwt.decode(
        data["token"],
        settings.JITSI_JWT_APP_SECRET,
        algorithms=["HS256"],
        audience="jitsi",
    )

    assert payload["room"] == f"lesson-{teacher_lesson.id}"
    assert payload["context"]["user"]["id"] == str(teacher_lesson.teacher_id)
    assert payload["context"]["user"]["moderator"] is True


@pytest.mark.asyncio
async def test_get_video_token_student(
    student_client: AsyncClient, teacher_lesson
):
    """Ученик получает JWT — moderator=False."""
    response = await student_client.post(
        f"/api/video/token/{teacher_lesson.id}"
    )
    assert response.status_code == 200
    data = response.json()

    from jose import jwt

    from app.shared.config import settings

    payload = jwt.decode(
        data["token"],
        settings.JITSI_JWT_APP_SECRET,
        algorithms=["HS256"],
        audience="jitsi",
    )

    assert payload["context"]["user"]["moderator"] is False


@pytest.mark.asyncio
async def test_get_video_token_not_found(teacher_client: AsyncClient):
    """Несуществующий урок → 404."""
    response = await teacher_client.post("/api/video/token/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_video_token_foreign_teacher(
    teacher_client: AsyncClient,
    db_session,
    student_user: User,
):
    """Чужой урок → 403."""
    from datetime import datetime, timedelta, timezone

    from app.auth.models import User as UserModel
    from app.lessons.models import Lesson
    from app.shared.security import get_password_hash

    teacher2 = UserModel(
        email="teacher_video@test.com",
        full_name="Teacher Video",
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
        title="Foreign Video Lesson",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=1),
        price=0,
        status="scheduled",
    )
    db_session.add(lesson2)
    await db_session.commit()
    await db_session.refresh(lesson2)

    response = await teacher_client.post(
        f"/api/video/token/{lesson2.id}"
    )
    assert response.status_code == 403