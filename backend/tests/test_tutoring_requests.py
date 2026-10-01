import pytest
from httpx import AsyncClient


# ==================== CREATE ====================


@pytest.mark.asyncio
async def test_create_tutoring_request(
    student_client, teacher_user
):
    """Ученик отправляет заявку на обучение."""
    response = await student_client.post(
        "/api/tutoring-requests",
        json={"teacher_id": teacher_user.id, "message": "Хочу учиться!"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["teacher_id"] == teacher_user.id
    assert data["status"] == "pending"
    assert data["message"] == "Хочу учиться!"


@pytest.mark.asyncio
async def test_create_tutoring_request_teacher_forbidden(
    teacher_client, student_user
):
    """Учитель не может отправлять заявки → 403."""
    response = await teacher_client.post(
        "/api/tutoring-requests",
        json={"teacher_id": student_user.id, "message": "Test"},
    )
    assert response.status_code == 403


# ==================== LIST ====================


@pytest.mark.asyncio
async def test_get_tutoring_requests_teacher(
    teacher_client, student_client, teacher_user
):
    """Учитель видит входящие заявки."""
    await student_client.post(
        "/api/tutoring-requests",
        json={"teacher_id": teacher_user.id, "message": "Test"},
    )

    response = await teacher_client.get("/api/tutoring-requests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"


# ==================== UPDATE (APPROVE) ====================


@pytest.mark.asyncio
async def test_approve_tutoring_request(
    teacher_client, student_client, teacher_user, student_user
):
    """Approve заявки → создаётся чат."""
    # 1. Заявка
    create_response = await student_client.post(
        "/api/tutoring-requests",
        json={"teacher_id": teacher_user.id, "message": "Test"},
    )
    request_id = create_response.json()["id"]

    # 2. Approve
    approve_response = await teacher_client.put(
        f"/api/tutoring-requests/{request_id}",
        json={"status": "approved"},
    )
    assert approve_response.status_code == 200, approve_response.text

    # 3. Проверяем, что чат создан
    chats_response = await teacher_client.get("/api/chats")
    assert chats_response.status_code == 200
    chats = chats_response.json()["items"]
    chat_with_student = [
        c for c in chats if c["other_user_id"] == student_user.id
    ]
    assert len(chat_with_student) == 1


@pytest.mark.asyncio
async def test_reject_tutoring_request(
    teacher_client, student_client, teacher_user
):
    """Reject заявки."""
    create_response = await student_client.post(
        "/api/tutoring-requests",
        json={"teacher_id": teacher_user.id, "message": "Test"},
    )
    request_id = create_response.json()["id"]

    reject_response = await teacher_client.put(
        f"/api/tutoring-requests/{request_id}",
        json={"status": "rejected"},
    )
    assert reject_response.status_code == 200


# ==================== CHECK STATUS ====================


@pytest.mark.asyncio
async def test_check_connection_status(
    student_client, teacher_user
):
    """GET /tutoring-requests/check/{teacher_id} — статус связи."""
    response = await student_client.get(
        f"/api/tutoring-requests/check/{teacher_user.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_connected"] is False
    assert data["has_pending_request"] is False