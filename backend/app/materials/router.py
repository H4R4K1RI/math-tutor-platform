from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_teacher, get_current_user
from app.auth.models import User
from app.materials.schemas import (
    FolderAccessCreate,
    MaterialCreate,
    MaterialFolderCreate,
    MaterialFolderResponse,
    MaterialFolderUpdate,
    MaterialResponse,
    MaterialUpdate,
)
from app.materials.service import MaterialsService
from app.shared.db import get_db

router = APIRouter(prefix="/materials", tags=["materials"])


# ==================== FOLDERS ====================


@router.post("/folders", response_model=MaterialFolderResponse)
async def create_folder(
    folder_data: MaterialFolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Создать папку."""
    service = MaterialsService(db)
    return await service.create_folder(folder_data, current_user)


@router.get("/folders", response_model=List[MaterialFolderResponse])
async def get_folders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список папок."""
    service = MaterialsService(db)
    return await service.get_folders(current_user)


@router.put("/folders/{folder_id}", response_model=MaterialFolderResponse)
async def update_folder(
    folder_id: int,
    folder_data: MaterialFolderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновить папку."""
    service = MaterialsService(db)
    return await service.update_folder(folder_id, folder_data, current_user)


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удалить папку со всеми материалами."""
    service = MaterialsService(db)
    return await service.delete_folder(folder_id, current_user)


# ==================== ACCESS ====================


@router.post("/folders/{folder_id}/access")
async def set_folder_access(
    folder_id: int,
    access_data: FolderAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Установить доступ к папке."""
    service = MaterialsService(db)
    return await service.set_folder_access(
        folder_id, access_data, current_user
    )


@router.get("/folders/{folder_id}/access")
async def get_folder_access(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Список учеников с доступом к папке."""
    service = MaterialsService(db)
    return await service.get_folder_access(folder_id, current_user)


# ==================== MATERIALS ====================


@router.post("/upload")
async def upload_material_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Загрузить файл материала."""
    service = MaterialsService(db)
    return await service.upload_material_file(file, current_user)


@router.post("/items", response_model=MaterialResponse)
async def create_material(
    material_data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Создать материал."""
    service = MaterialsService(db)
    return await service.create_material(material_data, current_user)


@router.get(
    "/folders/{folder_id}/items", response_model=List[MaterialResponse]
)
async def get_folder_materials(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список материалов в папке."""
    service = MaterialsService(db)
    return await service.get_folder_materials(folder_id, current_user)


@router.put("/items/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: int,
    material_data: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Обновить материал."""
    service = MaterialsService(db)
    return await service.update_material(
        material_id, material_data, current_user
    )


@router.delete("/items/{material_id}")
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """Удалить материал."""
    service = MaterialsService(db)
    return await service.delete_material(material_id, current_user)