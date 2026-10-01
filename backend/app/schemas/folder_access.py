from pydantic import BaseModel
from typing import List


class FolderAccessCreate(BaseModel):
    student_ids: List[int]