# ---- BlueSentra bootstrap: makes `src.*` imports work in Streamlit ----
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from src.dashboard.theme import inject_global_styles, render_sidebar_brand, render_sidebar_footer
from src.dashboard.views.network_events import render as render_network_events
from src.dashboard.views.prototype_soc import render as render_prototype_soc

DATA_DIR = REPO_ROOT / "src" / "data"

NAV_NETWORK = "Network Events"
NAV_PROTOTYPE = "Prototype Demo"

st.set_page_config(
    page_title="BlueSentra — Local Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_styles()

with st.sidebar:
    render_sidebar_brand()
    st.markdown('<p class="bs-section-label">Navigation</p>', unsafe_allow_html=True)
    view = st.radio(
        "Navigation",
        [NAV_NETWORK, NAV_PROTOTYPE],
        index=0,
        label_visibility="collapsed",
    )
    render_sidebar_footer()

if view == NAV_PROTOTYPE:
    render_prototype_soc(repo_root=REPO_ROOT, data_dir=DATA_DIR)
else:
    render_network_events()
