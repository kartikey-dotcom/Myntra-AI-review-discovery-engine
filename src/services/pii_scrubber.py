import re
from typing import Tuple, Dict, Any

class PIIScrubber:
    """
    Sanitizes user review text by redacting PII (phone numbers, emails, handles, URLs)
    and canonicalizing obfuscated characters.
    """
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    
    # Indian & International Phone Numbers (including spaced/dash variants e.g., 9 8 7 6 5 4 3 2 1 0)
    PHONE_PATTERN = re.compile(
        r'(?:\+?91[\-\s]?)?(?:[6-9]\d{9}|[6-9][\s\.\-]?\d{3}[\s\.\-]?\d{3}[\s\.\-]?\d{3}|[6-9](?:[\s\.\-]?\d){9})'
    )
    
    URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
    SOCIAL_HANDLE_PATTERN = re.compile(r'(?:@|ig:|instagram:|fb:)\s*[\w\.]+', re.IGNORECASE)

    @classmethod
    def sanitize(cls, text: str) -> Tuple[str, bool]:
        """
        Redacts PII from text and returns (sanitized_text, is_redacted).
        """
        original = text
        sanitized = text
        
        # 1. Redact Emails
        sanitized = cls.EMAIL_PATTERN.sub('[REDACTED_EMAIL]', sanitized)
        
        # 2. Redact URLs
        sanitized = cls.URL_PATTERN.sub('[REDACTED_URL]', sanitized)
        
        # 3. Redact Social Handles
        sanitized = cls.SOCIAL_HANDLE_PATTERN.sub('[REDACTED_HANDLE]', sanitized)
        
        # 4. Redact Phone Numbers
        sanitized = cls.PHONE_PATTERN.sub('[REDACTED_PHONE]', sanitized)
        
        is_redacted = (sanitized != original)
        return sanitized, is_redacted

class LanguageDetector:
    """
    Identifies language & code-switching (English, Hinglish, Hindi).
    """
    
    HINGLISH_KEYWORDS = {
        "accha", "acha", "bohot", "bahut", "bakwas", "chota", "bada", "sahi",
        "mast", "ekdam", "kya", "bhai", "hai", "nahi", "nahin", "liya", "lia",
        "kapda", "kapra", "sirf", "kharab", "thik", "theek", "dil"
    }
    
    @classmethod
    def detect(cls, text: str) -> str:
        words = set(re.findall(r'\b\w+\b', text.lower()))
        hinglish_matches = words.intersection(cls.HINGLISH_KEYWORDS)
        
        if len(hinglish_matches) >= 1:
            return "hinglish"
        
        # Check Devanagari script characters for pure Hindi
        if any('\u0900' <= char <= '\u097F' for char in text):
            return "hi"
            
        return "en"
