# Edge Case Management & System Resilience Protocols

> **Document Version:** 1.1.0  
> **Target Audience:** ML Engineers, Backend Developers, Security Auditors, Product Managers  

---

## 1. Overview

In an AI-driven review intelligence engine analyzing existing customer review feeds, system robustness depends on handling edge cases across unstructured natural language, body metric bounds, synthetic spam, image quality, and infrastructure degradation.

This document details the boundary conditions, validation rules, and fallback protocols enforced across the **Myntra AI Existing Review Intelligence Engine**.

---

## 2. Natural Language Processing & Text Edge Cases

### 2.1 Code-Mixed & Multilingual Feeds (Hinglish / Regional Dialects)
* **Challenge:** Existing reviews on Indian fashion platforms frequently mix Hindi and English (*"Fabric bohot soft hai, but length thoda short hai"*).
* **Handling Protocol:**
  - FastText language detector identifies `Hinglish` and routes to code-mixed NLP tokenizer.
  - Normalized dictionary maps common Romanized Hindi terms:
    - `"bohot / bahut"` $\rightarrow$ `Very / High Intensity`
    - `"thoda / thodi"` $\rightarrow$ `Slight / Low Intensity`
    - `"bekaar / kharaab"` $\rightarrow$ `Poor Quality / Negative Polarity`

### 2.2 Sarcasm & Mixed Sentiment Discrepancies
* **Challenge:** Reviews with sarcastic text like *"Great job sending a size M that fits a doll"* paired with 1-star ratings.
* **Handling Protocol:**
  - Calculate **Rating-Sentiment Discrepancy Score**: $\Delta = |Rating\_Norm - Text\_Sentiment\_Score|$.
  - If $\Delta > 0.7$, route review to `moderation_queue` with flag `SENTIMENT_DISCREPANCY`.

### 2.3 Adversarial PII Scrubbing Avoidance
* **Challenge:** Reviewers attempting to leak contact numbers or URLs using spacing tricks (*"9 8 7 6 5 4 3 2 1 0"*, *"test [at] gmail [dot] com"*).
* **Handling Protocol:**
  - Apply text normalization (strip non-alphanumeric spacing between digits) prior to PII regex scanning.
  - Redact phone numbers, emails, handles, and URLs to `[REDACTED_PHONE]`, `[REDACTED_EMAIL]`, etc.

---

## 3. Body Metric & Fit Intelligence Edge Cases

### 3.1 Unrealistic Height & Weight Metric Extraction
* **Boundary Validation Rules:**
  - Height Range: $120.0\,\text{cm} \le \text{Height} \le 220.0\,\text{cm}$ ($\sim 3'11''$ to $7'2''$).
  - Weight Range: $30.0\,\text{kg} \le \text{Weight} \le 200.0\,\text{kg}$ ($\sim 66\,\text{lbs}$ to $440\,\text{lbs}$).
* **Handling Protocol:**
  - If extracted or provided height/weight falls outside boundary range, set metric to `null` and log validation error without discarding the review text.

### 3.2 Imperial vs. Metric System Conversions
* **Imperial Metric Normalization:**
  - Feet/Inches: `5'9"`, `5 feet 9 inches`, `5.9 ft` $\rightarrow$ Convert to `175.26 cm`.
  - Pounds: `150 lbs`, `150 pounds` $\rightarrow$ Convert to `68.04 kg`.

---

## 4. Bot & Synthetic Review Detection Edge Cases

### 4.1 Low Perplexity / Highly Repetitive AI-Generated Text
* **Challenge:** Automated bot networks spamming template reviews (*"Top notch quality product that exceeded my expectations in every way"*).
* **Handling Protocol:**
  - Calculate token entropy $H(X)$ and sentence length variance (burstiness).
  - Reviews with entropy $< 2.5$ and template matches $> 2$ are flagged as `SYNTHETIC_AI` and quarantined.

---

## 5. System Fallback & Degradation Matrix

| Component | Failure Mode | Fallback Protocol |
| :--- | :--- | :--- |
| **Google Gemini AI API** | API Timeout / Rate Limit / Auth Error | Seamlessly fall back to internal rule-based aspect cluster engine |
| **Redis Cache Cluster** | Connection Loss / Cache Down | Direct fallback to PostgreSQL read-replica with circuit breaker |
| **OpenSearch Engine** | Cluster Degradation / High Index Latency | Fallback to SQLite/SQL keyword filtering query |
