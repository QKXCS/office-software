from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = {"env_file": BASE_DIR / ".env", "extra": "ignore"}

    # 环境
    env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # 数据库 (默认 SQLite，零外部依赖)
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/bangong.db"
    database_url_sync: str = f"sqlite:///{BASE_DIR}/bangong.db"

    # Qdrant (默认本地文件模式，零外部依赖)
    qdrant_url: str = ""
    qdrant_local_path: str = str(BASE_DIR / "qdrant_data")
    qdrant_collection: str = "bangong_docs"

    # Redis (可选，不配则用内存缓存)
    redis_url: str = ""

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    doubao_api_key: str = ""
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    default_llm_provider: str = "doubao"
    default_llm_model: str = "doubao-seed-2-0-lite-260428"
    vision_model: str = "doubao-seed-2-0-lite-260428"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # ASR / TTS
    asr_provider: str = "whisper"
    asr_model: str = "large-v3-turbo"
    tts_provider: str = "edge"

    # 文件存储
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # JWT
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 1440

    # LangFuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def use_local_qdrant(self) -> bool:
        return not self.qdrant_url


settings = Settings()
