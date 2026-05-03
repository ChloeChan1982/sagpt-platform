from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    APP_NAME: str = "SAGPT AI Backend"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./sagpt.db"
    
    # AI Provider Settings
    AI_PROVIDER: str = "siliconflow"
    
    # 直接强制从环境变量读取，不用 pydantic-settings 的自动探测
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "deepseek-ai/DeepSeek-V2.5")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
    
    USE_FREE_MODEL_TIER: bool = os.getenv("USE_FREE_MODEL_TIER", "true").lower() == "true"
    FREE_MODEL: str = os.getenv("FREE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    
    # CORS
    ALLOWED_ORIGINS: str = "https://sagpt.com,https://www.sagpt.com,http://localhost:3000"
    
    # Security
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "sagpt-dev-secret-key-change-in-production")
    
    # AI Matching
    MATCH_TOP_K: int = 5
    MATCH_MIN_SCORE: float = 0.6

@lru_cache()
def get_settings():
    return Settings()

# Provider presets
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
