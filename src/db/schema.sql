-- Schema for Myntra AI Review Engine (PostgreSQL / SQLite Compatible)

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    account_age_days INTEGER DEFAULT 0,
    total_reviews_submitted INTEGER DEFAULT 0,
    is_verified_purchaser INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skus (
    sku_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    fit_type TEXT DEFAULT 'REGULAR', -- REGULAR, OVERSIZED, SLIM, MATERNITY
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    sku_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    raw_text TEXT NOT NULL,
    sanitized_text TEXT NOT NULL,
    detected_language TEXT DEFAULT 'en',
    
    -- Body & Fit Metrics
    height_cm REAL,
    weight_kg REAL,
    body_build TEXT, -- SLIM, ATHLETIC, REGULAR, HEAVY
    size_worn TEXT,   -- S, M, L, XL, XXL
    fit_feedback TEXT, -- RUNS_SMALL, TRUE_TO_SIZE, RUNS_LARGE
    
    -- Moderation & Pipeline Metadata
    moderation_status TEXT DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED, QUARANTINED
    pii_redacted INTEGER DEFAULT 0,
    is_synthetic INTEGER DEFAULT 0,
    synthetic_confidence REAL DEFAULT 0.0,
    source_platform TEXT DEFAULT 'Play Store',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS moderation_queue (
    queue_id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    variance_score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'OPEN', -- OPEN, RESOLVED, DISMISSED
    assigned_to TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(review_id)
);

CREATE TABLE IF NOT EXISTS sku_fit_summaries (
    sku_id TEXT PRIMARY KEY,
    total_reviews INTEGER DEFAULT 0,
    avg_rating REAL DEFAULT 0.0,
    runs_small_count INTEGER DEFAULT 0,
    true_to_size_count INTEGER DEFAULT 0,
    runs_large_count INTEGER DEFAULT 0,
    ai_summary_text TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
);

CREATE TABLE IF NOT EXISTS conversion_claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL,
    sku_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    quote TEXT NOT NULL,
    verification_status TEXT NOT NULL, -- VERIFIED, REJECTED
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(review_id)
);
