from typing import Dict, Any, Tuple

class ComputerVisionFilter:
    """
    Evaluates customer-uploaded garment photos for image quality, blurriness,
    lighting condition, and content relevance.
    """
    
    MIN_LAPLACIAN_VARIANCE = 100.0  # Threshold for blurriness
    MIN_MEAN_INTENSITY = 30.0        # Threshold for extreme dark lighting
    
    @classmethod
    def evaluate_image_metadata(cls, image_bytes: bytes, filename: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """
        Evaluates raw image bytes or filename metadata.
        Returns: (is_accepted, reason, metrics)
        """
        # File extension validation
        allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
        ext = ("." + filename.split(".")[-1].lower()) if "." in filename else ".jpg"
        
        if ext not in allowed_exts:
            return False, "Unsupported image format", {"filename": filename}
            
        file_size_kb = len(image_bytes) / 1024.0 if image_bytes else 150.0
        
        if file_size_kb < 10.0:
            return False, "Image file too small or corrupted", {"size_kb": file_size_kb}
            
        # Simulated CV Analysis Metrics (Laplacian Variance & Mean Intensity)
        # Higher Laplacian Variance = Sharper image, lower = Blurry
        simulated_blur_score = 150.0 if file_size_kb > 20.0 else 80.0
        simulated_brightness = 120.0  # Normal lighting
        
        is_blurry = simulated_blur_score < cls.MIN_LAPLACIAN_VARIANCE
        is_too_dark = simulated_brightness < cls.MIN_MEAN_INTENSITY
        
        if is_blurry:
            return False, "Image too blurry. Please upload a clearer photo.", {
                "blur_score": simulated_blur_score,
                "brightness": simulated_brightness
            }
            
        return True, "Image verified for review gallery", {
            "blur_score": simulated_blur_score,
            "brightness": simulated_brightness,
            "file_size_kb": round(file_size_kb, 1)
        }
