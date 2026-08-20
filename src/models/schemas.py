from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from src.config import config

class ReviewCreateRequest(BaseModel):
    sku_id: str = Field(..., json_schema_extra={"example": "MYN-TSHIRT-101"})
    user_id: str = Field(..., json_schema_extra={"example": "USR-98721"})
    rating: int = Field(..., ge=1, le=5, json_schema_extra={"example": 5})
    review_text: str = Field(..., min_length=2, json_schema_extra={"example": "Fabric is super soft and true to size! Phone me at 9876543210"})
    
    # Optional Body Metrics
    height_cm: Optional[float] = Field(None, json_schema_extra={"example": 175.0})
    weight_kg: Optional[float] = Field(None, json_schema_extra={"example": 70.0})
    body_build: Optional[str] = Field(None, json_schema_extra={"example": "REGULAR"}) # SLIM, ATHLETIC, REGULAR, HEAVY
    size_worn: Optional[str] = Field(None, json_schema_extra={"example": "M"})       # XS, S, M, L, XL, XXL
    fit_feedback: Optional[str] = Field(None, json_schema_extra={"example": "TRUE_TO_SIZE"}) # RUNS_SMALL, TRUE_TO_SIZE, RUNS_LARGE

    @field_validator('height_cm')
    @classmethod
    def validate_height(cls, v):
        if v is not None:
            if v < config.MIN_HEIGHT_CM or v > config.MAX_HEIGHT_CM:
                raise ValueError(f"Height must be between {config.MIN_HEIGHT_CM}cm and {config.MAX_HEIGHT_CM}cm")
        return v

    @field_validator('weight_kg')
    @classmethod
    def validate_weight(cls, v):
        if v is not None:
            if v < config.MIN_WEIGHT_KG or v > config.MAX_WEIGHT_KG:
                raise ValueError(f"Weight must be between {config.MIN_WEIGHT_KG}kg and {config.MAX_WEIGHT_KG}kg")
        return v

class ReviewResponse(BaseModel):
    review_id: str
    sku_id: str
    user_id: str
    rating: int
    raw_text: str
    sanitized_text: str
    detected_language: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_build: Optional[str] = None
    size_worn: Optional[str] = None
    fit_feedback: Optional[str] = None
    moderation_status: str
    pii_redacted: bool
    created_at: str

class SKUSummaryResponse(BaseModel):
    sku_id: str
    total_reviews: int
    avg_rating: float
    fit_summary: dict
    ai_summary_text: Optional[str] = None

class ModerationDecisionRequest(BaseModel):
    review_id: str
    decision: str # APPROVED, REJECTED
    reason: Optional[str] = "Manual review decision"
