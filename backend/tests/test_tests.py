import pytest
from httpx import AsyncClient


def _make_test_payload(
    title: str = "Test 1",
    student_id: int | None = None,
    passing_score: int = 70,
) -> dict:
    """Полезная нагрузка для создания теста."""
    return {
        "title": title,
        "description": "Test description",
        "time_limit": 30,
        "passing_score": passing_score,
        "student_id": student_id,
        "group_id": None,
        "questions": [
            {
                "text": "2 + 2 = ?",
                "type": "single",
                "points": 1,
                "order": 0,
                "options": [
                    {"text": "3", "is_correct": False, "order": 0},
                    {"text": "4", "is_correct": True, "order": 1},
                    {"text": "5", "is_correct": False, "order": 2},
                ],
            },
            {
                "text": "Столица России?",
                "type": "single",
                "points": 1,
                "order": 1,
                "options": [
                    {"text": "Москва", "is_correct": True, "order": 0},
                    {"text": "Питер", "is_correct": False, "order": 1},
                ],
            },
        ],
    }


# ==================== CREATE ====================


@pytest.mark.asyncio
async def test_create_test_teacher(
    teacher_client, student_user, teacher_student_pair
):
    """Учитель создаёт тест."""
    payload = _make_test_payload(student_id=student_user.id)
    response = await teacher_client.post("/api/tests", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_create_test_student_forbidden(student_client):
    """Ученик не может создавать тесты → 403."""
    payload = _make_test_payload()
    response = await student_client.post("/api/tests", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_test_invalid_passing_score(teacher_client):
    """passing_score > 100 → 422."""
    payload = _make_test_payload(passing_score=200)
    response = await teacher_client.post("/api/tests", json=payload)
    assert response.status_code == 422


# ==================== LIST ====================


@pytest.mark.asyncio
async def test_get_tests_teacher(
    teacher_client, student_user, teacher_student_pair
):
    """Учитель видит свои тесты с количеством вопросов."""
    await teacher_client.post(
        "/api/tests",
        json=_make_test_payload(student_id=student_user.id),
    )

    response = await teacher_client.get("/api/tests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["questions_count"] == 2


# ==================== GET DETAIL ====================


@pytest.mark.asyncio
async def test_get_test_detail_teacher_has_is_correct(
    teacher_client, student_user, teacher_student_pair
):
    """Учитель видит is_correct для опций."""
    create_response = await teacher_client.post(
        "/api/tests",
        json=_make_test_payload(student_id=student_user.id),
    )
    test_id = create_response.json()["id"]

    response = await teacher_client.get(f"/api/tests/{test_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 2

    # Проверяем, что is_correct есть
    for q in data["questions"]:
        for opt in q["options"]:
            assert "is_correct" in opt


# ==================== ASSIGNED ====================


@pytest.mark.asyncio
async def test_get_assigned_tests_student(
    teacher_client, student_client, student_user, teacher_student_pair
):
    """Ученик видит назначенные тесты."""
    await teacher_client.post(
        "/api/tests",
        json=_make_test_payload(student_id=student_user.id),
    )

    response = await student_client.get("/api/tests/assigned")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["is_completed"] is False


# ==================== START + SUBMIT ====================


@pytest.mark.asyncio
async def test_start_and_submit_test(
    teacher_client, student_client, student_user, teacher_student_pair
):
    """Ученик проходит тест и получает результат."""
    # 1. Учитель создаёт тест
    create_response = await teacher_client.post(
        "/api/tests",
        json=_make_test_payload(student_id=student_user.id),
    )
    test_id = create_response.json()["id"]

    # 2. Ученик начинает тест
    start_response = await student_client.post(f"/api/tests/{test_id}/start")
    assert start_response.status_code == 200, start_response.text
    start_data = start_response.json()
    user_test_id = start_data["user_test_id"]

    # 3. Ученик отвечает правильно
    # Находим опции с правильными ответами
    test_detail = await teacher_client.get(f"/api/tests/{test_id}")
    questions = test_detail.json()["questions"]

    answers = []
    for q in questions:
        correct_opt = next(o for o in q["options"] if o.get("is_correct"))
        answers.append({"question_id": q["id"], "answer": str(correct_opt["id"])})

    submit_response = await student_client.post(
        f"/api/tests/submit/{user_test_id}",
        json={"answers": answers},
    )
    assert submit_response.status_code == 200, submit_response.text
    submit_data = submit_response.json()
    assert submit_data["score"] == 100
    assert submit_data["passed"] is True


@pytest.mark.asyncio
async def test_submit_test_wrong_answers(
    teacher_client, student_client, student_user, teacher_student_pair
):
    """Неправильные ответы → score < 100."""
    create_response = await teacher_client.post(
        "/api/tests",
        json=_make_test_payload(student_id=student_user.id),
    )
    test_id = create_response.json()["id"]

    start_response = await student_client.post(f"/api/tests/{test_id}/start")
    user_test_id = start_response.json()["user_test_id"]

    test_detail = await teacher_client.get(f"/api/tests/{test_id}")
    questions = test_detail.json()["questions"]

    # Отвечаем неправильно
    answers = []
    for q in questions:
        wrong_opt = next(o for o in q["options"] if not o.get("is_correct"))
        answers.append({"question_id": q["id"], "answer": str(wrong_opt["id"])})

    submit_response = await student_client.post(
        f"/api/tests/submit/{user_test_id}",
        json={"answers": answers},
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["score"] == 0


# ==================== STUDENT RESULT ====================


@pytest.mark.asyncio
async def test_student_gets_own_result(
    teacher_client, student_client, student_user, teacher_student_pair
):
    """Ученик получает свой результат."""
    create_response = await teacher_client.post(
        "/api/tests",
        json=_make_test_payload(student_id=student_user.id),
    )
    test_id = create_response.json()["id"]

    start_response = await student_client.post(f"/api/tests/{test_id}/start")
    user_test_id = start_response.json()["user_test_id"]

    test_detail = await teacher_client.get(f"/api/tests/{test_id}")
    questions = test_detail.json()["questions"]

    answers = []
    for q in questions:
        correct_opt = next(o for o in q["options"] if o.get("is_correct"))
        answers.append({"question_id": q["id"], "answer": str(correct_opt["id"])})

    await student_client.post(
        f"/api/tests/submit/{user_test_id}",
        json={"answers": answers},
    )

    # Ученик получает результат
    result_response = await student_client.get(f"/api/tests/student/{test_id}")
    assert result_response.status_code == 200
    data = result_response.json()
    assert data["score"] == 100
    assert data["passed"] is True


# ==================== UPDATE ====================


@pytest.mark.asyncio
async def test_update_test(
    teacher_client, student_user, teacher_student_pair
):
    """PUT /tests/{id} — обновление."""
    create_response = await teacher_client.post(
        "/api/tests",
        json=_make_test_payload(student_id=student_user.id),
    )
    test_id = create_response.json()["id"]

    updated_payload = _make_test_payload(
        title="Updated Test", student_id=student_user.id
    )
    response = await teacher_client.put(f"/api/tests/{test_id}", json=updated_payload)
    assert response.status_code == 200

    # Проверяем
    detail = await teacher_client.get(f"/api/tests/{test_id}")
    assert detail.json()["title"] == "Updated Test"


# ==================== DELETE ====================


@pytest.mark.asyncio
async def test_delete_test(
    teacher_client, student_user, teacher_student_pair
):
    """DELETE /tests/{id} — удаление."""
    create_response = await teacher_client.post(
        "/api/tests",
        json=_make_test_payload(student_id=student_user.id),
    )
    test_id = create_response.json()["id"]

    response = await teacher_client.delete(f"/api/tests/{test_id}")
    assert response.status_code == 200

    # Проверяем
    detail = await teacher_client.get(f"/api/tests/{test_id}")
    assert detail.status_code == 404