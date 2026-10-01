"""add check constraints

Revision ID: e293933d7c5b
Revises: f1abb6597b1e
Create Date: 2026-10-01 11:59:20.637222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e293933d7c5b'
down_revision: Union[str, None] = 'f1abb6597b1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User.role
    op.create_check_constraint(
        "ck_user_role",
        "users",
        "role IN ('teacher', 'student')",
    )

    # Submission.status
    op.create_check_constraint(
        "ck_submission_status",
        "submissions",
        "status IN ('pending', 'approved', 'rejected')",
    )

    # Lesson.status
    op.create_check_constraint(
        "ck_lesson_status",
        "lessons",
        "status IN ('scheduled', 'completed', 'cancelled')",
    )

    # Lesson.price
    op.create_check_constraint(
        "ck_lesson_price",
        "lessons",
        "price >= 0",
    )

    # LessonRequest.status
    op.create_check_constraint(
        "ck_lesson_request_status",
        "lesson_requests",
        "status IN ('pending', 'approved', 'rejected')",
    )

    # TutoringRequest.status
    op.create_check_constraint(
        "ck_tutoring_request_status",
        "tutoring_requests",
        "status IN ('pending', 'approved', 'rejected')",
    )

    # Review.rating
    op.create_check_constraint(
        "ck_review_rating",
        "reviews",
        "rating >= 1 AND rating <= 5",
    )

    # Test.passing_score
    op.create_check_constraint(
        "ck_test_passing_score",
        "tests",
        "passing_score >= 0 AND passing_score <= 100",
    )

    # Test.attempts
    op.create_check_constraint(
        "ck_test_attempts",
        "tests",
        "attempts >= 1",
    )

    # UserTest.status
    op.create_check_constraint(
        "ck_user_test_status",
        "user_tests",
        "status IN ('in_progress', 'completed')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_test_status", "user_tests", type_="check")
    op.drop_constraint("ck_test_attempts", "tests", type_="check")
    op.drop_constraint("ck_test_passing_score", "tests", type_="check")
    op.drop_constraint("ck_review_rating", "reviews", type_="check")
    op.drop_constraint("ck_tutoring_request_status", "tutoring_requests", type_="check")
    op.drop_constraint("ck_lesson_request_status", "lesson_requests", type_="check")
    op.drop_constraint("ck_lesson_price", "lessons", type_="check")
    op.drop_constraint("ck_lesson_status", "lessons", type_="check")
    op.drop_constraint("ck_submission_status", "submissions", type_="check")
    op.drop_constraint("ck_user_role", "users", type_="check")