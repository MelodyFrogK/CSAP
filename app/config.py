"""환경설정. .env 또는 환경변수에서 로드한다."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CSAP_",
        extra="ignore",
    )

    # LLM 공급자: anthropic | openai | echo
    llm_provider: str = "echo"

    # Anthropic
    anthropic_model: str = "claude-sonnet-4-6"
    # OpenAI
    openai_model: str = "gpt-4o"

    # Claude Code CLI 공급자(별도 API 키 없이 Claude Code 인증 재사용)
    claude_cli_binary: str = "claude"
    claude_cli_model: str = ""  # 빈 값이면 Claude Code 기본 모델 사용
    claude_cli_timeout: int = 180

    # 검색/청크 설정
    top_k: int = 6
    chunk_size: int = 1200
    chunk_overlap: int = 200
    concurrency: int = 4

    # 기본 명세서 템플릿 경로(미지정 시 샘플 사용)
    default_template: str = str(DATA_DIR / "sample_csap_template.xlsx")


@lru_cache
def get_settings() -> Settings:
    for d in (DATA_DIR, UPLOAD_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)
    return Settings()
