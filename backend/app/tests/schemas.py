from typing import List, Optional

from pydantic import BaseModel, Field


class AnswerOptionCreate(BaseModel):
    text: str
    is_correct: bool
    order: int = 0


class QuestionCreate(BaseModel):
    text: str
    type: str
    points: float = 1.0
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


class AnswerSubmit(BaseModel):
    question_id: int
    answer: str


class TestSubmit(BaseModel):
    answers: List[AnswerSubmit]