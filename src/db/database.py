import sqlite3
import os
from typing import Optional, List, Dict, Any
from src.config import config

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables from schema.sql if not exists."""
    schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        # Create review_aspects table if not present
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS review_aspects (
                aspect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id TEXT NOT NULL,
                sku_id TEXT NOT NULL,
                aspect_name TEXT NOT NULL,
                snippet TEXT NOT NULL,
                polarity TEXT NOT NULL,
                sentiment_score REAL DEFAULT 0.5,
                FOREIGN KEY (review_id) REFERENCES reviews(review_id)
            )
            """
        )
        # Create conversion_claims table if not present
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversion_claims (
                claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id TEXT NOT NULL,
                sku_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                claim_text TEXT NOT NULL,
                quote TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (review_id) REFERENCES reviews(review_id)
            )
            """
        )
        conn.commit()
        
        # Check if DB is empty and auto-seed initial dataset (Skip during pytest)
        if "PYTEST_CURRENT_TEST" not in os.environ:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM reviews")
            count = cursor.fetchone()["count"]
            if count == 0:
                conn.close()
                from src.db.seed_data import seed_database
                seed_database()
                return
    finally:
        try:
            conn.close()
        except Exception:
            pass

def insert_sku(sku_id: str, title: str = "Generic Item", brand: str = "Myntra Brand", category: str = "Apparel", fit_type: str = "REGULAR"):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO skus (sku_id, title, brand, category, fit_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sku_id, title, brand, category, fit_type)
        )
        conn.commit()
    finally:
        conn.close()

def insert_user(user_id: str, username: str = "user", account_age_days: int = 30, is_verified: int = 1):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (user_id, username, account_age_days, is_verified_purchaser)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username, account_age_days, is_verified)
        )
        conn.commit()
    finally:
        conn.close()

def save_review(review_data: Dict[str, Any]) -> str:
    conn = get_connection()
    try:
        # Ensure SKU and User exist
        conn.execute(
            "INSERT OR IGNORE INTO skus (sku_id, title, brand, category) VALUES (?, 'Generic Item', 'Myntra Brand', 'Apparel')",
            (review_data["sku_id"],)
        )
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, account_age_days, is_verified_purchaser) VALUES (?, 'user', 30, 1)",
            (review_data["user_id"],)
        )
        
        conn.execute(
            """
            INSERT INTO reviews (
                review_id, sku_id, user_id, rating, raw_text, sanitized_text,
                detected_language, height_cm, weight_kg, body_build, size_worn,
                fit_feedback, moderation_status, pii_redacted, is_synthetic, synthetic_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_data["review_id"],
                review_data["sku_id"],
                review_data["user_id"],
                review_data["rating"],
                review_data["raw_text"],
                review_data["sanitized_text"],
                review_data.get("detected_language", "en"),
                review_data.get("height_cm"),
                review_data.get("weight_kg"),
                review_data.get("body_build"),
                review_data.get("size_worn"),
                review_data.get("fit_feedback"),
                review_data.get("moderation_status", "APPROVED"),
                review_data.get("pii_redacted", 0),
                review_data.get("is_synthetic", 0),
                review_data.get("synthetic_confidence", 0.0)
            )
        )
        
        # Save aspect extraction results if present
        aspects = review_data.get("extracted_aspects", [])
        for asp in aspects:
            aspect_name = asp.get("aspect_name") or asp.get("aspect", "General")
            snippet = asp.get("snippet", "")
            polarity = asp.get("polarity", "POSITIVE")
            sentiment_score = asp.get("sentiment_score", 0.5)
            conn.execute(
                """
                INSERT INTO review_aspects (review_id, sku_id, aspect_name, snippet, polarity, sentiment_score)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (review_data["review_id"], review_data["sku_id"], aspect_name, snippet, polarity, sentiment_score)
            )
        
        # Update SKU summary statistics
        update_sku_summary(conn, review_data["sku_id"])
        
        conn.commit()
        return review_data["review_id"]
    finally:
        conn.close()

def save_conversion_claims(claims: List[Dict[str, Any]]):
    if not claims:
        return
    conn = get_connection()
    try:
        for cl in claims:
            conn.execute(
                """
                INSERT INTO conversion_claims (review_id, sku_id, user_id, category, claim_text, quote, verification_status, rejection_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cl["review_id"],
                    cl["sku_id"],
                    cl["user_id"],
                    cl["category"],
                    cl["claim_text"],
                    cl["quote"],
                    cl["verification_status"],
                    cl.get("rejection_reason")
                )
            )
        conn.commit()
    finally:
        conn.close()

def update_sku_summary(conn: sqlite3.Connection, sku_id: str):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            COUNT(*) as total,
            AVG(rating) as avg_r,
            SUM(CASE WHEN fit_feedback = 'RUNS_SMALL' THEN 1 ELSE 0 END) as small_c,
            SUM(CASE WHEN fit_feedback = 'TRUE_TO_SIZE' THEN 1 ELSE 0 END) as true_c,
            SUM(CASE WHEN fit_feedback = 'RUNS_LARGE' THEN 1 ELSE 0 END) as large_c
        FROM reviews
        WHERE sku_id = ? AND moderation_status = 'APPROVED'
        """,
        (sku_id,)
    )
    row = cursor.fetchone()
    if row and row["total"] > 0:
        total = row["total"]
        avg_r = round(row["avg_r"] or 0.0, 2)
        small_c = row["small_c"] or 0
        true_c = row["true_c"] or 0
        large_c = row["large_c"] or 0
        
        conn.execute(
            """
            INSERT OR REPLACE INTO sku_fit_summaries (
                sku_id, total_reviews, avg_rating, runs_small_count, true_to_size_count, runs_large_count, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (sku_id, total, avg_r, small_c, true_c, large_c)
        )

def get_reviews_for_sku(sku_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM reviews
            WHERE sku_id = ? AND moderation_status = 'APPROVED'
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (sku_id, limit, offset)
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def get_sku_aspects(sku_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM review_aspects WHERE sku_id = ?", (sku_id,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def get_sku_summary(sku_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sku_fit_summaries WHERE sku_id = ?", (sku_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def push_to_moderation_queue(review_id: str, reason: str, variance_score: float = 0.0):
    conn = get_connection()
    try:
        queue_id = f"mod_{review_id}"
        conn.execute(
            """
            INSERT OR REPLACE INTO moderation_queue (queue_id, review_id, reason, variance_score, status)
            VALUES (?, ?, ?, ?, 'OPEN')
            """,
            (queue_id, review_id, reason, variance_score)
        )
        conn.commit()
    finally:
        conn.close()
