from typing import List, Dict, Any, Optional
from src.db.database import get_reviews_for_sku

class OpenSearchIndexEngine:
    """
    Simulates OpenSearch / Elasticsearch inverted index engine for fast faceted
    review filtering by body metrics, size worn, build, and aspect keywords.
    """
    
    @classmethod
    def search_reviews(
        cls,
        sku_id: str,
        min_height_cm: Optional[float] = None,
        max_height_cm: Optional[float] = None,
        min_weight_kg: Optional[float] = None,
        max_weight_kg: Optional[float] = None,
        body_build: Optional[str] = None,
        size_worn: Optional[str] = None,
        min_rating: Optional[int] = None,
        query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Executes faceted filtering on approved SKU reviews.
        """
        all_reviews = get_reviews_for_sku(sku_id, limit=200, offset=0)
        filtered = []
        
        for rev in all_reviews:
            # 1. Height Filter
            if min_height_cm is not None and (rev.get("height_cm") is None or rev["height_cm"] < min_height_cm):
                continue
            if max_height_cm is not None and (rev.get("height_cm") is None or rev["height_cm"] > max_height_cm):
                continue
                
            # 2. Weight Filter
            if min_weight_kg is not None and (rev.get("weight_kg") is None or rev["weight_kg"] < min_weight_kg):
                continue
            if max_weight_kg is not None and (rev.get("weight_kg") is None or rev["weight_kg"] > max_weight_kg):
                continue
                
            # 3. Body Build Filter
            if body_build and rev.get("body_build") != body_build.upper():
                continue
                
            # 4. Size Worn Filter
            if size_worn and rev.get("size_worn") != size_worn.upper():
                continue
                
            # 5. Rating Filter
            if min_rating is not None and rev.get("rating", 0) < min_rating:
                continue
                
            # 6. Aspect Keyword Search Query
            if query and query.lower() not in rev.get("sanitized_text", "").lower():
                continue
                
            filtered.append(rev)
            
        paginated = filtered[offset : offset + limit]
        
        return {
            "sku_id": sku_id,
            "total_matches": len(filtered),
            "applied_filters": {
                "min_height_cm": min_height_cm,
                "max_height_cm": max_height_cm,
                "body_build": body_build,
                "size_worn": size_worn,
                "query": query
            },
            "reviews": paginated
        }
