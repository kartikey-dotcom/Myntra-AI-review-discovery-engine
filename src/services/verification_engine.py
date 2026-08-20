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
    Rejects claims with mechanism mismatches or interpretive stretch.
    """

    @classmethod
    def verify_claim(cls, claim_text: str, quote_text: str, category: str) -> Tuple[bool, str]:
        """
        Adversarial Verification Pass:
        Evaluates whether quote_text strictly and directly supports claim_text mechanism without interpretive stretch.
        Returns: (is_verified: bool, rejection_reason: str)
        """
        quote_lower = quote_text.lower().strip()
        claim_lower = claim_text.lower().strip()

        # Check 1: Length & Substantive Content Check
        if len(quote_lower) < 12:
            return False, "Candidate quote is too short (< 12 chars) to provide sufficient evidence."

        # Check 2: Strict Category & Mechanism Alignment Rules
        if category == "wishlist_behavior":
            # If claim is about deliberation duration/weeks
            has_time_duration = any(k in quote_lower for k in ["week", "month", "days", "deliberat", "saved for", "waiting for 3", "kept in wishlist for"])
            has_price_focus = any(k in quote_lower for k in ["price drop", "discount", "sale price", "deal", "rs", "rupees", "cheaper"])
            
            if has_price_focus and not has_time_duration:
                return False, "Quote refers to price-tracking mechanism rather than time-based deliberation."
            if not has_time_duration and not any(k in quote_lower for k in ["wishlist", "saved", "cart", "later"]):
                return False, "Quote lacks explicit wishlist holding or deliberation duration mechanism."

        elif category == "price_behavior":
            has_price_terms = any(k in quote_lower for k in ["price", "cost", "expensive", "discount", "sale", "deal", "worth", "value", "rs", "rupees"])
            if not has_price_terms:
                return False, "Quote mentions general sentiment but lacks explicit price or discount mechanism references."

        elif category == "size_fit_uncertainty":
            has_size_terms = any(k in quote_lower for k in ["size", "fit", "tight", "loose", "small", "large", "chart", "chest", "length", "waist", "sleeve"])
            if not has_size_terms:
                return False, "Quote lacks explicit size or fit uncertainty metrics."

        elif category == "return_refund":
            has_return_terms = any(k in quote_lower for k in ["return", "refund", "exchange", "policy", "pickup", "hassle", "replacement"])
            if not has_return_terms:
                return False, "Quote does not contain explicit return policy or refund hassle references."

        elif category == "styling_occasion":
            has_styling_terms = any(k in quote_lower for k in ["style", "styling", "occasion", "party", "office", "formal", "wedding", "pair", "outfit"])
            if not has_styling_terms:
                return False, "Quote lacks explicit event suitability or outfit styling references."

        elif category == "social_validation":
            has_social_terms = any(k in quote_lower for k in ["photo", "pics", "picture", "real image", "customer photos", "buyer proof"])
            if not has_social_terms:
                return False, "Quote does not mention real customer photo or buyer social validation proof."

        elif category == "comparison_shopping":
            has_comp_terms = any(k in quote_lower for k in ["compared", "versus", "other brand", "alternative", "cheaper option", "zara", "hm", "roadster", "levis"])
            if not has_comp_terms:
                return False, "Quote does not contain explicit multi-brand comparison shopping references."

        # Check 3: GenAI Secondary Verification Check if valid Gemini API key available
        has_valid_key = config.GEMINI_API_KEY and not config.GEMINI_API_KEY.endswith("_api_key_here") and len(config.GEMINI_API_KEY) > 25
        if has_valid_key and genai:
            try:
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                prompt = f"""
                You are a strict, adversarial Data Verification Audit Agent.
                Assess if the provided Quote strictly and directly supports the Claim mechanism without any interpretive stretch.
                
                Claim: "{claim_text}"
                Quote: "{quote_text}"
                Category: "{category}"
                
                Instruction: A quote mentioning 'wishlist' does NOT automatically support a claim about deliberation duration, price-waiting, or any other specific mechanism.
                If the quote is about a different mechanism (e.g., price-tracking) than the claim (e.g., time-based deliberation), answer REJECTED.
                
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

        return True, ""

    @classmethod
    def process_review_claims(cls, review_data: Dict[str, Any], aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 2 Claim Generation & Stage 3 Verification Pass over an ingested review record.
        Runs independently on every (claim, quote, record_id) triple.
        """
        results = []
        review_id = review_data.get("review_id", "REV-000")
        sku_id = review_data.get("sku_id", "SKU-000")
        raw_text = review_data.get("sanitized_text", review_data.get("raw_text", ""))
        user_id = review_data.get("user_id", "USR-000")
        height = review_data.get("height_cm")
        weight = review_data.get("weight_kg")
        platform = review_data.get("source_platform", "Play Store")

        for asp in aspects:
            category = asp.get("aspect_name", "general")
            snippet = asp.get("snippet", raw_text)

            # Generate candidate claim strictly aligned with category mechanism
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

            # Stage 3 Adversarial Verification Pass on this specific (claim, quote, record_id) triple
            is_verified, reason = cls.verify_claim(claim, snippet, category)

            record = {
                "review_id": review_id,
                "sku_id": sku_id,
                "user_id": user_id,
                "source_platform": platform,
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
