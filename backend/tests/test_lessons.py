from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


def _future_iso(hours: int = 24) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _future_iso_end(hours: int = 25) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


# ==================== CREATE ====================


@pytest.mark.asyncio
async def test_create_lesson_with_payment(
    teacher_client, student_user, teacher_user, teacher_student_pair
):
    """Создание урока → списание с баланса."""
    # 1. Учитель кладёт деньги на баланс ученика
    payment_response = await teacher_client.post(
        "/api/payments",
        json={"student_id": student_user.id, "amount": 5000, "note": "Deposit"},
    )
    assert payment_response.status_code == 200

    # 2. Создаём урок за 1000
    response = await teacher_client.post(
        "/api/lessons",
        json={
            "student_id": student_user.id,
            "title": "Math Lesson",
            "start_time": _future_iso(24),
            "end_time": _future_iso_end(25),
            "price": 1000,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Math Lesson"
    assert float(data["price"]) == 1000

    # 3. Проверяем баланс — 5000 - 1000 = 4000
    balance_response = await teacher_client.get("/api/payments/students")
    assert balance_response.status_code == 200
    students = balance_response.json()
    student_balance = next(
        s for s in students if s["student_id"] == student_user.id
    )
    assert float(student_balance["balance"]) == 4000


@pytest.mark.asyncio
async def test_create_lesson_insufficient_funds(
    teacher_client, student_user, teacher_student_pair
):
    """Недостаточно средств → 400."""
    response = await teacher_client.post(
        "/api/lessons",
        json={
            "student_id": student_user.id,
            "title": "Expensive",
            "start_time": _future_iso(24),
            "end_time": _future_iso_end(25),
            "price": 10000,
        },
    )
    assert response.status_code == 400
    assert "недостаточно" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_lesson_in_past(
    teacher_client, student_user, teacher_student_pair
):
    """Урок в прошлом → 400."""
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    past_end = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    response = await teacher_client.post(
        "/api/lessons",
        json={
            "student_id": student_user.id,
            "title": "Past",
            "start_time": past,
            "end_time": past_end,
            "price": 0,
        },
    )
    assert response.status_code == 400


# ==================== UPDATE (пересчёт) ====================


@pytest.mark.asyncio
async def test_update_lesson_price_recalculates_balance(
    teacher_client, student_user, teacher_student_pair
):
    """Изменение цены урока → корректировка баланса."""
    # 1. Платёж 5000
    await teacher_client.post(
        "/api/payments",
        json={"student_id": student_user.id, "amount": 5000},
    )

    # 2. Урок за 1000
    lesson_response = await teacher_client.post(
        "/api/lessons",
        json={
            "student_id": student_user.id,
            "title": "Recalc",
            "start_time": _future_iso(24),
            "end_time": _future_iso_end(25),
            "price": 1000,
        },
    )
    lesson_id = lesson_response.json()["id"]

    # 3. Меняем цену на 500
    update_response = await teacher_client.put(
        f"/api/lessons/{lesson_id}",
        json={"price": 500},
    )
    assert update_response.status_code == 200

    # 4. Баланс: 5000 - 500 = 4500
    balance_response = await teacher_client.get("/api/payments/students")
    students = balance_response.json()
    student_balance = next(
        s for s in students if s["student_id"] == student_user.id
    )
    assert float(student_balance["balance"]) == 4500


# ==================== DELETE (возврат) ====================


@pytest.mark.asyncio
async def test_delete_lesson_refunds_balance(
    teacher_client, student_user, teacher_student_pair
):
    """Отмена урока → возврат денег."""
    # 1. Платёж 5000
    await teacher_client.post(
        "/api/payments",
        json={"student_id": student_user.id, "amount": 5000},
    )

    # 2. Урок за 1000
    lesson_response = await teacher_client.post(
        "/api/lessons",
        json={
            "student_id": student_user.id,
            "title": "To Cancel",
            "start_time": _future_iso(24),
            "end_time": _future_iso_end(25),
            "price": 1000,
        },
    )
    lesson_id = lesson_response.json()["id"]

    # 3. Отменяем
    delete_response = await teacher_client.delete(f"/api/lessons/{lesson_id}")
    assert delete_response.status_code == 200

    # 4. Баланс: 5000 (вернулось 1000)
    balance_response = await teacher_client.get("/api/payments/students")
    students = balance_response.json()
    student_balance = next(
        s for s in students if s["student_id"] == student_user.id
    )
    assert float(student_balance["balance"]) == 5000