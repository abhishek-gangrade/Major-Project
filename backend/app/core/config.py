import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
_DEFAULT_DB_PATH = os.path.join(_ROOT_DIR, "adaptiveprep.db")


class Settings(BaseSettings):
    PROJECT_NAME: str = "AdaptivePrep"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = "adaptiveprep-super-secret-development-key-change-in-prod-xyz123"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database: Anchored to project root for consistent access across CLI, Alembic, and tests
    DATABASE_URL: str = f"sqlite:///{_DEFAULT_DB_PATH}"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Adaptive Recommendation Engine Weights (S = 100 * (0.45A + 0.25R + 0.20D + 0.10E))
    WEIGHT_ACCURACY: float = 0.45
    WEIGHT_RECENCY: float = 0.25
    WEIGHT_DIFFICULTY: float = 0.20
    WEIGHT_EFFICIENCY: float = 0.10
    
    # Difficulty Selection Thresholds
    THRESHOLD_EASY_UPPER: float = 40.0      # S < 40 -> Easy
    THRESHOLD_MEDIUM_UPPER: float = 70.0    # 40 <= S < 70 -> Medium, S >= 70 -> Hard
    
    # Window and smoothing parameters
    RECENCY_WINDOW_SIZE: int = 5
    MIN_OBSERVATION_THRESHOLD: int = 3
    ALGORITHM_VERSION: str = "v1.0.0-multi-factor"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

