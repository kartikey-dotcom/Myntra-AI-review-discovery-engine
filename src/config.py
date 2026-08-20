import os

# Try loading from dotenv if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try loading from streamlit secrets if running under Streamlit Cloud
def get_secret(key: str, default: str = "") -> str:
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default

class Config:
    PROJECT_NAME: str = get_secret("PROJECT_NAME", "Myntra AI Review Engine")
    VERSION: str = "1.0.0"
    API_PREFIX: str = get_secret("API_PREFIX", "/api/v1")
    ENVIRONMENT: str = get_secret("ENVIRONMENT", "development")
    
    # LLM Settings (Gemini AI)
    LLM_PROVIDER: str = get_secret("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = get_secret("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = get_secret("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    
    # Database
    DB_TYPE: str = get_secret("DB_TYPE", "sqlite")
    DB_PATH: str = get_secret("DB_PATH", "myntra_reviews.db")
    DATABASE_URL: str = get_secret("DATABASE_URL", "")
    
    # Redis
    REDIS_HOST: str = get_secret("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(get_secret("REDIS_PORT", "6379"))
    REDIS_TTL_SECONDS: int = int(get_secret("REDIS_TTL_SECONDS", "3600"))
    
    # Validation Boundaries (as specified in edge-cases.md)
    MIN_HEIGHT_CM: float = float(get_secret("MIN_HEIGHT_CM", "120.0"))  # ~3'11"
    MAX_HEIGHT_CM: float = float(get_secret("MAX_HEIGHT_CM", "220.0"))  # ~7'2"
    MIN_WEIGHT_KG: float = float(get_secret("MIN_WEIGHT_KG", "30.0"))   # ~66 lbs
    MAX_WEIGHT_KG: float = float(get_secret("MAX_WEIGHT_KG", "200.0"))  # ~440 lbs
    
    # Event Queue
    KAFKA_RAW_TOPIC: str = get_secret("KAFKA_RAW_TOPIC", "kafka.reviews.raw")
    KAFKA_MODERATED_TOPIC: str = get_secret("KAFKA_MODERATED_TOPIC", "kafka.reviews.moderated")

config = Config()
