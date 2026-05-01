from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "SAGPT AI Backend"
    DEBUG: bool = True
    
    # Database - supports any PostgreSQL (Render, Neon, Supabase, local)
    DATABASE_URL: str = "postgresql://sagpt:sagpt123@db:5432/sagpt"
    
    # AI Provider Settings
    AI_PROVIDER: str = "siliconflow"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.siliconflow.cn/v1"
    OPENAI_MODEL: str = "deepseek-ai/DeepSeek-V2.5"
    EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    
    # Cost optimization
    USE_FREE_MODEL_TIER: bool = True
    FREE_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    
    # CORS - Readdy domains included
    ALLOWED_ORIGINS: str = "https://sagpt.com,https://www.sagpt.com,http://localhost:3000,http://localhost:5173,https://readdy.ai"
    
    # Security
    API_SECRET_KEY: str = "sagpt-dev-secret-key-change-in-production"
    
    # AI Matching
    MATCH_TOP_K: int = 5
    MATCH_MIN_SCORE: float = 0.6
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

# Provider presets for easy configuration
PROVIDER_PRESETS = {
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "chat_model": "deepseek-ai/DeepSeek-V2.5",
        "embedding_model": "BAAI/bge-large-zh-v1.5",
        "free_model": "Qwen/Qwen2.5-7B-Instruct",
        "use_free_tier": True,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "chat_model": "deepseek-chat",
        "embedding_model": "text-embedding-3-large",
        "free_model": None,
        "use_free_tier": False,
    },
    "aliyun": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "chat_model": "qwen-plus",
        "embedding_model": "text-embedding-v3",
        "free_model": None,
        "use_free_tier": False,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "chat_model": "gpt-4o",
        "embedding_model": "text-embedding-3-large",
        "free_model": None,
        "use_free_tier": False,
    },
}