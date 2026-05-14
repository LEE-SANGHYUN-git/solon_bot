from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # 앱 기본 정보
    APP_NAME: str = "Solon Text Summarizer"
    APP_VERSION: str = "1.0.0"

    # Gemini API
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # 요약 설정 기본값
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_MAX_LENGTH: int = 300  # 요약 결과 최대 글자 수
    DEFAULT_STYLE: str = "bullet"  # bullet | paragraph | tldr

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
