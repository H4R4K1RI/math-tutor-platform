from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    student_id: int
    amount: Decimal = Field(..., gt=0)
    note: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    student_id: int
    amount: Decimal
    note: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentBalanceResponse(BaseModel):
    student_id: int
    student_name: str
    balance: Decimal
    total_paid: Decimal
    total_debt: Decimal


class PaymentHistoryResponse(BaseModel):
    payments: list[PaymentResponse]
    balance: Decimal