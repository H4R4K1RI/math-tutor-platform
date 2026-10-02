import os
import shutil
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.shared.db import get_db
from app.models.folder_access import FolderAccess
from app.models.material import Material
from app.models.material_folder import MaterialFolder
from app.auth.models import User
from app.schemas.folder_access import FolderAccessCreate
from app.schemas.material import MaterialCreate, MaterialResponse, MaterialUpdate
from app.schemas.material_folder import (
    MaterialFolderCreate,
    MaterialFolderResponse,
    MaterialFolderUpdate,
)
from app.socket_manager import sio

router = APIRouter(prefix="/materials", tags=["materials"])

UPLOAD_DIR = "uploads/materials"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ========== ПАПКИ ==========


@router.post("/folders", response_model=MaterialFolderResponse)
async def create_folder(
    folder_data: MaterialFolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    new_folder = MaterialFolder(
        teacher_id=current_user.id,
        name=folder_data.name,
        description=folder_data.description,
    )

    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)

    await sio.emit("materials_updated", {"action": "folder_created"})

    return new_folder


@router.get("/folders", response_model=List[MaterialFolderResponse])
async def get_folders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить папки (оптимизировано)"""

    if current_user.role == "teacher":
        result = await db.execute(
            select(MaterialFolder)
            .where(MaterialFolder.teacher_id == current_user.id)
            .order_by(MaterialFolder.created_at.desc())
        )
    else:
        result = await db.execute(
            select(MaterialFolder)
            .join(FolderAccess, FolderAccess.folder_id == MaterialFolder.id)
            .where(FolderAccess.student_id == current_user.id)
            .order_by(MaterialFolder.created_at.desc())
        )

    folders = result.scalars().all()

    if not folders:
        return []

    folder_ids = [f.id for f in folders]

    # Количество материалов — одним запросом
    count_result = await db.execute(
        select(Material.folder_id, func.count(Material.id))
        .where(Material.folder_id.in_(folder_ids))
        .group_by(Material.folder_id)
    )
    counts = {row[0]: row[1] for row in count_result.all()}

    response = []
    for folder in folders:
        response.append(
            {
                "id": folder.id,
                "teacher_id": folder.teacher_id,
                "name": folder.name,
                "description": folder.description,
                "created_at": folder.created_at,
                "updated_at": folder.updated_at,
                "materials_count": counts.get(folder.id, 0),
            }
        )

    return response


@router.put("/folders/{folder_id}", response_model=MaterialFolderResponse)
async def update_folder(
    folder_id: int,
    folder_data: MaterialFolderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    result = await db.execute(
        select(MaterialFolder).where(
            MaterialFolder.id == folder_id,
            MaterialFolder.teacher_id == current_user.id,
        )
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if folder_data.name is not None:
        folder.name = folder_data.name
    if folder_data.description is not None:
        folder.description = folder_data.description

    await db.commit()
    await db.refresh(folder)

    await sio.emit("materials_updated", {"action": "folder_updated"})

    return folder


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    result = await db.execute(
        select(MaterialFolder).where(
            MaterialFolder.id == folder_id,
            MaterialFolder.teacher_id == current_user.id,
        )
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    materials_result = await db.execute(
        select(Material).where(Material.folder_id == folder_id)
    )
    materials = materials_result.scalars().all()

    for material in materials:
        if material.type == "file" and material.url:
            filename = material.url.replace("/static/materials/", "")
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

    await db.delete(folder)
    await db.commit()

    await sio.emit("materials_updated", {"action": "folder_deleted"})

    return {"message": "Folder deleted"}


# ========== ДОСТУП ==========


@router.post("/folders/{folder_id}/access")
async def set_folder_access(
    folder_id: int,
    access_data: FolderAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    folder_result = await db.execute(
        select(MaterialFolder).where(
            MaterialFolder.id == folder_id,
            MaterialFolder.teacher_id == current_user.id,
        )
    )
    folder = folder_result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    from app.api.students import get_teacher_student_ids

    teacher_student_ids = await get_teacher_student_ids(db, current_user.id)

    invalid_ids = set(access_data.student_ids) - teacher_student_ids
    if invalid_ids:
        raise HTTPException(
            status_code=403,
            detail=f"You don't have access to students: {sorted(invalid_ids)}",
        )

    await db.execute(delete(FolderAccess).where(FolderAccess.folder_id == folder_id))

    for student_id in access_data.student_ids:
        db.add(FolderAccess(folder_id=folder_id, student_id=student_id))

    await db.commit()

    await sio.emit("materials_updated", {"action": "access_updated"})

    return {"message": "Access updated"}


@router.get("/folders/{folder_id}/access")
async def get_folder_access(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Получить список учеников с доступом к папке (оптимизировано)"""

    folder_result = await db.execute(
        select(MaterialFolder).where(
            MaterialFolder.id == folder_id,
            MaterialFolder.teacher_id == current_user.id,
        )
    )
    folder = folder_result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    result = await db.execute(
        select(FolderAccess).where(FolderAccess.folder_id == folder_id)
    )
    accesses = result.scalars().all()

    if not accesses:
        return []

    student_ids = [a.student_id for a in accesses]
    students_result = await db.execute(select(User).where(User.id.in_(student_ids)))
    students_map = {u.id: u for u in students_result.scalars().all()}

    return [
        {
            "id": s.id,
            "name": s.full_name,
            "email": s.email,
        }
        for s in students_map.values()
    ]


# ========== МАТЕРИАЛЫ ==========


@router.post("/upload")
async def upload_material_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
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
            status_code=400, detail=f"File type {file.content_type} not allowed"
        )

    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    file_url = f"/static/materials/{unique_name}"
    file_size = os.path.getsize(file_path)

    return {"url": file_url, "file_name": file.filename, "file_size": file_size}


@router.post("/items", response_model=MaterialResponse)
async def create_material(
    material_data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    folder_result = await db.execute(
        select(MaterialFolder).where(
            MaterialFolder.id == material_data.folder_id,
            MaterialFolder.teacher_id == current_user.id,
        )
    )
    folder = folder_result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    new_material = Material(
        folder_id=material_data.folder_id,
        teacher_id=current_user.id,
        title=material_data.title,
        description=material_data.description,
        type=material_data.type,
        url=material_data.url,
        file_name=material_data.file_name,
        file_size=material_data.file_size,
        order=material_data.order,
    )

    db.add(new_material)
    await db.commit()
    await db.refresh(new_material)

    await sio.emit("materials_updated", {"action": "material_created"})

    return new_material


@router.get("/folders/{folder_id}/items", response_model=List[MaterialResponse])
async def get_folder_materials(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "teacher":
        folder_result = await db.execute(
            select(MaterialFolder).where(
                MaterialFolder.id == folder_id,
                MaterialFolder.teacher_id == current_user.id,
            )
        )
        if not folder_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        access_result = await db.execute(
            select(FolderAccess).where(
                FolderAccess.folder_id == folder_id,
                FolderAccess.student_id == current_user.id,
            )
        )
        if not access_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Material).where(Material.folder_id == folder_id).order_by(Material.order)
    )
    materials = result.scalars().all()

    return materials


@router.put("/items/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: int,
    material_data: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Material).where(
            Material.id == material_id, Material.teacher_id == current_user.id
        )
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if material_data.title is not None:
        material.title = material_data.title
    if material_data.description is not None:
        material.description = material_data.description
    if material_data.order is not None:
        material.order = material_data.order

    await db.commit()
    await db.refresh(material)

    await sio.emit("materials_updated", {"action": "material_updated"})

    return material


@router.delete("/items/{material_id}")
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Material).where(
            Material.id == material_id, Material.teacher_id == current_user.id
        )
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if material.type == "file" and material.url:
        file_path = material.url.replace("/static/materials/", "")
        full_path = os.path.join(UPLOAD_DIR, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    await db.delete(material)
    await db.commit()

    await sio.emit("materials_updated", {"action": "material_deleted"})

    return {"message": "Material deleted"}