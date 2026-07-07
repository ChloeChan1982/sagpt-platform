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
    # Zhipu AI Configuration (NEW - Default LLM Provider)
    ZHIPU_API_KEY: str = os.getenv("ZHIPU_API_KEY", "")
    ZHIPU_CHAT_MODEL: str = os.getenv("ZHIPU_CHAT_MODEL", "glm-4-flash")
    ZHIPU_EMBEDDING_MODEL: str = os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-2")

    # OpenAI Configuration (fallback for complex English)
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

    # WeChat Mini Program
    WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "")
    WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "")
    WECHAT_CONTACTED_TEMPLATE_ID: str = os.getenv("WECHAT_CONTACTED_TEMPLATE_ID", "")
    WECHAT_COMPLETED_TEMPLATE_ID: str = os.getenv("WECHAT_COMPLETED_TEMPLATE_ID", "")
    MINI_SESSION_DAYS: int = int(os.getenv("MINI_SESSION_DAYS", "30"))

    # Attachment Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_ATTACHMENT_BYTES: int = 20 * 1024 * 1024
    MAX_ATTACHMENTS_PER_DEMAND: int = 3

    # Gmail Configuration (NEW - Email Automation)
    GMAIL_SERVICE_ACCOUNT_JSON: str = os.getenv("GMAIL_SERVICE_ACCOUNT_JSON", "")
    GMAIL_SENDER_EMAIL: str = os.getenv("GMAIL_SENDER_EMAIL", "sagpt@sagpt.com")
    GMAIL_SENDER_NAME: str = os.getenv("GMAIL_SENDER_NAME", "SAGPT")

    # Google Sheets Configuration (NEW - CRM)
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    GOOGLE_CREDENTIALS: str = os.getenv("GOOGLE_CREDENTIALS", "")  # Base64 encoded

@lru_cache()
def get_settings():
    return Settings()

# Provider presets
PROVIDER_PRESETS = {
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "chat_model": "glm-4-flash",
        "embedding_model": "embedding-2",
        "free_model": "glm-4-flash",
        "use_free_tier": True,
        "api_key_env": "ZHIPU_API_KEY",
    },
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
