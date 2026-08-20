from typing import Dict, Any
from src.db.database import get_connection

class BehavioralProfiler:
    """
    Evaluates account metadata, purchase verification status, and review posting velocity
    to detect bot swarms and fraudulent reviewer profiles.
    """
    
    MAX_HOURLY_REVIEW_THRESHOLD = 5  # >5 reviews in 1 hour indicates velocity anomaly
    
    @classmethod
    def evaluate_user_trust(cls, user_id: str, sku_id: str) -> Dict[str, Any]:
        """
        Evaluates user profile features and returns trust_score and risk_flags.
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Fetch user account details
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                # Default for newly observed unregistered user ID
                is_verified = 0
                account_age_days = 0
            else:
                user_dict = dict(user_row)
                is_verified = user_dict.get("is_verified_purchaser", 0)
                account_age_days = user_dict.get("account_age_days", 0)
                
            # Check review velocity (reviews in last 1 hour across platform)
            cursor.execute(
                """
                SELECT COUNT(*) as velocity FROM reviews
                WHERE user_id = ? AND created_at >= datetime('now', '-1 hour')
                """,
                (user_id,)
            )
            velocity_row = cursor.fetchone()
            recent_velocity = velocity_row["velocity"] if velocity_row else 0
            
            # Risk Factors Calculation
            risk_score = 0.0
            risk_reasons = []
            
            if not is_verified:
                risk_score += 0.35
                risk_reasons.append("Unverified Purchaser")
                
            if account_age_days < 3:
                risk_score += 0.30
                risk_reasons.append("New Account (< 3 days old)")
                
            if recent_velocity > cls.MAX_HOURLY_REVIEW_THRESHOLD:
                risk_score += 0.40
                risk_reasons.append(f"High Posting Velocity ({recent_velocity} reviews/hr)")
                
            trust_score = round(max(0.0, 1.0 - risk_score), 2)
            
            return {
                "user_id": user_id,
                "is_verified_purchaser": bool(is_verified),
                "account_age_days": account_age_days,
                "recent_velocity": recent_velocity,
                "trust_score": trust_score,
                "risk_score": round(min(1.0, risk_score), 2),
                "risk_reasons": risk_reasons
            }
        finally:
            conn.close()
