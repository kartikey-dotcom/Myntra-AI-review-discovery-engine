from typing import Dict, Any, Tuple
from src.services.synthetic_detector import SyntheticTextDetector
from src.services.behavioral_profiler import BehavioralProfiler

class ModerationRuleEngine:
    """
    Combines Synthetic Text Metrics, Behavioral Profile Trust Scores, and Rating-Sentiment
    Variance to determine automated moderation decisions (APPROVED, REJECTED, or PENDING).
    """
    
    # Thresholds
    AUTO_APPROVE_TRUST_THRESHOLD = 0.65
    SYNTHETIC_REJECT_THRESHOLD = 0.85
    SYNTHETIC_FLAG_THRESHOLD = 0.50
    
    @classmethod
    def evaluate(cls, payload: Dict[str, Any]) -> Tuple[str, float, str, Dict[str, Any]]:
        """
        Returns (moderation_status, confidence_score, reason, composite_metrics)
        moderation_status: APPROVED | REJECTED | PENDING
        """
        text = payload["review_text"]
        rating = payload["rating"]
        user_id = payload["user_id"]
        sku_id = payload["sku_id"]
        
        # 1. Run Synthetic Detector
        is_synthetic, synthetic_score, text_metrics = SyntheticTextDetector.analyze(text)
        
        # 2. Run Behavioral Profiler
        profile = BehavioralProfiler.evaluate_user_trust(user_id, sku_id)
        
        # 3. Calculate Rating-Text Sentiment Variance Score
        # Simple sentiment heuristic for Phase 2 integration
        lower_text = text.lower()
        neg_words = {"bad", "poor", "terrible", "horrible", "worst", "waste", "torn", "defect", "bakwas"}
        pos_words = {"good", "great", "excellent", "awesome", "perfect", "love", "amazing", "mast", "accha"}
        
        words = set(lower_text.split())
        neg_count = len(words.intersection(neg_words))
        pos_count = len(words.intersection(pos_words))
        
        variance_score = 0.0
        if rating >= 4 and neg_count > 0 and pos_count == 0:
            variance_score = 0.80  # High star rating with exclusively negative text
        elif rating <= 2 and pos_count > 0 and neg_count == 0:
            variance_score = 0.75  # Low star rating with exclusively positive text
            
        # Decision Matrix Computation
        status = "APPROVED"
        reason = "Automated approval for low-risk review"
        
        # Rule 1: High synthetic AI score -> REJECT or PENDING
        if synthetic_score >= cls.SYNTHETIC_REJECT_THRESHOLD:
            status = "REJECTED" if profile["risk_score"] > 0.5 else "PENDING"
            reason = f"High synthetic AI review score ({synthetic_score})"
        # Rule 2: High Rating-Sentiment Variance -> PENDING
        elif variance_score >= 0.70:
            status = "PENDING"
            reason = f"Rating-sentiment discrepancy detected (Variance score: {variance_score})"
        # Rule 3: High Behavioral Risk (Unverified + Velocity Spike) -> PENDING
        elif profile["risk_score"] >= 0.70:
            status = "PENDING"
            reasons_str = ", ".join(profile["risk_reasons"])
            reason = f"Behavioral risk flags: {reasons_str}"
        # Rule 4: Verified Purchaser + Low Risk -> Fast-Track APPROVED (>70% target)
        elif profile["is_verified_purchaser"] and synthetic_score < cls.SYNTHETIC_FLAG_THRESHOLD:
            status = "APPROVED"
            reason = "Fast-track approval for verified purchaser"
            
        composite_metrics = {
            "synthetic_score": synthetic_score,
            "behavioral_trust_score": profile["trust_score"],
            "behavioral_risk_score": profile["risk_score"],
            "variance_score": variance_score,
            "text_metrics": text_metrics,
            "user_profile": profile
        }
        
        return status, synthetic_score, reason, composite_metrics
