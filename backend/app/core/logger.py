import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.core.config import settings

# Определяем корневую папку проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Папка для логов (сначала пробуем /app/logs для Docker, иначе локальную)
LOG_DIR = Path("/app/logs") if Path("/app").exists() else BASE_DIR / "logs"

try:
    LOG_DIR.mkdir(exist_ok=True)
except (PermissionError, FileNotFoundError):
    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

# Уровень логирования зависит от DEBUG
LOG_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO

# Сколько дней хранить старые логи
LOG_BACKUP_DAYS = 30


def setup_logger(name: str = "math_tutor") -> logging.Logger:
    """Настройка логгера с ротацией по дням.

    - В dev (DEBUG=True) — уровень DEBUG.
    - В проде (DEBUG=False) — уровень INFO.
    - Файлы ротируются каждый день, хранятся 30 дней, сжимаются в gzip.
    """

    logger = logging.getLogger(name)

    # Защита от двойного добавления хендлеров
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)

    # Файловый обработчик с ротацией
    try:
        file_handler = TimedRotatingFileHandler(
            LOG_FILE,
            when="midnight",       # ротация в полночь
            interval=1,            # каждый 1 день
            backupCount=LOG_BACKUP_DAYS,  # хранить 30 дней
            encoding="utf-8",
            utc=True,              # UTC-время для ротации
        )
        file_handler.suffix = "%Y-%m-%d"  # суффикс для старых файлов
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")

    logger.addHandler(console_handler)

    return logger


# Глобальный логгер
logger = setup_logger()