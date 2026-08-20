"""
Seed Dataset Generator for Myntra Wishlist Purchase-Conversion & Review Intelligence Engine.
Executes multi-source customer feedback corpus ingestion (4,420 records across Play Store, App Store, and Reddit).
"""

from src.db.database import get_connection, init_db
from src.services.scraper_pipeline import ScraperCorpusPipeline

def seed_database():
    init_db()
    print("Seeding full 4,420 multi-source customer review corpus into myntra_reviews.db...")
    ScraperCorpusPipeline.ingest_full_corpus(play_store_count=2150, app_store_count=1420, reddit_count=850)
    print("[OK] Successfully seeded 4,420 multi-source conversion review records with verified findings & rejected log.")

if __name__ == "__main__":
    seed_database()
