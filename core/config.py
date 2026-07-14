"""
app/core/config.py

Central configuration object. Everything that varies between dev/staging/
production (DB URL, secrets, model names, file paths) lives here and is
loaded once from environment variables / .env.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./tridomain.db"

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    # ── JWT ─────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-to-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Groq ────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── RAG ─────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = ".rag/index_store/faiss.index"
    FAISS_DOCS_PATH: str = ".rag/index_store/docs.json"
    HF_TOKEN: str = ""

    # ── Reports ─────────────────────────────────────────────────
    REPORTS_DIR: str = "./reports"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
