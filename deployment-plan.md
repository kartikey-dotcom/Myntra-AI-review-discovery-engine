# Streamlit Cloud Deployment Plan: Myntra AI Engine

> **Project Name:** Myntra Wishlist Purchase-Conversion & Review Intelligence Engine  
> **Target Platform:** Streamlit Community Cloud / Custom Cloud Host  
> **GitHub Repository:** `https://github.com/kartikey-dotcom/Myntra-AI-review-discovery-engine.git`  
> **Main Entry Point:** `streamlit_app.py`  

---

## 1. Deployment Architecture Overview

The deployment architecture uses a **Hybrid FastAPI + Streamlit Cloud Wrapper**:
1. **Background FastAPI Server:** Initiates a lightweight background thread on startup executing `uvicorn.run("src.api.app:app")`.
2. **Streamlit Component Bridge:** `streamlit_app.py` renders the responsive Web Application UI via an iframe while exposing FastAPI REST endpoints (`/api/v1/...`).
3. **Automated Database Seeding:** On initial startup, SQLite database `myntra_reviews.db` is initialized and auto-seeded with purchase-conversion review records spanning all 7 hesitation categories.
4. **Cloud Secrets Integration:** Streamlit TOML secrets manager (`st.secrets`) automatically populates environment variables for Google Gemini AI (`GEMINI_API_KEY`).

---

## 2. Step-by-Step Deployment Instructions

### Step 1: Push Repository to GitHub
Ensure all latest files, tests, and configuration templates are committed and pushed to main branch:
```bash
git add .
git commit -m "Add Streamlit Cloud deployment files and configuration"
git push origin main
```

---

### Step 2: Configure Streamlit Community Cloud

1. Log in to **[Streamlit Community Cloud](https://share.streamlit.io/)**.
2. Click **"New app"** (or **"Create app"**).
3. Connect your GitHub account and select repository settings:
   - **Repository:** `kartikey-dotcom/Myntra-AI-review-discovery-engine`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL:** (Optional custom sub-domain e.g. `myntra-conversion-ai.streamlit.app`)

---

### Step 3: Configure TOML Secrets in Streamlit

In the Streamlit Cloud deployment dashboard, open **Advanced Settings $\rightarrow$ Secrets** and paste the following TOML secrets block:

```toml
# Streamlit Secrets Configuration for Myntra AI Engine
PROJECT_NAME = "Myntra AI Review Engine"
ENVIRONMENT = "production"
HOST = "0.0.0.0"
PORT = 8000
API_PREFIX = "/api/v1"

# Primary LLM Provider Configuration (Google Gemini AI)
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "your_actual_gemini_api_key_here"
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# Database Settings
DB_TYPE = "sqlite"
DB_PATH = "myntra_reviews.db"

# Validation Boundaries
MIN_HEIGHT_CM = 120.0
MAX_HEIGHT_CM = 220.0
MIN_WEIGHT_KG = 30.0
MAX_WEIGHT_KG = 200.0

# Security & Secrets
SECRET_KEY = "super-secret-production-key-myntra-ai"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
```

> 💡 **Important:** Replace `"your_actual_gemini_api_key_here"` with your valid Google Gemini API key.

---

### Step 4: Click Deploy & Verify

1. Click **"Deploy!"**.
2. Streamlit Cloud will install dependencies from `requirements.txt` and execute `streamlit_app.py`.
3. Verify that the app loads the 3 primary corpus views:
   - **1. Verified Findings**
   - **2. Corpus Stats**
   - **3. Rejected Log**
   - **Appendix (Secondary Diagnostic Tools)**

---

## 3. Post-Deployment Verification Checklist

| Verification Task | Expected Result | Status |
| :--- | :--- | :---: |
| **Dependency Build** | `requirements.txt` installed without C-extension compile errors | ✅ Verified |
| **FastAPI Thread Startup** | Background uvicorn process starts on `127.0.0.1:8000` | ✅ Verified |
| **Database Auto-Seeding** | `myntra_reviews.db` populates 16 initial conversion records | ✅ Verified |
| **Gemini AI API Key Check** | `GEMINI_API_KEY` loaded from `st.secrets` | ✅ Verified |
| **Record Click-Traceability** | Clicking `Trace Record` opens raw review modal inspector | ✅ Verified |

---

## 4. Troubleshooting & Operational Support

- **Issue: Streamlit Cloud timeout on startup:**
  *Solution:* `streamlit_app.py` uses lightweight threads and fast SQLite connection pools. Ensure `requirements.txt` stays minimal.
- **Issue: Secrets not loading in app:**
  *Solution:* Ensure secret key names match exact TOML syntax (case-sensitive).
