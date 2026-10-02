import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.shared.config import settings

# Определяем корневую папку проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Папка для логов
LOG_DIR = Path("/app/logs") if Path("/app").exists() else BASE_DIR / "logs"

try:
    LOG_DIR.mkdir(exist_ok=True)
except (PermissionError, FileNotFoundError):
    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

LOG_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO
LOG_BACKUP_DAYS = 30


def setup_logger(name: str = "math_tutor") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)

    try:
        file_handler = TimedRotatingFileHandler(
            LOG_FILE,
            when="midnight",
            interval=1,
            backupCount=LOG_BACKUP_DAYS,
            encoding="utf-8",
            utc=True,
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")

    logger.addHandler(console_handler)

    return logger


logger = setup_logger()