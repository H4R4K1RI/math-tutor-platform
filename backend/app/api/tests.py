import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_teacher, get_current_user
from app.shared.db import get_db
from app.models.answer_option import AnswerOption
from app.models.chat import Chat
from app.models.group_student import GroupStudent
from app.models.question import Question
from app.models.test import Test
from app.models.user import User
from app.models.user_answer import UserAnswer
from app.models.user_test import UserTest
from app.socket_manager import sio

router = APIRouter(prefix="/tests", tags=["tests"])


# ========== Pydantic схемы ==========


class AnswerOptionCreate(BaseModel):
    text: str
    is_correct: bool
    order: int = 0


class QuestionCreate(BaseModel):
    text: str
    type: str
    points: float = 1
    order: int = 0
    correct_answer: Optional[str] = None
    options: List[AnswerOptionCreate] = []


class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit: Optional[int] = None
    shuffle_questions: bool = False
    show_results_immediately: bool = True
    attempts: int = Field(default=1, ge=1)
    passing_score: int = Field(default=70, ge=0, le=100)
    group_id: Optional[int] = None
    student_id: Optional[int] = None
    questions: List[QuestionCreate]

# ========== Эндпоинты ==========


@router.post("/")
async def create_test(
    test_data: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Создать новый тест"""

    new_test = Test(
        teacher_id=current_user.id,
        title=test_data.title,
        description=test_data.description,
        time_limit=test_data.time_limit,
        shuffle_questions=test_data.shuffle_questions,
        show_results_immediately=test_data.show_results_immediately,
        attempts=test_data.attempts,
        passing_score=test_data.passing_score,
        group_id=test_data.group_id,
        student_id=test_data.student_id,
    )

    db.add(new_test)
    await db.flush()

    for q_data in test_data.questions:
        question = Question(
            test_id=new_test.id,
            text=q_data.text,
            type=q_data.type,
            points=q_data.points,
            order=q_data.order,
            correct_answer=q_data.correct_answer,
        )
        db.add(question)
        await db.flush()

        for opt_data in q_data.options:
            option = AnswerOption(
                question_id=question.id,
                text=opt_data.text,
                is_correct=opt_data.is_correct,
                order=opt_data.order,
            )
            db.add(option)

    await db.commit()
    await db.refresh(new_test)

    await sio.emit("test_created", {"test_id": new_test.id, "title": new_test.title})

    return {"id": new_test.id, "message": "Test created successfully"}


@router.get("/")
async def get_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить список тестов учителя (оптимизировано)"""

    result = await db.execute(
        select(Test)
        .where(Test.teacher_id == current_user.id)
        .order_by(Test.created_at.desc())
    )
    tests = result.scalars().all()

    if not tests:
        return []

    test_ids = [t.id for t in tests]

    count_result = await db.execute(
        select(Question.test_id, func.count(Question.id))
        .where(Question.test_id.in_(test_ids))
        .group_by(Question.test_id)
    )
    counts = {row[0]: row[1] for row in count_result.all()}

    response = []
    for test in tests:
        response.append(
            {
                "id": test.id,
                "title": test.title,
                "description": test.description,
                "time_limit": test.time_limit,
                "passing_score": test.passing_score,
                "is_active": test.is_active,
                "created_at": test.created_at,
                "questions_count": counts.get(test.id, 0),
            }
        )

    return response


@router.get("/assigned")
async def get_my_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить тесты, назначенные ученику.

    Включает:
    1. Личные тесты (student_id == current_user.id)
    2. Групповые (student в группе)
    3. «Для всех» (student_id IS NULL AND group_id IS NULL) — только
       от учителей, с которыми ученик связан.
    """

    # 1. Личные
    personal_tests_result = await db.execute(
        select(Test).where(
            Test.student_id == current_user.id,
            Test.is_active.is_(True),
        )
    )
    personal_tests = personal_tests_result.scalars().all()

    # 2. Групповые
    group_result = await db.execute(
        select(GroupStudent.group_id).where(GroupStudent.student_id == current_user.id)
    )
    group_ids = [row[0] for row in group_result.all()]

    group_tests = []
    if group_ids:
        group_tests_result = await db.execute(
            select(Test).where(
                Test.group_id.in_(group_ids),
                Test.is_active.is_(True),
            )
        )
        group_tests = group_tests_result.scalars().all()

    # 3. «Для всех» — только от связанных учителей
    teacher_ids_result = await db.execute(
        select(Chat.teacher_id).where(Chat.student_id == current_user.id).distinct()
    )
    teacher_ids = [row[0] for row in teacher_ids_result.all()]

    common_tests = []
    if teacher_ids:
        common_tests_result = await db.execute(
            select(Test).where(
                Test.student_id.is_(None),
                Test.group_id.is_(None),
                Test.teacher_id.in_(teacher_ids),
                Test.is_active.is_(True),
            )
        )
        common_tests = common_tests_result.scalars().all()

    # 4. Объединяем, дедупликация
    all_tests = list(
        {
            t.id: t
            for t in list(personal_tests) + list(group_tests) + list(common_tests)
        }.values()
    )

    if not all_tests:
        return []

    test_ids = [t.id for t in all_tests]

    user_tests_result = await db.execute(
        select(UserTest)
        .where(
            UserTest.test_id.in_(test_ids),
            UserTest.user_id == current_user.id,
            UserTest.status == "completed",
        )
        .order_by(UserTest.finished_at.desc())
    )
    user_tests = user_tests_result.scalars().all()

    user_tests_map = {}
    for ut in user_tests:
        if ut.test_id not in user_tests_map:
            user_tests_map[ut.test_id] = ut

    results = []
    for test in all_tests:
        user_test = user_tests_map.get(test.id)

        results.append(
            {
                "id": test.id,
                "title": test.title,
                "description": test.description,
                "time_limit": test.time_limit,
                "passing_score": test.passing_score,
                "is_completed": user_test is not None,
                "score": user_test.score if user_test else None,
                "passed": (
                    (user_test.score >= test.passing_score) if user_test else None
                ),
            }
        )

    return results


@router.get("/{test_id}")
async def get_test_detail(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить детали теста (оптимизировано)"""

    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if current_user.role == "teacher":
        if test.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    questions_result = await db.execute(
        select(Question).where(Question.test_id == test_id).order_by(Question.order)
    )
    questions = questions_result.scalars().all()

    if not questions:
        return {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "time_limit": test.time_limit,
            "shuffle_questions": test.shuffle_questions,
            "passing_score": test.passing_score,
            "created_at": test.created_at,
            "questions": [],
        }

    question_ids = [q.id for q in questions]

    options_result = await db.execute(
        select(AnswerOption)
        .where(AnswerOption.question_id.in_(question_ids))
        .order_by(AnswerOption.order)
    )
    options = options_result.scalars().all()

    options_by_question: dict[int, list] = {}
    for opt in options:
        options_by_question.setdefault(opt.question_id, []).append(opt)

    is_teacher_owner = (
        current_user.role == "teacher" and test.teacher_id == current_user.id
    )

    questions_data = []
    for q in questions:
        q_options = options_by_question.get(q.id, [])

        # Учителю — отдаём is_correct, ученику — нет
        options_payload = []
        for opt in q_options:
            option_dict = {"id": opt.id, "text": opt.text, "order": opt.order}
            if is_teacher_owner:
                option_dict["is_correct"] = opt.is_correct
            options_payload.append(option_dict)

            question_dict = {
            "id": q.id,
            "text": q.text,
            "type": q.type,
            "points": q.points,
            "order": q.order,
            "options": options_payload,
        }
            
        if is_teacher_owner and q.type in ("open", "number"):
            question_dict["correct_answer"] = q.correct_answer

        questions_data.append(question_dict)

    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "time_limit": test.time_limit,
        "shuffle_questions": test.shuffle_questions,
        "passing_score": test.passing_score,
        "created_at": test.created_at,
        "questions": questions_data,
    }


@router.put("/{test_id}")
async def update_test(
    test_id: int,
    test_data: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновить тест"""

    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.teacher_id == current_user.id)
    )
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    test.title = test_data.title
    test.description = test_data.description
    test.time_limit = test_data.time_limit
    test.shuffle_questions = test_data.shuffle_questions
    test.show_results_immediately = test_data.show_results_immediately
    test.attempts = test_data.attempts
    test.passing_score = test_data.passing_score
    test.group_id = test_data.group_id
    test.student_id = test_data.student_id

    await db.execute(delete(Question).where(Question.test_id == test_id))

    for q_data in test_data.questions:
        question = Question(
            test_id=test_id,
            text=q_data.text,
            type=q_data.type,
            points=q_data.points,
            order=q_data.order,
            correct_answer=q_data.correct_answer,
        )
        db.add(question)
        await db.flush()

        for opt_data in q_data.options:
            option = AnswerOption(
                question_id=question.id,
                text=opt_data.text,
                is_correct=opt_data.is_correct,
                order=opt_data.order,
            )
            db.add(option)

    await db.commit()

    return {"message": "Test updated successfully"}


@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удалить тест"""

    result = await db.execute(
        select(Test).where(Test.id == test_id, Test.teacher_id == current_user.id)
    )
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    await db.delete(test)
    await db.commit()

    await sio.emit("test_deleted", {"test_id": test_id})

    return {"message": "Test deleted successfully"}


# ========== Схемы для прохождения тестов ==========


class AnswerSubmit(BaseModel):
    question_id: int
    answer: str


class TestSubmit(BaseModel):
    answers: List[AnswerSubmit]


# ========== Эндпоинты для учеников ==========


@router.post("/{test_id}/start")
async def start_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Начать прохождение теста (ученик) — оптимизировано"""

    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if not test.is_active:
        raise HTTPException(status_code=400, detail="Test is not active")

    # Проверка доступа
    if test.student_id is not None and test.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if test.group_id is not None:
        group_result = await db.execute(
            select(GroupStudent).where(
                GroupStudent.group_id == test.group_id,
                GroupStudent.student_id == current_user.id,
            )
        )
        if not group_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied")

    # Если тест «для всех» — проверяем связь с учителем
    if test.student_id is None and test.group_id is None:
        chat_result = await db.execute(
            select(Chat).where(
                Chat.teacher_id == test.teacher_id,
                Chat.student_id == current_user.id,
            )
        )
        if not chat_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied")

    attempts_result = await db.execute(
        select(func.count(UserTest.id)).where(
            UserTest.test_id == test_id,
            UserTest.user_id == current_user.id,
            UserTest.status == "completed",
        )
    )
    completed_attempts = attempts_result.scalar() or 0

    if completed_attempts >= test.attempts:
        raise HTTPException(
            status_code=400, detail=f"Maximum attempts ({test.attempts}) reached"
        )

    user_test = UserTest(test_id=test_id, user_id=current_user.id, status="in_progress")
    db.add(user_test)
    await db.commit()
    await db.refresh(user_test)

    questions_result = await db.execute(
        select(Question).where(Question.test_id == test_id).order_by(Question.order)
    )
    questions = questions_result.scalars().all()

    if not questions:
        return {
            "user_test_id": user_test.id,
            "test_id": test.id,
            "title": test.title,
            "description": test.description,
            "time_limit": test.time_limit,
            "questions": [],
        }

    question_ids = [q.id for q in questions]

    options_result = await db.execute(
        select(AnswerOption)
        .where(AnswerOption.question_id.in_(question_ids))
        .order_by(AnswerOption.order)
    )
    options = options_result.scalars().all()

    options_by_question: dict[int, list] = {}
    for opt in options:
        options_by_question.setdefault(opt.question_id, []).append(opt)

    questions_data = []
    for q in questions:
        q_options = options_by_question.get(q.id, [])
        questions_data.append(
            {
                "id": q.id,
                "text": q.text,
                "type": q.type,
                "points": q.points,
                "options": (
                    [{"id": opt.id, "text": opt.text} for opt in q_options]
                    if q.type in ["single", "multiple"]
                    else []
                ),
            }
        )

    return {
        "user_test_id": user_test.id,
        "test_id": test.id,
        "title": test.title,
        "description": test.description,
        "time_limit": test.time_limit,
        "questions": questions_data,
    }


@router.post("/submit/{user_test_id}")
async def submit_test(
    user_test_id: int,
    submission: TestSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отправить ответы и завершить тест"""

    result = await db.execute(
        select(UserTest).where(
            UserTest.id == user_test_id, UserTest.user_id == current_user.id
        )
    )
    user_test = result.scalar_one_or_none()

    if not user_test:
        raise HTTPException(status_code=404, detail="Test attempt not found")

    if user_test.status == "completed":
        raise HTTPException(status_code=400, detail="Test already completed")

    test_result = await db.execute(select(Test).where(Test.id == user_test.test_id))
    test = test_result.scalar_one_or_none()

    questions_result = await db.execute(
        select(Question).where(Question.test_id == test.id)
    )
    questions = {q.id: q for q in questions_result.scalars().all()}

    options_result = await db.execute(
        select(AnswerOption).where(
            AnswerOption.question_id.in_([q.id for q in questions.values()])
        )
    )
    correct_options = {}
    for opt in options_result.scalars().all():
        if opt.question_id not in correct_options:
            correct_options[opt.question_id] = []
        if opt.is_correct:
            correct_options[opt.question_id].append(opt.id)

    total_score = 0
    max_score = 0

    for answer in submission.answers:
        question = questions.get(answer.question_id)
        if not question:
            continue

        max_score += question.points
        is_correct = False

        if question.type == "single":
            selected_option = int(answer.answer) if answer.answer else None
            correct = correct_options.get(question.id, [])
            is_correct = len(correct) == 1 and selected_option == correct[0]

        elif question.type == "multiple":
            # answer.answer — JSON-строка типа "[1,2,3]" или пустая
            selected_options = set()
            if answer.answer:
                try:
                    parsed = json.loads(answer.answer)
                    if isinstance(parsed, list):
                        selected_options = set(int(x) for x in parsed)
                except (ValueError, TypeError):
                    # fallback: если не JSON — попробуем как список через запятую
                    selected_options = set(
                        int(x.strip()) for x in str(answer.answer).split(",") if x.strip().isdigit()
                    )
            correct_set = set(correct_options.get(question.id, []))
            is_correct = selected_options == correct_set

        elif question.type == "number":
            try:
                user_number = float(answer.answer) if answer.answer else None
                correct_number = (
                    float(question.correct_answer) if question.correct_answer else None
                )
                is_correct = user_number == correct_number
            except Exception:
                is_correct = False

        elif question.type == "open":
            is_correct = None

        if is_correct:
            total_score += question.points

        user_answer = UserAnswer(
            user_test_id=user_test_id,
            question_id=question.id,
            answer=answer.answer,
            is_correct=is_correct if is_correct is not None else False,
            points_earned=question.points if is_correct else 0,
        )
        db.add(user_answer)

    score_percent = int((total_score / max_score) * 100) if max_score > 0 else 0

    user_test.status = "completed"
    user_test.finished_at = datetime.now(timezone.utc)
    user_test.score = score_percent
    user_test.max_score = max_score

    await db.commit()

    await sio.emit(
        "test_completed",
        {
            "test_id": test.id,
            "student_id": current_user.id,
            "student_name": current_user.full_name,
            "score": score_percent,
        },
    )

    return {
        "score": score_percent,
        "max_score": max_score,
        "total_earned": total_score,
        "passing_score": test.passing_score,
        "passed": score_percent >= test.passing_score,
        "message": "Test submitted successfully",
    }


@router.get("/results/{test_id}")
async def get_test_results(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить результаты теста для учителя (оптимизировано)"""

    test_result = await db.execute(
        select(Test).where(Test.id == test_id, Test.teacher_id == current_user.id)
    )
    test = test_result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    attempts_result = await db.execute(
        select(UserTest).where(
            UserTest.test_id == test_id, UserTest.status == "completed"
        )
    )
    attempts = attempts_result.scalars().all()

    if not attempts:
        return {
            "test": {
                "id": test.id,
                "title": test.title,
                "passing_score": test.passing_score,
            },
            "statistics": {
                "total_attempts": 0,
                "passed": 0,
                "passed_percent": 0,
                "average_score": 0,
            },
            "results": [],
        }

    user_ids = {a.user_id for a in attempts}
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    results = []
    for attempt in attempts:
        student = users_map.get(attempt.user_id)
        results.append(
            {
                "user_test_id": attempt.id,
                "student_id": attempt.user_id,
                "student_name": student.full_name if student else "Unknown",
                "score": attempt.score,
                "max_score": attempt.max_score,
                "passed": attempt.score >= test.passing_score,
                "started_at": attempt.started_at,
                "finished_at": attempt.finished_at,
            }
        )

    total_attempts = len(results)
    passed = sum(1 for r in results if r["passed"])
    average_score = (
        sum(r["score"] for r in results) / total_attempts if total_attempts > 0 else 0
    )

    return {
        "test": {
            "id": test.id,
            "title": test.title,
            "passing_score": test.passing_score,
        },
        "statistics": {
            "total_attempts": total_attempts,
            "passed": passed,
            "passed_percent": (
                int((passed / total_attempts) * 100) if total_attempts > 0 else 0
            ),
            "average_score": round(average_score, 1),
        },
        "results": results,
    }


@router.get("/student/{test_id}")
async def get_my_test_result(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить результат ученика по тесту (оптимизировано)"""

    result = await db.execute(
        select(UserTest)
        .where(
            UserTest.test_id == test_id,
            UserTest.user_id == current_user.id,
            UserTest.status == "completed",
        )
        .order_by(UserTest.finished_at.desc())
        .limit(1)
    )
    user_test = result.scalar_one_or_none()

    if not user_test:
        raise HTTPException(status_code=404, detail="Test result not found")

    test_result = await db.execute(select(Test).where(Test.id == test_id))
    test = test_result.scalar_one_or_none()

    answers_result = await db.execute(
        select(UserAnswer).where(UserAnswer.user_test_id == user_test.id)
    )
    answers = answers_result.scalars().all()

    questions_result = await db.execute(
        select(Question).where(Question.test_id == test_id)
    )
    questions = {q.id: q for q in questions_result.scalars().all()}

    answers_data = []
    for ans in answers:
        question = questions.get(ans.question_id)
        answers_data.append(
            {
                "question_id": ans.question_id,
                "question_text": question.text if question else "",
                "user_answer": ans.answer,
                "is_correct": ans.is_correct,
                "points_earned": ans.points_earned,
                "max_points": question.points if question else 0,
            }
        )

    return {
        "score": user_test.score,
        "max_score": user_test.max_score,
        "passed": user_test.score >= test.passing_score if test else False,
        "passing_score": test.passing_score if test else 0,
        "started_at": user_test.started_at,
        "finished_at": user_test.finished_at,
        "answers": answers_data,
    }


@router.get("/{test_id}/results/{user_id}")
async def get_student_test_result(
    test_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить детальный результат ученика по тесту (оптимизировано)"""

    test_result = await db.execute(
        select(Test).where(Test.id == test_id, Test.teacher_id == current_user.id)
    )
    test = test_result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    user_test_result = await db.execute(
        select(UserTest).where(
            UserTest.test_id == test_id,
            UserTest.user_id == user_id,
            UserTest.status == "completed",
        )
    )
    user_test = user_test_result.scalar_one_or_none()
    if not user_test:
        raise HTTPException(status_code=404, detail="No attempts found")

    answers_result = await db.execute(
        select(UserAnswer).where(UserAnswer.user_test_id == user_test.id)
    )
    answers = answers_result.scalars().all()

    questions_result = await db.execute(
        select(Question).where(Question.test_id == test_id)
    )
    questions = {q.id: q for q in questions_result.scalars().all()}

    real_max_score = sum(q.points for q in questions.values())

    all_question_ids = [q.id for q in questions.values()]
    options_result = await db.execute(
        select(AnswerOption).where(AnswerOption.question_id.in_(all_question_ids))
    )
    options_by_question: dict[int, list] = {}
    for opt in options_result.scalars().all():
        options_by_question.setdefault(opt.question_id, []).append(
            {"id": opt.id, "text": opt.text, "is_correct": opt.is_correct}
        )

    answers_data = []
    total_earned = 0
    for ans in answers:
        q = questions.get(ans.question_id)
        if not q:
            continue

        total_earned += ans.points_earned
        options = options_by_question.get(q.id, [])

        answers_data.append(
            {
                "question_id": ans.question_id,
                "question_text": q.text,
                "user_answer": ans.answer,
                "is_correct": ans.is_correct,
                "points_earned": ans.points_earned,
                "max_points": q.points,
                "options": options,
            }
        )

    return {
        "student_id": user_id,
        "score": user_test.score,
        "max_score": real_max_score,
        "total_earned": total_earned,
        "passed": user_test.score >= test.passing_score,
        "started_at": user_test.started_at,
        "finished_at": user_test.finished_at,
        "answers": answers_data,
    }