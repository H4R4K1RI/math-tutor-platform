import pytest
from httpx import AsyncClient


# ==================== ADD PAYMENT ====================


@pytest.mark.asyncio
async def test_add_payment(
    teacher_client, student_user, teacher_student_pair
):
    """Учитель добавляет платёж → баланс увеличивается."""
    response = await teacher_client.post(
        "/api/payments",
        json={"student_id": student_user.id, "amount": 1000, "note": "March"},
    )
    assert response.status_code == 200
    assert float(response.json()["new_balance"]) == 1000


@pytest.mark.asyncio
async def test_add_payment_negative_amount(
    teacher_client, student_user, teacher_student_pair
):
    """Отрицательный платёж → 422."""
    response = await teacher_client.post(
        "/api/payments",
        json={"student_id": student_user.id, "amount": -100},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_payment_to_foreign_student(
    teacher_client, db_session
):
    """Платёж чужому ученику → 403."""
    from app.shared.security import get_password_hash
    from app.models.user import User

    foreign_student = User(
        email="foreign@test.com",
        full_name="Foreign Student",
        hashed_password=get_password_hash("password123"),
        role="student",
        is_active=True,
        is_verified=True,
    )
    db_session.add(foreign_student)
    await db_session.commit()
    await db_session.refresh(foreign_student)

    response = await teacher_client.post(
        "/api/payments",
        json={"student_id": foreign_student.id, "amount": 1000},
    )
    assert response.status_code == 403


# ==================== LIST ====================


@pytest.mark.asyncio
async def test_get_students_balance(
    teacher_client, student_user, teacher_student_pair
):
    """Список учеников с балансами."""
    await teacher_client.post(
        "/api/payments",
        json={"student_id": student_user.id, "amount": 1000},
    )

    response = await teacher_client.get("/api/payments/students")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["student_id"] == student_user.id
    assert float(data[0]["balance"]) == 1000
    assert float(data[0]["total_paid"]) == 1000
    assert float(data[0]["total_debt"]) == 0


# ==================== HISTORY ====================


@pytest.mark.asyncio
async def test_payment_history_teacher(
    teacher_client, student_user, teacher_student_pair
):
    """Учитель видит историю платежей ученика."""
    await teacher_client.post(
        "/api/payments",
        json={"student_id": student_user.id, "amount": 500, "note": "First"},
    )
    await teacher_client.post(
        "/api/payments",
        json={"student_id": student_user.id, "amount": 300, "note": "Second"},
    )

    response = await teacher_client.get(
        f"/api/payments/history/{student_user.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["payments"]) == 2
    assert float(data["balance"]) == 800