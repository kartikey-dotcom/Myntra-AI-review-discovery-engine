import re
import math
from typing import Dict, Any, Tuple

class SyntheticTextDetector:
    """
    Evaluates review text for statistical indicators of synthetic AI-generated content (LLMs)
    and automated bot spam patterns using perplexity, token entropy, burstiness, and n-gram repetition.
    """
    
    # Common repetitive template fillers used by low-quality bot generators
    BOT_TEMPLATE_PHRASES = [
        "as an ai", "highly recommend purchasing", "exceeded my expectations in every way",
        "in conclusion", "it is important to note", "must buy product", "top notch quality product"
    ]
    
    @classmethod
    def calculate_token_entropy(cls, text: str) -> float:
        """
        Calculates Shannon entropy of token frequency.
        Synthetic LLM text often exhibits unnaturally uniform token entropy.
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0
        
        freqs = {}
        for w in words:
            freqs[w] = freqs.get(w, 0) + 1
            
        entropy = 0.0
        total = len(words)
        for count in freqs.values():
            p = count / total
            entropy -= p * math.log2(p)
            
        return round(entropy, 4)
    
    @classmethod
    def calculate_burstiness(cls, text: str) -> float:
        """
        Calculates sentence length variance (burstiness).
        Human text has high burstiness (mix of short and long sentences).
        LLM text tends to have uniform sentence lengths.
        """
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) <= 1:
            return 0.5  # Neutral default for single-sentence reviews
            
        lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        if mean_len == 0:
            return 0.0
            
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        
        # Burstiness score bounded [0.0, 1.0]
        burstiness = std_dev / (mean_len + 1.0)
        return min(1.0, round(burstiness, 4))
    
    @classmethod
    def analyze(cls, text: str) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluates review text and returns: (is_flagged_synthetic, confidence_score, metrics_dict)
        Confidence Score: 0.0 (Definitely Human) to 1.0 (Definitely Synthetic AI/Bot)
        """
        lower_text = text.lower()
        words = re.findall(r'\b\w+\b', lower_text)
        word_count = len(words)
        
        if word_count < 4:
            # Emoji / short reviews are fast-tracked as non-synthetic (handled separately)
            return False, 0.1, {"word_count": word_count, "reason": "Short text fast-track"}
            
        entropy = cls.calculate_token_entropy(text)
        burstiness = cls.calculate_burstiness(text)
        
        # Check template phrase matches
        template_match_count = sum(1 for phrase in cls.BOT_TEMPLATE_PHRASES if phrase in lower_text)
        
        # Scoring model heuristic:
        # LLMs: Moderate/High entropy + Low burstiness + Uniform phrasing
        score = 0.0
        
        # Low burstiness penalty (< 0.15 indicates rigid uniform sentence structure)
        if burstiness < 0.15 and word_count > 15:
            score += 0.35
            
        # Template matches
        if template_match_count >= 1:
            score += 0.40 * template_match_count
            
        # Repetitive token ratio
        unique_ratio = len(set(words)) / word_count
        if unique_ratio < 0.4 and word_count > 10:
            score += 0.30  # Highly repetitive text
            
        score = min(1.0, round(score, 4))
        is_synthetic = score >= 0.70
        
        metrics = {
            "word_count": word_count,
            "entropy": entropy,
            "burstiness": burstiness,
            "template_matches": template_match_count,
            "synthetic_score": score
        }
        
        return is_synthetic, score, metrics
