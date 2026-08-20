import sqlite3
from typing import List, Dict, Any
from src.db.database import get_connection

class CorpusAnalyticsEngine:
    """
    Computes corpus-wide purchase-conversion statistics and click-traceable claim logs across multi-source platforms.
    """

    TAXONOMY_CATEGORIES = [
        "size_fit_uncertainty",
        "wishlist_behavior",
        "price_behavior",
        "return_refund",
        "styling_occasion",
        "social_validation",
        "comparison_shopping"
    ]

    @classmethod
    def get_corpus_stats(cls) -> Dict[str, Any]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Total Ingested Reviews Count
            cursor.execute("SELECT COUNT(*) as total FROM reviews")
            total_reviews = cursor.fetchone()["total"]

            # Source Platform Breakdown (Play Store, App Store, Reddit)
            cursor.execute("SELECT COUNT(*) as count FROM reviews WHERE source_platform = 'Play Store'")
            play_store_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM reviews WHERE source_platform = 'App Store'")
            app_store_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM reviews WHERE source_platform = 'Reddit'")
            reddit_count = cursor.fetchone()["count"]

            # Total Claims Evaluated
            cursor.execute("SELECT COUNT(*) as total FROM conversion_claims")
            total_claims = cursor.fetchone()["total"]

            # Category Breakdown
            category_counts = {}
            for cat in cls.TAXONOMY_CATEGORIES:
                cursor.execute(
                    "SELECT COUNT(*) as cnt FROM conversion_claims WHERE category = ?",
                    (cat,)
                )
                cnt = cursor.fetchone()["cnt"]
                pct = round((cnt / total_claims * 100), 1) if total_claims > 0 else 0.0
                category_counts[cat] = {
                    "count": cnt,
                    "percentage": pct
                }

            # Verification Status Counts
            cursor.execute("SELECT COUNT(*) as verified FROM conversion_claims WHERE verification_status = 'VERIFIED'")
            verified_count = cursor.fetchone()["verified"]

            cursor.execute("SELECT COUNT(*) as rejected FROM conversion_claims WHERE verification_status = 'REJECTED'")
            rejected_count = cursor.fetchone()["rejected"]

            return {
                "total_corpus_reviews": total_reviews,
                "source_breakdown": {
                    "Play Store": play_store_count,
                    "App Store": app_store_count,
                    "Reddit": reddit_count
                },
                "total_claims_evaluated": total_claims,
                "verified_claims_count": verified_count,
                "rejected_claims_count": rejected_count,
                "verification_pass_rate_pct": round((verified_count / total_claims * 100), 1) if total_claims > 0 else 0.0,
                "category_breakdown": category_counts
            }
        finally:
            conn.close()

    @classmethod
    def get_verified_findings(cls, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.claim_id, c.category, c.claim_text, c.quote, c.review_id, c.sku_id, r.user_id, r.height_cm, r.weight_kg, r.size_worn, r.source_platform, r.sanitized_text as full_review_text
                FROM conversion_claims c
                JOIN reviews r ON c.review_id = r.review_id
                WHERE c.verification_status = 'VERIFIED'
                ORDER BY c.claim_id DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @classmethod
    def get_rejected_log(cls, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.claim_id, c.category, c.claim_text, c.quote, c.rejection_reason, c.review_id, c.sku_id, r.source_platform, r.sanitized_text as full_review_text
                FROM conversion_claims c
                JOIN reviews r ON c.review_id = r.review_id
                WHERE c.verification_status = 'REJECTED'
                ORDER BY c.claim_id DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @classmethod
    def get_record_details(cls, review_id: str) -> Dict[str, Any]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.*, s.title as sku_title, s.brand, s.category as sku_category
                FROM reviews r
                LEFT JOIN skus s ON r.sku_id = s.sku_id
                WHERE r.review_id = ?
                """,
                (review_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {}
            return dict(row)
        finally:
            conn.close()
