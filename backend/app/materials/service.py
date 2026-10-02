import os
import shutil
import uuid
from datetime import datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.chat.socket import sio
from app.materials.models import FolderAccess, Material, MaterialFolder
from app.materials.schemas import (
    FolderAccessCreate,
    MaterialCreate,
    MaterialFolderCreate,
    MaterialFolderUpdate,
    MaterialUpdate,
)
from app.shared.logger import logger
from app.students.service import get_teacher_student_ids

UPLOAD_DIR = "uploads/materials"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _delete_file_by_url(url: str) -> None:
    """Удалить файл с диска по URL /static/materials/<filename>."""
    filename = url.replace("/static/materials/", "")
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")


class MaterialsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== FOLDERS ====================

    async def create_folder(
        self, data: MaterialFolderCreate, current_user: User
    ) -> MaterialFolder:
        new_folder = MaterialFolder(
            teacher_id=current_user.id,
            name=data.name,
            description=data.description,
        )

        self.db.add(new_folder)
        await self.db.commit()
        await self.db.refresh(new_folder)

        await sio.emit("materials_updated", {"action": "folder_created"})

        return new_folder

    async def get_folders(self, current_user: User) -> list[dict]:
        if current_user.role == "teacher":
            result = await self.db.execute(
                select(MaterialFolder)
                .where(MaterialFolder.teacher_id == current_user.id)
                .order_by(MaterialFolder.created_at.desc())
            )
        else:
            result = await self.db.execute(
                select(MaterialFolder)
                .join(
                    FolderAccess,
                    FolderAccess.folder_id == MaterialFolder.id,
                )
                .where(FolderAccess.student_id == current_user.id)
                .order_by(MaterialFolder.created_at.desc())
            )

        folders = result.scalars().all()

        if not folders:
            return []

        folder_ids = [f.id for f in folders]

        count_result = await self.db.execute(
            select(Material.folder_id, func.count(Material.id))
            .where(Material.folder_id.in_(folder_ids))
            .group_by(Material.folder_id)
        )
        counts = {row[0]: row[1] for row in count_result.all()}

        return [
            {
                "id": folder.id,
                "teacher_id": folder.teacher_id,
                "name": folder.name,
                "description": folder.description,
                "created_at": folder.created_at,
                "updated_at": folder.updated_at,
                "materials_count": counts.get(folder.id, 0),
            }
            for folder in folders
        ]

    async def update_folder(
        self,
        folder_id: int,
        data: MaterialFolderUpdate,
        current_user: User,
    ) -> MaterialFolder:
        result = await self.db.execute(
            select(MaterialFolder).where(
                MaterialFolder.id == folder_id,
                MaterialFolder.teacher_id == current_user.id,
            )
        )
        folder = result.scalar_one_or_none()

        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        if data.name is not None:
            folder.name = data.name
        if data.description is not None:
            folder.description = data.description

        await self.db.commit()
        await self.db.refresh(folder)

        await sio.emit("materials_updated", {"action": "folder_updated"})

        return folder

    async def delete_folder(
        self, folder_id: int, current_user: User
    ) -> dict:
        result = await self.db.execute(
            select(MaterialFolder).where(
                MaterialFolder.id == folder_id,
                MaterialFolder.teacher_id == current_user.id,
            )
        )
        folder = result.scalar_one_or_none()

        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        materials_result = await self.db.execute(
            select(Material).where(Material.folder_id == folder_id)
        )
        materials = materials_result.scalars().all()

        for material in materials:
            if material.type == "file" and material.url:
                _delete_file_by_url(material.url)

        await self.db.delete(folder)
        await self.db.commit()

        await sio.emit("materials_updated", {"action": "folder_deleted"})

        return {"message": "Folder deleted"}

    # ==================== ACCESS ====================

    async def set_folder_access(
        self,
        folder_id: int,
        data: FolderAccessCreate,
        current_user: User,
    ) -> dict:
        folder_result = await self.db.execute(
            select(MaterialFolder).where(
                MaterialFolder.id == folder_id,
                MaterialFolder.teacher_id == current_user.id,
            )
        )
        folder = folder_result.scalar_one_or_none()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        teacher_student_ids = await get_teacher_student_ids(
            self.db, current_user.id
        )

        invalid_ids = set(data.student_ids) - teacher_student_ids
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have access to students: {sorted(invalid_ids)}",
            )

        await self.db.execute(
            delete(FolderAccess).where(FolderAccess.folder_id == folder_id)
        )

        for student_id in data.student_ids:
            self.db.add(
                FolderAccess(folder_id=folder_id, student_id=student_id)
            )

        await self.db.commit()

        await sio.emit("materials_updated", {"action": "access_updated"})

        return {"message": "Access updated"}

    async def get_folder_access(
        self, folder_id: int, current_user: User
    ) -> list[dict]:
        folder_result = await self.db.execute(
            select(MaterialFolder).where(
                MaterialFolder.id == folder_id,
                MaterialFolder.teacher_id == current_user.id,
            )
        )
        folder = folder_result.scalar_one_or_none()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        result = await self.db.execute(
            select(FolderAccess).where(FolderAccess.folder_id == folder_id)
        )
        accesses = result.scalars().all()

        if not accesses:
            return []

        student_ids = [a.student_id for a in accesses]
        students_result = await self.db.execute(
            select(User).where(User.id.in_(student_ids))
        )
        students_map = {u.id: u for u in students_result.scalars().all()}

        return [
            {
                "id": s.id,
                "name": s.full_name,
                "email": s.email,
            }
            for s in students_map.values()
        ]

    # ==================== MATERIALS ====================

    async def upload_material_file(
        self, file: UploadFile, current_user: User
    ) -> dict:
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "video/mp4",
            "video/webm",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed",
            )

        ext = os.path.splitext(file.filename)[1]
        unique_name = (
            f"{current_user.id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
            f"{uuid.uuid4().hex[:8]}{ext}"
        )
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}",
            )

        file_url = f"/static/materials/{unique_name}"
        file_size = os.path.getsize(file_path)

        return {
            "url": file_url,
            "file_name": file.filename,
            "file_size": file_size,
        }

    async def create_material(
        self, data: MaterialCreate, current_user: User
    ) -> Material:
        folder_result = await self.db.execute(
            select(MaterialFolder).where(
                MaterialFolder.id == data.folder_id,
                MaterialFolder.teacher_id == current_user.id,
            )
        )
        folder = folder_result.scalar_one_or_none()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        new_material = Material(
            folder_id=data.folder_id,
            teacher_id=current_user.id,
            title=data.title,
            description=data.description,
            type=data.type,
            url=data.url,
            file_name=data.file_name,
            file_size=data.file_size,
            order=data.order,
        )

        self.db.add(new_material)
        await self.db.commit()
        await self.db.refresh(new_material)

        await sio.emit("materials_updated", {"action": "material_created"})

        return new_material

    async def get_folder_materials(
        self, folder_id: int, current_user: User
    ) -> list[Material]:
        if current_user.role == "teacher":
            folder_result = await self.db.execute(
                select(MaterialFolder).where(
                    MaterialFolder.id == folder_id,
                    MaterialFolder.teacher_id == current_user.id,
                )
            )
            if not folder_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )
        else:
            access_result = await self.db.execute(
                select(FolderAccess).where(
                    FolderAccess.folder_id == folder_id,
                    FolderAccess.student_id == current_user.id,
                )
            )
            if not access_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )

        result = await self.db.execute(
            select(Material)
            .where(Material.folder_id == folder_id)
            .order_by(Material.order)
        )
        return list(result.scalars().all())

    async def update_material(
        self,
        material_id: int,
        data: MaterialUpdate,
        current_user: User,
    ) -> Material:
        result = await self.db.execute(
            select(Material).where(
                Material.id == material_id,
                Material.teacher_id == current_user.id,
            )
        )
        material = result.scalar_one_or_none()

        if not material:
            raise HTTPException(status_code=404, detail="Material not found")

        if data.title is not None:
            material.title = data.title
        if data.description is not None:
            material.description = data.description
        if data.order is not None:
            material.order = data.order

        await self.db.commit()
        await self.db.refresh(material)

        await sio.emit("materials_updated", {"action": "material_updated"})

        return material

    async def delete_material(
        self, material_id: int, current_user: User
    ) -> dict:
        result = await self.db.execute(
            select(Material).where(
                Material.id == material_id,
                Material.teacher_id == current_user.id,
            )
        )
        material = result.scalar_one_or_none()

        if not material:
            raise HTTPException(status_code=404, detail="Material not found")

        if material.type == "file" and material.url:
            _delete_file_by_url(material.url)

        await self.db.delete(material)
        await self.db.commit()

        await sio.emit("materials_updated", {"action": "material_deleted"})

        return {"message": "Material deleted"}