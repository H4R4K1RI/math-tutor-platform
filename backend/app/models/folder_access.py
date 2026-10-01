from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.db.database import Base


class FolderAccess(Base):
    __tablename__ = "folder_access"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(
        Integer,
        ForeignKey("material_folders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint("folder_id", "student_id", name="uq_folder_access"),
    )