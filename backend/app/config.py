from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Config(BaseSettings):
    # Mistral AI
    MISTRAL_API_KEY: str = Field("", env="MISTRAL_API_KEY")
    MISTRAL_MODEL: str = Field("mistral-small-latest", env="MISTRAL_MODEL")

    # Базы данных
    DATABASE_PATH: str = Field("../data/agents.db", env="DATABASE_PATH")
    CHROMA_PATH: str = Field("../data/chroma", env="CHROMA_PATH")

    # Логирование
    LOG_FILE: str = Field("../logs/backend.log", env="LOG_FILE")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")  # DEBUG, INFO, WARNING, ERROR

    class Config:
        env_file = ".env"
        case_sensitive = True


config = Config()

# Создаем папку для логов если её нет
log_dir = os.path.dirname(config.LOG_FILE)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

print(f"🔧 Конфигурация загружена:")
print(f"  📁 DB: {os.path.abspath(config.DATABASE_PATH)}")
print(f"  📁 Chroma: {os.path.abspath(config.CHROMA_PATH)}")
print(f"  📁 Логи: {os.path.abspath(config.LOG_FILE)}")