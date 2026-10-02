import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.models import Chat
from app.chat.socket import sio
from app.models.group_student import GroupStudent
from app.tests.models import (
    AnswerOption,
    Question,
    Test,
    UserAnswer,
    UserTest,
)
from app.tests.schemas import TestCreate, TestSubmit


def _grade_answer(question: Question, answer: str, correct_option_ids: list[int]) -> Optional[bool]:
    """Вычислить, правильный ли ответ.

    Возвращает True/False, либо None для типа 'open' (проверяется вручную).
    """
    if question.type == "single":
        try:
            selected = int(answer) if answer else None
        except (ValueError, TypeError):
            return False
        return len(correct_option_ids) == 1 and selected == correct_option_ids[0]

    if question.type == "multiple":
        selected: set[int] = set()
        if answer:
            try:
                parsed = json.loads(answer)
                if isinstance(parsed, list):
                    selected = {int(x) for x in parsed}
            except (ValueError, TypeError):
                # fallback: "1,2,3"
                selected = {
                    int(x.strip())
                    for x in str(answer).split(",")
                    if x.strip().isdigit()
                }
        return selected == set(correct_option_ids)

    if question.type == "number":
        try:
            user_number = float(answer) if answer else None
            correct_number = (
                float(question.correct_answer) if question.correct_answer else None
            )
            return user_number == correct_number
        except Exception:
            return False

    if question.type == "open":
        return None

    return False


class TestsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== CREATE ====================

    async def create_test(self, data: TestCreate, current_user: User) -> dict:
        new_test = Test(
            teacher_id=current_user.id,
            title=data.title,
            description=data.description,
            time_limit=data.time_limit,
            shuffle_questions=data.shuffle_questions,
            show_results_immediately=data.show_results_immediately,
            attempts=data.attempts,
            passing_score=data.passing_score,
            group_id=data.group_id,
            student_id=data.student_id,
        )

        self.db.add(new_test)
        await self.db.flush()

        for q_data in data.questions:
            question = Question(
                test_id=new_test.id,
                text=q_data.text,
                type=q_data.type,
                points=q_data.points,
                order=q_data.order,
                correct_answer=q_data.correct_answer,
            )
            self.db.add(question)
            await self.db.flush()

            for opt_data in q_data.options:
                self.db.add(
                    AnswerOption(
                        question_id=question.id,
                        text=opt_data.text,
                        is_correct=opt_data.is_correct,
                        order=opt_data.order,
                    )
                )

        await self.db.commit()
        await self.db.refresh(new_test)

        await sio.emit(
            "test_created", {"test_id": new_test.id, "title": new_test.title}
        )

        return {"id": new_test.id, "message": "Test created successfully"}

    # ==================== LIST ====================

    async def get_teacher_tests(self, current_user: User) -> list[dict]:
        result = await self.db.execute(
            select(Test)
            .where(Test.teacher_id == current_user.id)
            .order_by(Test.created_at.desc())
        )
        tests = result.scalars().all()

        if not tests:
            return []

        test_ids = [t.id for t in tests]

        count_result = await self.db.execute(
            select(Question.test_id, func.count(Question.id))
            .where(Question.test_id.in_(test_ids))
            .group_by(Question.test_id)
        )
        counts = {row[0]: row[1] for row in count_result.all()}

        return [
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
            for test in tests
        ]

    async def get_assigned_tests(self, current_user: User) -> list[dict]:
        """Тесты, назначенные ученику:
        1. Личные (student_id == current_user.id)
        2. Групповые (student в группе)
        3. «Для всех» — от связанных учителей.
        """
        personal_result = await self.db.execute(
            select(Test).where(
                Test.student_id == current_user.id,
                Test.is_active.is_(True),
            )
        )
        personal_tests = personal_result.scalars().all()

        group_result = await self.db.execute(
            select(GroupStudent.group_id).where(
                GroupStudent.student_id == current_user.id
            )
        )
        group_ids = [row[0] for row in group_result.all()]

        group_tests = []
        if group_ids:
            group_tests_result = await self.db.execute(
                select(Test).where(
                    Test.group_id.in_(group_ids),
                    Test.is_active.is_(True),
                )
            )
            group_tests = group_tests_result.scalars().all()

        teacher_ids_result = await self.db.execute(
            select(Chat.teacher_id)
            .where(Chat.student_id == current_user.id)
            .distinct()
        )
        teacher_ids = [row[0] for row in teacher_ids_result.all()]

        common_tests = []
        if teacher_ids:
            common_tests_result = await self.db.execute(
                select(Test).where(
                    Test.student_id.is_(None),
                    Test.group_id.is_(None),
                    Test.teacher_id.in_(teacher_ids),
                    Test.is_active.is_(True),
                )
            )
            common_tests = common_tests_result.scalars().all()

        all_tests = list(
            {
                t.id: t
                for t in list(personal_tests)
                + list(group_tests)
                + list(common_tests)
            }.values()
        )

        if not all_tests:
            return []

        test_ids = [t.id for t in all_tests]

        user_tests_result = await self.db.execute(
            select(UserTest)
            .where(
                UserTest.test_id.in_(test_ids),
                UserTest.user_id == current_user.id,
                UserTest.status == "completed",
            )
            .order_by(UserTest.finished_at.desc())
        )
        user_tests = user_tests_result.scalars().all()

        user_tests_map: dict[int, UserTest] = {}
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
                        (user_test.score >= test.passing_score)
                        if user_test
                        else None
                    ),
                }
            )

        return results

    # ==================== DETAIL ====================

    async def get_test_detail(self, test_id: int, current_user: User) -> dict:
        result = await self.db.execute(select(Test).where(Test.id == test_id))
        test = result.scalar_one_or_none()

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
            )

        if current_user.role == "teacher":
            if test.teacher_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                )

        questions_result = await self.db.execute(
            select(Question)
            .where(Question.test_id == test_id)
            .order_by(Question.order)
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

        options_result = await self.db.execute(
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

            options_payload = []
            for opt in q_options:
                option_dict = {"id": opt.id, "text": opt.text, "order": opt.order}
                if is_teacher_owner:
                    option_dict["is_correct"] = opt.is_correct
                options_payload.append(option_dict)

            # ФИКС БАГА: question_dict создаётся ВНЕ цикла по опциям
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

    # ==================== UPDATE ====================

    async def update_test(
        self, test_id: int, data: TestCreate, current_user: User
    ) -> dict:
        result = await self.db.execute(
            select(Test).where(
                Test.id == test_id, Test.teacher_id == current_user.id
            )
        )
        test = result.scalar_one_or_none()

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
            )

        test.title = data.title
        test.description = data.description
        test.time_limit = data.time_limit
        test.shuffle_questions = data.shuffle_questions
        test.show_results_immediately = data.show_results_immediately
        test.attempts = data.attempts
        test.passing_score = data.passing_score
        test.group_id = data.group_id
        test.student_id = data.student_id

        await self.db.execute(delete(Question).where(Question.test_id == test_id))

        for q_data in data.questions:
            question = Question(
                test_id=test_id,
                text=q_data.text,
                type=q_data.type,
                points=q_data.points,
                order=q_data.order,
                correct_answer=q_data.correct_answer,
            )
            self.db.add(question)
            await self.db.flush()

            for opt_data in q_data.options:
                self.db.add(
                    AnswerOption(
                        question_id=question.id,
                        text=opt_data.text,
                        is_correct=opt_data.is_correct,
                        order=opt_data.order,
                    )
                )

        await self.db.commit()

        return {"message": "Test updated successfully"}

    # ==================== DELETE ====================

    async def delete_test(self, test_id: int, current_user: User) -> dict:
        result = await self.db.execute(
            select(Test).where(
                Test.id == test_id, Test.teacher_id == current_user.id
            )
        )
        test = result.scalar_one_or_none()

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
            )

        await self.db.delete(test)
        await self.db.commit()

        await sio.emit("test_deleted", {"test_id": test_id})

        return {"message": "Test deleted successfully"}

        # ==================== START ====================

    async def start_test(self, test_id: int, current_user: User) -> dict:
        result = await self.db.execute(select(Test).where(Test.id == test_id))
        test = result.scalar_one_or_none()

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
            )

        if not test.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test is not active",
            )

        if test.student_id is not None and test.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        if test.group_id is not None:
            group_result = await self.db.execute(
                select(GroupStudent).where(
                    GroupStudent.group_id == test.group_id,
                    GroupStudent.student_id == current_user.id,
                )
            )
            if not group_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                )

        if test.student_id is None and test.group_id is None:
            chat_result = await self.db.execute(
                select(Chat).where(
                    Chat.teacher_id == test.teacher_id,
                    Chat.student_id == current_user.id,
                )
            )
            if not chat_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
                )

        attempts_result = await self.db.execute(
            select(func.count(UserTest.id)).where(
                UserTest.test_id == test_id,
                UserTest.user_id == current_user.id,
                UserTest.status == "completed",
            )
        )
        completed_attempts = attempts_result.scalar() or 0

        if completed_attempts >= test.attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum attempts ({test.attempts}) reached",
            )

        user_test = UserTest(
            test_id=test_id, user_id=current_user.id, status="in_progress"
        )
        self.db.add(user_test)
        await self.db.commit()
        await self.db.refresh(user_test)

        questions_result = await self.db.execute(
            select(Question)
            .where(Question.test_id == test_id)
            .order_by(Question.order)
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

        options_result = await self.db.execute(
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

    # ==================== SUBMIT ====================

    async def submit_test(
        self,
        user_test_id: int,
        submission: TestSubmit,
        current_user: User,
    ) -> dict:
        result = await self.db.execute(
            select(UserTest).where(
                UserTest.id == user_test_id,
                UserTest.user_id == current_user.id,
            )
        )
        user_test = result.scalar_one_or_none()

        if not user_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test attempt not found",
            )

        if user_test.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test already completed",
            )

        test_result = await self.db.execute(
            select(Test).where(Test.id == user_test.test_id)
        )
        test = test_result.scalar_one_or_none()

        questions_result = await self.db.execute(
            select(Question).where(Question.test_id == test.id)
        )
        questions: dict[int, Question] = {
            q.id: q for q in questions_result.scalars().all()
        }

        options_result = await self.db.execute(
            select(AnswerOption).where(
                AnswerOption.question_id.in_(
                    [q.id for q in questions.values()]
                )
            )
        )
        correct_options: dict[int, list[int]] = {}
        for opt in options_result.scalars().all():
            correct_options.setdefault(opt.question_id, [])
            if opt.is_correct:
                correct_options[opt.question_id].append(opt.id)

        total_score = 0.0
        max_score = 0.0

        for answer in submission.answers:
            question = questions.get(answer.question_id)
            if not question:
                continue

            max_score += question.points
            is_correct = _grade_answer(
                question,
                answer.answer,
                correct_options.get(question.id, []),
            )

            if is_correct:
                total_score += question.points

            self.db.add(
                UserAnswer(
                    user_test_id=user_test_id,
                    question_id=question.id,
                    answer=answer.answer,
                    is_correct=is_correct if is_correct is not None else False,
                    points_earned=question.points if is_correct else 0,
                )
            )

        score_percent = (
            int((total_score / max_score) * 100) if max_score > 0 else 0
        )

        user_test.status = "completed"
        user_test.finished_at = datetime.now(timezone.utc)
        user_test.score = score_percent
        user_test.max_score = max_score

        await self.db.commit()

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

    # ==================== RESULTS (teacher) ====================

    async def get_test_results(self, test_id: int, current_user: User) -> dict:
        test_result = await self.db.execute(
            select(Test).where(
                Test.id == test_id, Test.teacher_id == current_user.id
            )
        )
        test = test_result.scalar_one_or_none()

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
            )

        attempts_result = await self.db.execute(
            select(UserTest).where(
                UserTest.test_id == test_id,
                UserTest.status == "completed",
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
        users_result = await self.db.execute(
            select(User).where(User.id.in_(user_ids))
        )
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
            sum(r["score"] for r in results) / total_attempts
            if total_attempts > 0
            else 0
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
                    int((passed / total_attempts) * 100)
                    if total_attempts > 0
                    else 0
                ),
                "average_score": round(average_score, 1),
            },
            "results": results,
        }

    # ==================== RESULTS (student) ====================

    async def get_my_test_result(
        self, test_id: int, current_user: User
    ) -> dict:
        result = await self.db.execute(
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test result not found",
            )

        test_result = await self.db.execute(
            select(Test).where(Test.id == test_id)
        )
        test = test_result.scalar_one_or_none()

        answers_result = await self.db.execute(
            select(UserAnswer).where(UserAnswer.user_test_id == user_test.id)
        )
        answers = answers_result.scalars().all()

        questions_result = await self.db.execute(
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
            "passed": (
                user_test.score >= test.passing_score if test else False
            ),
            "passing_score": test.passing_score if test else 0,
            "started_at": user_test.started_at,
            "finished_at": user_test.finished_at,
            "answers": answers_data,
        }

    # ==================== RESULT (teacher, per student) ====================

    async def get_student_test_result(
        self, test_id: int, user_id: int, current_user: User
    ) -> dict:
        test_result = await self.db.execute(
            select(Test).where(
                Test.id == test_id, Test.teacher_id == current_user.id
            )
        )
        test = test_result.scalar_one_or_none()
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
            )

        user_test_result = await self.db.execute(
            select(UserTest).where(
                UserTest.test_id == test_id,
                UserTest.user_id == user_id,
                UserTest.status == "completed",
            )
        )
        user_test = user_test_result.scalar_one_or_none()
        if not user_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No attempts found",
            )

        answers_result = await self.db.execute(
            select(UserAnswer).where(UserAnswer.user_test_id == user_test.id)
        )
        answers = answers_result.scalars().all()

        questions_result = await self.db.execute(
            select(Question).where(Question.test_id == test_id)
        )
        questions = {q.id: q for q in questions_result.scalars().all()}

        real_max_score = sum(q.points for q in questions.values())

        all_question_ids = [q.id for q in questions.values()]
        options_result = await self.db.execute(
            select(AnswerOption).where(
                AnswerOption.question_id.in_(all_question_ids)
            )
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