import asyncio
from app.db.database import engine, Base
from app.models.user import User
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.chat import Chat, Message
from app.models.student_progress import StudentProgress

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created successfully")

if __name__ == "__main__":
    asyncio.run(create_tables())