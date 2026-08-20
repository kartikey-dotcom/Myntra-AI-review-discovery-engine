import re
from typing import Dict, Any, Optional

class FitIntelligenceEngine:
    """
    Extracts body metrics (height, weight, body build) from unstructured review text via NER rules
    and computes SKU fit delta distributions.
    """
    
    # Regex patterns for height & weight extraction
    FEET_INCHES_PATTERN = re.compile(r'\b([4-7])\s*(?:ft|\'|\text{ feet})\s*([0-1]?\d)?\s*(?:in|\"|\text{ inches})?\b', re.IGNORECASE)
    CM_PATTERN = re.compile(r'\b(1[2-9]\d|2[0-1]\d)\s*cm\b', re.IGNORECASE)
    KG_PATTERN = re.compile(r'\b([3-9]\d|1\d\d|200)\s*kg\b', re.IGNORECASE)
    LBS_PATTERN = re.compile(r'\b([6-9]\d|1\d\d|2\d\d|3\d\d|400)\s*(?:lbs|pounds)\b', re.IGNORECASE)
    
    BUILD_KEYWORDS = {
        "SLIM": ["slim", "lean", "skinny", "petite"],
        "ATHLETIC": ["athletic", "muscular", "toned", "gym"],
        "REGULAR": ["average", "regular", "normal"],
        "HEAVY": ["heavy", "chubby", "plus size", "broad", "curvy"]
    }

    @classmethod
    def extract_body_metrics(cls, text: str) -> Dict[str, Any]:
        """
        Parses unstructured review text for height, weight, and build descriptions.
        """
        extracted_height = None
        extracted_weight = None
        extracted_build = None
        
        # 1. Height Extraction (CM or Feet/Inches)
        cm_match = cls.CM_PATTERN.search(text)
        if cm_match:
            extracted_height = float(cm_match.group(1))
        else:
            ft_match = cls.FEET_INCHES_PATTERN.search(text)
            if ft_match:
                feet = int(ft_match.group(1))
                inches = int(ft_match.group(2)) if ft_match.group(2) else 0
                extracted_height = round((feet * 30.48) + (inches * 2.54), 1)
                
        # 2. Weight Extraction (KG or LBS)
        kg_match = cls.KG_PATTERN.search(text)
        if kg_match:
            extracted_weight = float(kg_match.group(1))
        else:
            lbs_match = cls.LBS_PATTERN.search(text)
            if lbs_match:
                lbs = float(lbs_match.group(1))
                extracted_weight = round(lbs * 0.453592, 1)
                
        # 3. Build Keyword Extraction
        lower_text = text.lower()
        for build_type, keywords in cls.BUILD_KEYWORDS.items():
            if any(kw in lower_text for kw in keywords):
                extracted_build = build_type
                break
                
        return {
            "extracted_height_cm": extracted_height,
            "extracted_weight_kg": extracted_weight,
            "extracted_body_build": extracted_build
        }

    @classmethod
    def classify_fit_delta(cls, text: str) -> str:
        """
        Determines if review implies RUNS_SMALL, TRUE_TO_SIZE, or RUNS_LARGE.
        """
        lower = text.lower()
        if any(w in lower for w in ["tight", "small", "chota", "short", "size up", "order larger"]):
            return "RUNS_SMALL"
        elif any(w in lower for w in ["loose", "large", "bada", "baggy", "size down", "oversized"]):
            return "RUNS_LARGE"
        elif any(w in lower for w in ["perfect", "true to size", "exact fit", "sahi", "good fit"]):
            return "TRUE_TO_SIZE"
        return "TRUE_TO_SIZE"
