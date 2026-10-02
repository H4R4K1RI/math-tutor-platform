import os

from app.shared.logger import logger

UPLOAD_DIR = "uploads"


def delete_file(file_url: str) -> None:
    """Удалить файл с диска по URL /static/<filename>."""
    try:
        filename = file_url.replace("/static/", "")
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")