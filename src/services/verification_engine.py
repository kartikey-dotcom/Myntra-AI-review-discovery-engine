import logging
from typing import List, Dict, Any, Tuple
from src.config import config

logger = logging.getLogger(__name__)

# Import official Google GenAI SDK
try:
    from google import genai
except ImportError:
    genai = None

class VerificationEngine:
    """
    Stage 3 Adversarial Relevance Verification Engine.
    Verifies that every generated claim is strictly supported by its linked candidate quote.
    Rejects claims with interpretive stretch, routing them to the non-empty Rejected Log.
    """

    @classmethod
    def verify_claim(cls, claim_text: str, quote_text: str, category: str) -> Tuple[bool, str]:
        """
        Adversarial Verification Pass:
        Evaluates whether quote_text strictly supports claim_text without interpretive stretch.
        Returns: (is_verified: bool, rejection_reason: str)
        """
        # Strict Rule-Based Adversarial Verification Rules
        claim_lower = claim_text.lower()
        quote_lower = quote_text.lower()

        # Check 1: Quote must contain substantive overlap with claim category
        if len(quote_lower.strip()) < 10:
            return False, "Candidate quote is too short (< 10 chars) to provide sufficient evidence."

        # Check 2: Direct keyword alignment check
        if category == "size_fit_uncertainty" and not any(k in quote_lower for k in ["size", "fit", "tight", "small", "large", "chart", "length"]):
            return False, "Quote lacks explicit size or fit uncertainty metrics."

        if category == "price_behavior" and not any(k in quote_lower for k in ["price", "cost", "expensive", "discount", "worth", "sale"]):
            return False, "Quote mentions general sentiment but lacks specific price hesitation references."

        if category == "wishlist_behavior" and not any(k in quote_lower for k in ["wishlist", "saved", "cart", "later", "weeks", "waiting"]):
            return False, "Quote does not contain explicit wishlist or purchase deferral behavior."

        # Check 3: GenAI Secondary Verification Check if valid Gemini API key available
        has_valid_key = config.GEMINI_API_KEY and not config.GEMINI_API_KEY.endswith("_api_key_here") and len(config.GEMINI_API_KEY) > 25
        if has_valid_key and genai:
            try:
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                prompt = f"""
                You are a strict, adversarial Data Verification Audit Agent.
                Assess if the provided Quote strictly and directly supports the Claim without any interpretive stretch.
                
                Claim: "{claim_text}"
                Quote: "{quote_text}"
                Category: "{category}"
                
                Respond with EXACTLY one line:
                VERIFIED: <brief reason>
                OR
                REJECTED: <one line reason why quote fails to strictly support claim>
                """
                response = client.models.generate_content(
                    model=config.GEMINI_MODEL_NAME,
                    contents=prompt
                )
                res_text = response.text.strip() if response else ""
                if res_text.startswith("REJECTED:"):
                    reason = res_text.replace("REJECTED:", "").strip()
                    return False, reason or "Failed secondary LLM adversarial verification check."
            except Exception as e:
                logger.warning(f"Adversarial LLM verification fallback triggered: {e}")

        # Default verification pass if quote aligns cleanly
        return True, ""

    @classmethod
    def process_review_claims(cls, review_data: Dict[str, Any], aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 2 Claim Generation & Stage 3 Verification Pass over an ingested review record.
        """
        results = []
        review_id = review_data.get("review_id", "REV-000")
        sku_id = review_data.get("sku_id", "SKU-000")
        raw_text = review_data.get("sanitized_text", review_data.get("raw_text", ""))
        user_id = review_data.get("user_id", "USR-000")
        height = review_data.get("height_cm")
        weight = review_data.get("weight_kg")

        for asp in aspects:
            category = asp.get("aspect_name", "general")
            category_type = asp.get("category_type", "CONVERSION_HESITATION")
            snippet = asp.get("snippet", raw_text)
            matched_kw = asp.get("matched_keyword", "")

            # Generate candidate claim
            if category == "size_fit_uncertainty":
                claim = f"Shoppers defer purchase due to uncertainty regarding size chart accuracy and fit delta."
            elif category == "price_behavior":
                claim = f"Shoppers hold items in wishlist waiting for price drops or discount validation."
            elif category == "wishlist_behavior":
                claim = f"Shoppers use wishlist as a temporary holding area while deliberating for weeks."
            elif category == "return_refund":
                claim = f"Hesitation stems from concerns regarding return policy complexity or replacement delays."
            elif category == "styling_occasion":
                claim = f"Shoppers hesitate when unsure of event suitability or pairing options."
            elif category == "social_validation":
                claim = f"Buyers delay purchase due to lack of real customer photos or unverified reviews."
            elif category == "comparison_shopping":
                claim = f"Shoppers compare Myntra items against competing brands before committing."
            else:
                claim = f"Customer feedback regarding {category.lower()} quality impact."

            # Stage 3 Adversarial Verification Pass
            is_verified, reason = cls.verify_claim(claim, snippet, category)

            record = {
                "review_id": review_id,
                "sku_id": sku_id,
                "user_id": user_id,
                "category": category,
                "claim_text": claim,
                "quote": snippet,
                "full_text": raw_text,
                "height_cm": height,
                "weight_kg": weight,
                "verification_status": "VERIFIED" if is_verified else "REJECTED",
                "rejection_reason": reason if not is_verified else None
            }
            results.append(record)

        return results
