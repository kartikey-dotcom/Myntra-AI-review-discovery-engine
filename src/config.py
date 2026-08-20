import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Myntra AI Review Engine")
    VERSION: str = "1.0.0"
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # LLM Settings (Gemini AI)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    
    # Database
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")
    DB_PATH: str = os.getenv("DB_PATH", "myntra_reviews.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_TTL_SECONDS: int = int(os.getenv("REDIS_TTL_SECONDS", 3600))
    
    # Validation Boundaries (as specified in edge-cases.md)
    MIN_HEIGHT_CM: float = float(os.getenv("MIN_HEIGHT_CM", 120.0))  # ~3'11"
    MAX_HEIGHT_CM: float = float(os.getenv("MAX_HEIGHT_CM", 220.0))  # ~7'2"
    MIN_WEIGHT_KG: float = float(os.getenv("MIN_WEIGHT_KG", 30.0))   # ~66 lbs
    MAX_WEIGHT_KG: float = float(os.getenv("MAX_WEIGHT_KG", 200.0))  # ~440 lbs
    
    # Event Queue
    KAFKA_RAW_TOPIC: str = os.getenv("KAFKA_RAW_TOPIC", "kafka.reviews.raw")
    KAFKA_MODERATED_TOPIC: str = os.getenv("KAFKA_MODERATED_TOPIC", "kafka.reviews.moderated")

config = Config()
