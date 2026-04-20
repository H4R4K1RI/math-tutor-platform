from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import os
import shutil
import uuid
from datetime import datetime

from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/upload", tags=["upload"])

# Создаём папку для загрузок, если её нет
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Загрузка файла на сервер.
    Возвращает URL для доступа к файлу.
    """
    # Проверяем тип файла
    allowed_types = [
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "text/csv",
    "application/zip"
]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Allowed: {allowed_types}"
        )
    
    # Генерируем уникальное имя файла
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Возвращаем URL
    file_url = f"/static/{unique_name}"
    
    return {
        "filename": unique_name,
        "original_name": file.filename,
        "url": file_url,
        "size": os.path.getsize(file_path),
        "content_type": file.content_type
    }

def delete_file(file_url: str):
    """Удаляет файл с диска"""
    try:
        # Из URL получаем имя файла /static/filename.jpg
        filename = file_url.replace('/static/', '')
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {e}")
