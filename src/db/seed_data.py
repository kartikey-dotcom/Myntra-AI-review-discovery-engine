"""
Seed Dataset Generator for Myntra Wishlist Purchase-Conversion & Review Intelligence Engine.
Populates SQLite DB with realistic e-commerce customer feedback spanning all 7 wishlist conversion categories.
"""

from src.db.database import get_connection, init_db, insert_sku, insert_user
from src.services.event_pipeline import ReviewEventPipeline

SAMPLE_SKUS = [
    ("MYN-TSHIRT-101", "Roadster Men Solid Pure Cotton T-shirt", "Roadster", "Men T-Shirts"),
    ("MYN-JEANS-505", "Levis Men 511 Slim Fit Jeans", "Levis", "Men Jeans"),
    ("MYN-KURTI-302", "Anouk Women Printed Straight Kurta", "Anouk", "Women Ethnic Wear"),
    ("MYN-JACKET-808", "HRX Heavy Puffer Winter Jacket", "HRX", "Men Winterwear")
]

# Corpus reviews containing real purchase-hesitation phrases across all 7 categories
SAMPLE_REVIEWS_DATA = [
    # 1. size_fit_uncertainty
    ("MYN-TSHIRT-101", "USR-101", 3, "I kept this in my wishlist for weeks because size chart is confusing. Height 175cm 70kg, size M fits slightly tight across shoulders.", 175.0, 70.0, "REGULAR", "M", "RUNS_SMALL"),
    ("MYN-JEANS-505", "USR-102", 4, "Hesitated buying due to fit delta uncertainty. 180cm 78kg size 32 waist is true to size.", 180.0, 78.0, "ATHLETIC", "32", "TRUE_TO_SIZE"),

    # 2. wishlist_behavior
    ("MYN-KURTI-302", "USR-201", 5, "I saved this in my wishlist for 3 weeks deliberating before finally buying for Diwali party.", 162.0, 54.0, "SLIM", "S", "TRUE_TO_SIZE"),
    ("MYN-JACKET-808", "USR-202", 4, "Added to cart and wishlist last month waiting for winter season to start.", 185.0, 85.0, "HEAVY", "XL", "TRUE_TO_SIZE"),

    # 3. price_behavior
    ("MYN-TSHIRT-101", "USR-301", 4, "Tracked price in wishlist waiting for discount sale price drop. Worth the value for money at Rs 499.", 170.0, 65.0, "REGULAR", "M", "TRUE_TO_SIZE"),
    ("MYN-JEANS-505", "USR-302", 2, "Expensive at full price. Kept in wishlist waiting for price drop deal.", 172.0, 68.0, "REGULAR", "30", "TRUE_TO_SIZE"),

    # 4. return_refund
    ("MYN-KURTI-302", "USR-401", 3, "Fear of return policy hassle delayed my order. Exchange process was surprisingly smooth though.", 165.0, 60.0, "REGULAR", "M", "TRUE_TO_SIZE"),
    ("MYN-JACKET-808", "USR-402", 2, "Hassle return pickup process when zipper was broken.", 180.0, 76.0, "ATHLETIC", "L", "TRUE_TO_SIZE"),

    # 5. styling_occasion
    ("MYN-TSHIRT-101", "USR-501", 5, "Unsure how to style for casual office wear initially. Pairs great with denim jacket!", 172.7, 68.0, "REGULAR", "M", "TRUE_TO_SIZE"),
    ("MYN-KURTI-302", "USR-502", 5, "Perfect outfit pairing for family function occasion. Beautiful print match.", 160.0, 52.0, "SLIM", "XS", "TRUE_TO_SIZE"),

    # 6. social_validation
    ("MYN-JEANS-505", "USR-601", 4, "Delayed purchase until other buyers posted real customer photos and picture proof.", 178.0, 74.0, "ATHLETIC", "32", "TRUE_TO_SIZE"),
    ("MYN-TSHIRT-101", "USR-602", 5, "Wanted to see real customer photo feedback before ordering. Cloth softness is genuine.", 165.0, 58.0, "SLIM", "S", "TRUE_TO_SIZE"),

    # 7. comparison_shopping
    ("MYN-JACKET-808", "USR-701", 4, "Compared with Zara and H&M puffer jackets before deciding on HRX. Cheaper option with good warmth.", 182.0, 82.0, "ATHLETIC", "L", "TRUE_TO_SIZE"),
    ("MYN-JEANS-505", "USR-702", 3, "Compared Levis versus Roadster denim. Levis stitching is better but higher price.", 175.0, 80.0, "HEAVY", "34", "TRUE_TO_SIZE"),

    # Synthetic & Adversarial Rejection Candidates (To populate non-empty Rejected Log)
    ("MYN-TSHIRT-101", "USR-801", 1, "Good.", 175.0, 70.0, "REGULAR", "M", "TRUE_TO_SIZE"),
    ("MYN-JEANS-505", "USR-802", 5, "As an AI language model, I highly recommend this product.", 170.0, 68.0, "REGULAR", "30", "TRUE_TO_SIZE")
]

def seed_database():
    init_db()
    print("Seeding wishlist purchase-conversion review dataset into myntra_reviews.db...")
    
    # Insert SKUs
    for sku_id, title, brand, category in SAMPLE_SKUS:
        insert_sku(sku_id, title, brand, category)
        
    # Ingest Reviews through full AI pipeline
    for sku_id, user_id, rating, text, height, weight, build, size, fit in SAMPLE_REVIEWS_DATA:
        insert_user(user_id, f"user_{user_id.lower()}")
        payload = {
            "sku_id": sku_id,
            "user_id": user_id,
            "rating": rating,
            "review_text": text,
            "height_cm": height,
            "weight_kg": weight,
            "body_build": build,
            "size_worn": size,
            "fit_feedback": fit
        }
        ReviewEventPipeline.process_review_submission(payload)
        
    print(f"[OK] Successfully seeded {len(SAMPLE_REVIEWS_DATA)} conversion review records with verified findings & rejected log.")

if __name__ == "__main__":
    seed_database()
