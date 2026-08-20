import streamlit as st
import streamlit.components.v1 as components
import threading
import time
import uvicorn
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

from src.config import config
from src.db.database import init_db

# Load Secrets into os.environ if running on Streamlit Cloud
if hasattr(st, "secrets"):
    for key, val in st.secrets.items():
        if isinstance(val, str) or isinstance(val, (int, float, bool)):
            os.environ[key] = str(val)

def run_fastapi_server():
    init_db()
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, log_level="warning")

# Start FastAPI server in a background daemon thread if not already running
if "server_started" not in st.session_state:
    st.session_state["server_started"] = True
    thread = threading.Thread(target=run_fastapi_server, daemon=True)
    thread.start()
    time.sleep(2)  # Give server 2 seconds to initialize

# Streamlit Page Config
st.set_page_config(
    page_title="Myntra Wishlist Purchase-Conversion AI Engine",
    page_icon="🛍️",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 100%; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Render Live Web Application UI inside Streamlit Frame
ui_url = "http://127.0.0.1:8000"
components.iframe(ui_url, height=920, scrolling=True)
