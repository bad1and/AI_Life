"""
Настройка логирования для бэкенда
Логи пишутся и в консоль, и в файл
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from .config import config

# Создаем папку для логов
log_file = Path(config.LOG_FILE)
log_file.parent.mkdir(parents=True, exist_ok=True)

# Настройка формата логов
log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# Настройка корневого логгера
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format=log_format,
    datefmt=date_format,
    handlers=[
        # В файл
        logging.FileHandler(log_file, encoding='utf-8'),
        # В консоль
        logging.StreamHandler(sys.stdout)
    ]
)


# Создаем логгеры для разных модулей
def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер для модуля

    Args:
        name: имя модуля (обычно __name__)

    Returns:
        logging.Logger: настроенный логгер
    """
    return logging.getLogger(name)


# Логгер для основных событий
main_logger = get_logger("main")

# Логгер для API запросов
api_logger = get_logger("api")

# Логгер для агентов
agents_logger = get_logger("agents")

# Логгер для Mistral AI
mistral_logger = get_logger("mistral")

# Логгер для базы данных
db_logger = get_logger("database")

# Логгер для памяти
memory_logger = get_logger("memory")


def log_request(endpoint: str, method: str, params: dict = None):
    """Логирование HTTP запроса"""
    api_logger.info(f"➡️ {method} {endpoint} | Параметры: {params}")


def log_response(endpoint: str, status: int, duration: float):
    """Логирование HTTP ответа"""
    api_logger.info(f"⬅️ {endpoint} | Статус: {status} | Время: {duration:.3f}с")


def log_error(error: Exception, context: str = ""):
    """Логирование ошибки"""
    main_logger.error(f"❌ Ошибка: {error} | Контекст: {context}", exc_info=True)

# Пример использования в других модулях:
# from app.logger import get_logger
# logger = get_logger(__name__)
# logger.info("Сообщение")
# logger.error("Ошибка")