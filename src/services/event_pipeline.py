import uuid
import logging
from typing import Dict, Any
from src.services.pii_scrubber import PIIScrubber, LanguageDetector
from src.services.moderation_rules import ModerationRuleEngine
from src.services.absa_engine import ABSAEngine
from src.services.fit_intelligence import FitIntelligenceEngine
from src.services.verification_engine import VerificationEngine
from src.db.database import save_review, save_conversion_claims, push_to_moderation_queue

logger = logging.getLogger(__name__)

class ReviewEventPipeline:
    """
    Event processing pipeline (Expanded Wishlist Conversion Taxonomy & Verification):
    1. PII Scrubbing
    2. Language Identification
    3. Synthetic Text & Behavioral Trust Evaluation
    4. ABSA Taxonomy Extraction (7 Wishlist Conversion Categories + Quality Aspects)
    5. Fit Intelligence (Body Metric NER & Fit Delta Inference)
    6. Stage 3 Adversarial Verification Pass (Verified Findings vs Rejected Log)
    7. Database Persistence
    """
    
    @classmethod
    def process_review_submission(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        review_id = payload.get("review_id") or f"rev_{uuid.uuid4().hex[:10]}"
        raw_text = payload["review_text"]
        
        # 1. PII Scrubbing
        sanitized_text, pii_redacted = PIIScrubber.sanitize(raw_text)
        
        # 2. Language Detection
        detected_lang = LanguageDetector.detect(sanitized_text)
        
        # 3. Composite Moderation Evaluation
        mod_status, synth_score, reason, metrics = ModerationRuleEngine.evaluate(payload)
        
        # 4. Expanded Taxonomy ABSA Extraction
        extracted_aspects = ABSAEngine.extract_aspects(sanitized_text)
        
        # 5. Body Metric NER & Fit Delta Inference
        body_metrics = FitIntelligenceEngine.extract_body_metrics(sanitized_text)
        fit_feedback = payload.get("fit_feedback") or FitIntelligenceEngine.classify_fit_delta(sanitized_text)
        
        height_cm = payload.get("height_cm") or body_metrics["extracted_height_cm"]
        weight_kg = payload.get("weight_kg") or body_metrics["extracted_weight_kg"]
        body_build = payload.get("body_build") or body_metrics["extracted_body_build"]
        
        review_record = {
            "review_id": review_id,
            "sku_id": payload["sku_id"],
            "user_id": payload["user_id"],
            "rating": payload["rating"],
            "raw_text": raw_text,
            "sanitized_text": sanitized_text,
            "detected_language": detected_lang,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "body_build": body_build,
            "size_worn": payload.get("size_worn"),
            "fit_feedback": fit_feedback,
            "moderation_status": mod_status,
            "pii_redacted": 1 if pii_redacted else 0,
            "is_synthetic": 1 if synth_score > 0.6 else 0,
            "synthetic_confidence": synth_score,
            "source_platform": payload.get("source_platform", "Play Store"),
            "extracted_aspects": extracted_aspects
        }
        
        # 6. Stage 2 Claim Generation & Stage 3 Verification Pass
        claims = VerificationEngine.process_review_claims(review_record, extracted_aspects)
        
        # 7. Save to database
        save_review(review_record)
        save_conversion_claims(claims)
        
        # Push to moderation queue if flagged
        if mod_status in ("PENDING", "REJECTED"):
            push_to_moderation_queue(
                review_id=review_id,
                reason=reason,
                variance_score=metrics["variance_score"]
            )
            
        review_record["moderation_metrics"] = metrics
        review_record["claims"] = claims
        return review_record
