import re
from typing import List, Dict, Any

class ABSAEngine:
    """
    Aspect-Based Sentiment Analysis (ABSA) & Conversion Taxonomy Extractor.
    Extracts physical product attributes AND 7 purchase hesitation/wishlist categories.
    """

    CONVERSION_TAXONOMY_KEYWORDS = {
        "size_fit_uncertainty": [
            "size", "fit", "sizing", "chart", "tight", "loose", "small", "large",
            "chest", "waist", "length", "sleeve", "shoulder", "measurements", "fit delta"
        ],
        "wishlist_behavior": [
            "wishlist", "saved", "cart", "later", "weeks", "months", "waiting",
            "deliberating", "deciding", "contemplating", "finally bought"
        ],
        "price_behavior": [
            "price", "cost", "expensive", "overpriced", "worth", "discount", "sale",
            "deal", "value for money", "affordable", "price drop"
        ],
        "return_refund": [
            "return", "refund", "exchange", "policy", "hassle", "pickup", "damaged return",
            "return process", "replacement"
        ],
        "styling_occasion": [
            "style", "styling", "occasion", "party", "office", "formal", "casual",
            "wedding", "pair", "outfit", "wear with", "match"
        ],
        "social_validation": [
            "photo", "pics", "real image", "picture", "review", "validation", "feedback",
            "other buyers", "customer photos", "proof"
        ],
        "comparison_shopping": [
            "compared", "versus", "other brand", "alternative", "cheaper option",
            "competing", "zara", "hm", "roadster", "levis"
        ]
    }

    PRODUCT_ASPECT_KEYWORDS = {
        "Fabric Quality": ["fabric", "material", "cloth", "cotton", "soft", "polyester", "denim", "feel"],
        "Color Accuracy": ["color", "colour", "shade", "fade", "washed", "bleeding", "dull", "picture match"],
        "Stitching": ["stitch", "stitching", "thread", "seam", "tailoring", "durability"],
        "Transparency": ["transparent", "see through", "thin", "sheer", "lining"],
        "Shrinkage": ["shrink", "shrank", "shrinkage", "wash shrink"]
    }

    @classmethod
    def extract_aspects(cls, text: str) -> List[Dict[str, Any]]:
        text_lower = text.lower()
        extracted = []

        # 1. Extract Purchase Hesitation Categories
        for category, keywords in cls.CONVERSION_TAXONOMY_KEYWORDS.items():
            matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
            if matches:
                snippet = cls._extract_snippet(text, matches[0])
                polarity = cls._evaluate_polarity(snippet)
                extracted.append({
                    "aspect": category,
                    "aspect_name": category,
                    "category_type": "CONVERSION_HESITATION",
                    "snippet": snippet,
                    "polarity": polarity,
                    "sentiment_score": 0.2 if polarity == "NEGATIVE" else 0.8,
                    "matched_keyword": matches[0]
                })

        # 2. Extract Product Aspect Attributes
        for aspect_name, keywords in cls.PRODUCT_ASPECT_KEYWORDS.items():
            matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
            if matches:
                snippet = cls._extract_snippet(text, matches[0])
                polarity = cls._evaluate_polarity(snippet)
                extracted.append({
                    "aspect": aspect_name,
                    "aspect_name": aspect_name,
                    "category_type": "PRODUCT_QUALITY",
                    "snippet": snippet,
                    "polarity": polarity,
                    "sentiment_score": 0.2 if polarity == "NEGATIVE" else 0.8,
                    "matched_keyword": matches[0]
                })

        return extracted

    @classmethod
    def _evaluate_polarity(cls, snippet: str) -> str:
        snippet_lower = snippet.lower()
        neg_words = ["bad", "poor", "thin", "faded", "dull", "shrink", "rough", "tight", "short", "expensive", "hassle", "confusing", "issue", "problem"]
        pos_words = ["good", "great", "soft", "super", "comfortable", "breathable", "perfect", "worth", "beautiful", "sturdy", "warm"]

        has_neg = any(nw in snippet_lower for nw in neg_words)
        has_pos = any(pw in snippet_lower for pw in pos_words)

        if has_neg and not has_pos:
            return "NEGATIVE"
        if has_neg and has_pos:
            # Check proximity to negative words
            return "NEGATIVE" if any(w in snippet_lower for w in ["dull", "fade", "shrink", "tight", "bad", "poor"]) else "POSITIVE"
        return "POSITIVE" if has_pos else "NEUTRAL"

    @classmethod
    def _extract_snippet(cls, text: str, keyword: str, window: int = 35) -> str:
        idx = text.lower().find(keyword.lower())
        if idx == -1:
            return text[:70]
        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)
        return text[start:end].strip()
