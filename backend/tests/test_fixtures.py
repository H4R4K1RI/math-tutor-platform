import pytest


@pytest.mark.asyncio
async def test_teacher_user(teacher_user):
    assert teacher_user.email == "teacher@test.com"
    assert teacher_user.role == "teacher"


@pytest.mark.asyncio
async def test_student_user(student_user):
    assert student_user.email == "student@test.com"
    assert student_user.role == "student"


@pytest.mark.asyncio
async def test_client(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_teacher_client(teacher_client):
    response = await teacher_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "teacher@test.com"


@pytest.mark.asyncio
async def test_teacher_student_pair(teacher_student_pair):
    assert teacher_student_pair["teacher"].role == "teacher"
    assert teacher_student_pair["student"].role == "student"
    assert teacher_student_pair["chat"].id is not None