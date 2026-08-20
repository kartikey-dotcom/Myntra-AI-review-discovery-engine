import streamlit as st
import pandas as pd
import os
import sys

# Ensure root directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from src.config import config
from src.db.database import init_db
from src.services.corpus_analytics import CorpusAnalyticsEngine
from src.services.synthetic_detector import SyntheticTextDetector
from src.services.seller_analytics import SellerAnalyticsEngine
from src.services.event_pipeline import ReviewEventPipeline

# Initialize DB & Seed Data
init_db()

# Streamlit Page Configuration
st.set_page_config(
    page_title="Myntra Wishlist Purchase-Conversion & Review Intelligence Engine",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 800; color: #ff3f6c; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1rem; color: #a1a1aa; margin-bottom: 1.5rem; }
    .card-box { background-color: #18181b; border: 1px solid #27272a; padding: 1.2rem; border-radius: 12px; margin-bottom: 1rem; }
    .quote-style { background: rgba(0,0,0,0.3); border-left: 4px solid #ff3f6c; padding: 0.6rem 1rem; font-style: italic; color: #e4e4e7; margin: 0.5rem 0; }
    .badge-pill { background: rgba(139,92,246,0.2); color: #a78bfa; padding: 0.2rem 0.6rem; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<div class="main-header">Myntra AI Wishlist Purchase-Conversion Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Research Focus: <em>"Why do Myntra users wishlist items and fail to purchase within 30 days — and what moves them to purchase?"</em></div>', unsafe_allow_html=True)

# Sidebar Info
st.sidebar.title("🛍️ Navigation & Control")
st.sidebar.info(f"**Environment:** {config.ENVIRONMENT}\n\n**LLM Provider:** {config.LLM_PROVIDER}\n\n**Model:** {config.GEMINI_MODEL_NAME}")

# Main Tabs for Streamlit UI
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Verified Findings (Click-Traceable)",
    "2. Corpus Stats",
    "3. Stage 3 Verification Rejected Log",
    "4. Dataset Analyzer & Secondary Tools"
])

# ==============================================================================
# TAB 1: VERIFIED FINDINGS (Primary View)
# ==============================================================================
with tab1:
    st.subheader("1. Stage 3 Verified Findings (Click-Traceable Evidence)")
    st.caption("Every claim below has passed Stage 3 adversarial LLM verification against direct quotes in the review corpus.")
    
    findings = CorpusAnalyticsEngine.get_verified_findings(limit=50)
    
    if not findings:
        st.warning("No verified claims found in corpus database.")
    else:
        for idx, item in enumerate(findings):
            with st.container():
                st.markdown(f"""
                <div class="card-box">
                    <span class="badge-pill">{item['category'].replace('_', ' ').upper()}</span>
                    <h4 style="margin-top:0.5rem; color:#ffffff;">"{item['claim_text']}"</h4>
                    <div class="quote-style">"{item['quote']}"</div>
                    <div style="font-size:0.85rem; color:#a1a1aa; display:flex; justify-content:space-between; margin-top:0.5rem;">
                        <span>SKU: <strong>{item['sku_id']}</strong> | Height: {item['height_cm'] or 'N/A'}cm / Weight: {item['weight_kg'] or 'N/A'}kg</span>
                        <span style="color:#ff3f6c; font-weight:700;">Record ID: {item['review_id']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"🔍 Trace Full Raw Review for Record {item['review_id']}"):
                    rec = CorpusAnalyticsEngine.get_record_details(item['review_id'])
                    st.json(rec)

# ==============================================================================
# TAB 2: CORPUS STATS
# ==============================================================================
with tab2:
    st.subheader("2. Multi-Source Review Corpus Statistics")
    st.caption("Reproducible category distribution across 4,420 real customer feedback records.")
    
    stats = CorpusAnalyticsEngine.get_corpus_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Ingested Reviews", f"{stats['total_corpus_reviews']:,}")
    col2.metric("Total Claims Evaluated", f"{stats['total_claims_evaluated']:,}")
    col3.metric("Verification Pass Rate", f"{stats['verification_pass_rate_pct']}%")
    col4.metric("Rejected Claims", f"{stats['rejected_claims_count']:,}")
    
    st.divider()
    st.subheader("🌐 Multi-Source Ingestion Breakdown")
    s_break = stats.get("source_breakdown", {})
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Google Play Store Reviews", f"{s_break.get('Play Store', 0):,}")
    sc2.metric("Apple App Store Reviews", f"{s_break.get('App Store', 0):,}")
    sc3.metric("Reddit Feedback & Discussions", f"{s_break.get('Reddit', 0):,}")

    st.divider()
    st.subheader("Wishlist Purchase-Hesitation Category Breakdown")
    
    breakdown = stats.get("category_breakdown", {})
    df_chart = pd.DataFrame([
        {"Category": cat.replace('_', ' ').title(), "Percentage (%)": data["percentage"], "Count": data["count"]}
        for cat, data in breakdown.items()
    ])
    
    st.bar_chart(df_chart.set_index("Category")["Percentage (%)"])
    st.dataframe(df_chart, use_container_width=True)

# ==============================================================================
# TAB 3: REJECTED LOG
# ==============================================================================
with tab3:
    st.subheader("3. Stage 3 Verification Rejected Log")
    st.caption("Claims that failed the adversarial relevance test ('Does this candidate quote strictly support this claim?'). Strictly non-empty log.")
    
    rejected = CorpusAnalyticsEngine.get_rejected_log(limit=50)
    
    if not rejected:
        st.info("No rejected claims logged.")
    else:
        df_rej = pd.DataFrame([
            {
                "Claim ID": f"#{item['claim_id']}",
                "Category": item['category'].replace('_', ' ').title(),
                "Generated Claim": item['claim_text'],
                "Candidate Quote": item['quote'],
                "Stage 3 Rejection Reason": item['rejection_reason'] or "Failed adversarial verification",
                "Record ID": item['review_id']
            }
            for item in rejected
        ])
        st.dataframe(df_rej, use_container_width=True)

# ==============================================================================
# TAB 4: DATASET ANALYZER & SECONDARY TOOLS
# ==============================================================================
with tab4:
    st.subheader("4. Batch Review Dataset Analyzer & Secondary Tools")
    
    st.markdown("### 📥 Batch Dataset Analyzer")
    batch_sku = st.text_input("Dataset / SKU Name", value="MYN-STREAMLIT-BATCH")
    batch_input = st.text_area("Paste Raw Existing Review Texts (One per line)", value="I kept this dress in my wishlist for 3 weeks because size chart is confusing.\nTracked price in wishlist waiting for discount sale price drop.\nAs an AI language model, I highly recommend this product.")
    
    if st.button("Run Batch AI Analysis", type="primary"):
        lines = [l.strip() for l in batch_input.split("\n") if l.strip()]
        if lines:
            count = 0
            for idx, text in enumerate(lines):
                payload = {
                    "sku_id": batch_sku,
                    "user_id": f"USR-ST-{idx+1:03d}",
                    "rating": 4,
                    "review_text": text
                }
                ReviewEventPipeline.process_review_submission(payload)
                count += 1
            st.success(f"✓ Ingested and analyzed {count} reviews into the wishlist conversion corpus!")
            st.rerun()

    st.divider()
    
    st.markdown("### 🛡️ Synthetic AI Review Detector")
    synth_text = st.text_area("Analyze Review Text Authenticity", value="As an AI language model, I highly recommend purchasing this product.")
    if st.button("Scan Synthetic AI Score"):
        is_synth, score, metrics = SyntheticTextDetector.analyze(synth_text)
        st.write(f"**Synthetic AI Flag:** {'🚨 SYNTHETIC AI DETECTED' if is_synth else '✅ ORGANIC HUMAN TEXT'}")
        st.write(f"**Confidence Score:** {score * 100:.1f}%")
        st.json(metrics)

    st.divider()
    
    st.markdown("### 🏬 Seller Sizing Calibration Portal")
    brand_name = st.text_input("Brand Name", value="Roadster")
    if st.button("Fetch Brand Quality Report"):
        report = SellerAnalyticsEngine.get_brand_analytics(brand_name)
        st.json(report)
