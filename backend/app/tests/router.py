from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.auth.models import User
from app.shared.db import get_db
from app.tests.schemas import TestCreate, TestSubmit
from app.tests.service import TestsService

router = APIRouter(prefix="/tests", tags=["tests"])


# ==================== TEACHER ====================


@router.post("/")
async def create_test(
    test_data: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Создать новый тест."""
    service = TestsService(db)
    return await service.create_test(test_data, current_user)


@router.get("/")
async def get_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Список тестов учителя."""
    service = TestsService(db)
    return await service.get_teacher_tests(current_user)


# ==================== STUDENT (специфичные — до /{test_id}) ====================


@router.get("/assigned")
async def get_my_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Тесты, назначенные ученику."""
    service = TestsService(db)
    return await service.get_assigned_tests(current_user)


# ==================== SUBMIT (2 сегмента) ====================


@router.post("/submit/{user_test_id}")
async def submit_test(
    user_test_id: int,
    submission: TestSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отправить ответы и завершить тест."""
    service = TestsService(db)
    return await service.submit_test(user_test_id, submission, current_user)


# ==================== RESULTS (специфичные — до /{test_id}) ====================


@router.get("/results/{test_id}")
async def get_test_results(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Результаты теста для учителя."""
    service = TestsService(db)
    return await service.get_test_results(test_id, current_user)


@router.get("/student/{test_id}")
async def get_my_test_result(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Результат ученика по тесту."""
    service = TestsService(db)
    return await service.get_my_test_result(test_id, current_user)


# ==================== START (2 сегмента) ====================


@router.post("/{test_id}/start")
async def start_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Начать прохождение теста."""
    service = TestsService(db)
    return await service.start_test(test_id, current_user)


# ==================== UPDATE / DELETE ====================


@router.put("/{test_id}")
async def update_test(
    test_id: int,
    test_data: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновить тест."""
    service = TestsService(db)
    return await service.update_test(test_id, test_data, current_user)


@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удалить тест."""
    service = TestsService(db)
    return await service.delete_test(test_id, current_user)


# ==================== RESULT (teacher, per student) ====================


@router.get("/{test_id}/results/{user_id}")
async def get_student_test_result(
    test_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Детальный результат ученика по тесту."""
    service = TestsService(db)
    return await service.get_student_test_result(test_id, user_id, current_user)


# ==================== DETAIL (общий — В САМОМ КОНЦЕ!) ====================


@router.get("/{test_id}")
async def get_test_detail(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Детали теста."""
    service = TestsService(db)
    return await service.get_test_detail(test_id, current_user)