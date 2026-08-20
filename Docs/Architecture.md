# System Architecture: Myntra AI Review Analytics & Intelligence Engine

> **Document Version:** 1.1.0  
> **Target Audience:** System Architects, AI/ML Engineers, Backend Engineers, Product Managers  

---

## 1. High-Level Architecture Overview

The **Myntra AI Review Intelligence Engine** is a high-throughput, low-latency distributed system designed to process existing user-generated reviews (text, images, ratings, and fit feedback) available across public feeds and catalog datasets. It enforces review authenticity, distills aspect-based customer sentiment, extracts body-metric intelligence, and powers real-time UI components across Myntra's mobile and web platforms.

```mermaid
flowchart TD
    subgraph Ingestion & Input Layer
        A1[Catalog Review Feeds]
        A2[Batch CSV / JSON Datasets]
        A3[Public Feedback Feeds]
        A4[Seller Portal Dashboard]
    end

    subgraph API & Gateway Layer
        B1[API Gateway - Kong / AWS API Gateway]
        B2[Authentication & Rate Limiter]
        B3[Redis Low-Latency Cache]
    end

    subgraph Event Streaming & Queue
        C1[Apache Kafka / Event Hub]
        C2[Raw Review Ingestion Topic]
        C3[Analyzed Review Events Topic]
    end

    subgraph Core AI Microservices
        D1[Trust & Safety Engine\nFake / AI Review Detector]
        D2[ABSA & Summarization Engine\nGoogle Gemini AI + ABSA]
        D3[Size & Fit Intelligence Engine\nNER & Fit Delta Calculator]
        D4[Computer Vision Engine\nPhoto Quality & Verification]
    end

    subgraph Data & Storage Layer
        E1[(PostgreSQL / Relational DB\nMetadata & Analysis Records)]
        E2[(Pinecone / Vector DB\nReview & Aspect Embeddings)]
        E3[(OpenSearch / Elasticsearch\nFull-Text Search & Aggregations)]
        E4[(S3 / Blob Storage\nCatalog & User Photos)]
        E5[(Snowflake / BigQuery\nAnalytics & Model Retraining)]
    end

    A1 & A2 & A3 -->|Ingest / Bulk Analyze| B1
    B1 --> B2 --> B3
    B1 -->|Publish Submissions| C1 --> C2
    
    C2 --> D1 & D2 & D3 & D4
    
    D1 & D2 & D3 & D4 -->|Persist Metrics| E1 & E2 & E3 & E4
    D1 & D2 & D3 & D4 -->|Stream Results| C3
    
    C3 -->|Update Cache| B3
    B1 -->|Query Insights| A4
```

---

## 2. Ingestion & Preprocessing Pipeline

### 2.1 Event-Driven Processing Workflow
1. **Feed Ingestion:** Existing review datasets (Star Rating, Review Text, Size Worn, Height/Weight metrics, Garment Photos) are ingested via batch endpoints or Kafka streams.
2. **Gateway Validation:** The API Gateway validates JWT tokens, rate limits batch jobs, and sanitizes input text.
3. **Kafka Ingestion:** The submission event is pushed to `kafka.reviews.raw` with partition key `sku_id` to guarantee ordering per product.
4. **Preprocessing Worker:**
   - **PII Scrubbing:** Redacts phone numbers, emails, or personal handles using Regex and SpaCy entity masking.
   - **Language Identification:** Detects language (English, Hindi, Hinglish) and routes to appropriate NLP tokenization pipelines.

---

## 3. Core AI Microservices Deep-Dive

### 3.1 Trust & Safety Engine (Synthetic & Fake Review Detector)
* **Text Feature Extractor:** Analyzes perplexity, burstiness, and repetitive phrase n-grams to detect synthetic LLM reviews in existing datasets.
* **Rating-Text Sentiment Variance:** Flags reviews where numerical rating (e.g., `5 Stars`) strongly diverges from text sentiment.

### 3.2 Aspect-Based Sentiment Analysis (ABSA) & Gemini Summarization
* **Aspect Extractor (Fine-Tuned Transformer / Lexicon Engine):** Identifies domain categories: `Fabric Quality`, `Color Accuracy`, `Stitching/Durability`, `Transparency`, `Shrinkage`.
* **Google Gemini AI Integration (`gemini-2.5-flash`):** Synthesize aspect clusters into structured pros, cons, and 1-sentence SKU insight cards.

### 3.3 Size & Fit Intelligence Engine
* **Body Metric NER (Named Entity Recognition):** Extracts body metrics from existing review text (e.g., *"5'9 ft"*, *"70 kg"*, *"175cm"*).
* **Fit Delta Classifier:** Categorizes fit feedback into discrete buckets: `Runs Small (-1)`, `True to Size (0)`, `Runs Large (+1)`.

---

## 4. Data Storage & Indexing Architecture

| Storage Layer | Engine | Use Case |
| :--- | :--- | :--- |
| **Relational Store** | SQLite / PostgreSQL | Source of truth for review metadata and SKU summary records |
| **Vector Database** | Pinecone / Qdrant | Dense vector embeddings for semantic review search |
| **Search Engine** | OpenSearch / Elasticsearch | Inverted index document store for faceted height/weight review search |
| **Caching Layer** | Redis Cluster | Sub-50ms query caching for pre-aggregated SKU AI summary cards |
