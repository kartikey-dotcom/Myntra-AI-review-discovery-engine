from typing import List, Dict, Any
from src.db.database import get_connection

class SellerAnalyticsEngine:
    """
    Powers Brand Partner & Merchant Analytics Dashboard.
    Exposes aspect defect trends, customer sentiment alerts, and sizing chart calibration recommendations.
    """
    
    @classmethod
    def get_brand_analytics(cls, brand_name: str) -> Dict[str, Any]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Fetch SKUs owned by brand
            cursor.execute("SELECT sku_id, title, category FROM skus WHERE brand LIKE ?", (f"%{brand_name}%",))
            skus = [dict(r) for r in cursor.fetchall()]
            sku_ids = [s["sku_id"] for s in skus]
            
            if not sku_ids:
                return {
                    "brand": brand_name,
                    "total_skus": 0,
                    "quality_alerts": [],
                    "size_calibration_recommendation": "No registered SKUs found for this brand."
                }
                
            placeholders = ",".join(["?"] * len(sku_ids))
            
            # Fetch negative aspect counts
            cursor.execute(
                f"""
                SELECT aspect_name, COUNT(*) as defect_count
                FROM review_aspects
                WHERE sku_id IN ({placeholders}) AND polarity = 'NEGATIVE'
                GROUP BY aspect_name
                ORDER BY defect_count DESC
                """,
                sku_ids
            )
            defects = [dict(r) for r in cursor.fetchall()]
            
            # Fetch sizing fit stats
            cursor.execute(
                f"""
                SELECT 
                    SUM(runs_small_count) as small,
                    SUM(true_to_size_count) as true_sz,
                    SUM(runs_large_count) as large,
                    SUM(total_reviews) as total
                FROM sku_fit_summaries
                WHERE sku_id IN ({placeholders})
                """,
                sku_ids
            )
            fit_row = cursor.fetchone()
            
            total_revs = fit_row["total"] if fit_row and fit_row["total"] else 1
            small_pct = round(((fit_row["small"] or 0) / total_revs * 100), 1)
            large_pct = round(((fit_row["large"] or 0) / total_revs * 100), 1)
            
            calibration = "Sizing alignment optimal (True to size)."
            if small_pct > 25.0:
                calibration = f"Recommendation: Update sizing chart for {brand_name}. {small_pct}% of customers report items run SMALL."
            elif large_pct > 25.0:
                calibration = f"Recommendation: Update sizing chart for {brand_name}. {large_pct}% of customers report items run LARGE."
                
            return {
                "brand": brand_name,
                "total_skus_tracked": len(skus),
                "total_customer_feedback_samples": total_revs,
                "top_quality_defect_alerts": defects[:3],
                "sizing_fit_breakdown": {
                    "runs_small_pct": small_pct,
                    "runs_large_pct": large_pct
                },
                "size_calibration_recommendation": calibration
            }
        finally:
            conn.close()
