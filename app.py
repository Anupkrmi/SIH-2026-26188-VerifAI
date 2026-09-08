"""BorderShield AI -- Streamlit console entry point.

Five screens (Command Dashboard, New Screening, Evidence Analysis, Risk
Decision, Investigation), navigated via a fixed sidebar, matching the
Stitch reference design (reference/stitch_bordershield_ai_interface_design/).
Every screen's logic lives in ui/pages.py; this file only wires page
config, session state, and the sidebar nav that switches between them.

Every Attack Wall button (ui/pages.py::render_dashboard) maps to a real,
generated attack (synth/forge.py) run through the actual Trust Ladder
pipeline (core/pipeline.py) -- nothing is staged or faked for the demo.
"""
from __future__ import annotations

import streamlit as st

from ui import actions, pages, screens
from ui.style import inject

st.set_page_config(page_title="BorderShield AI", page_icon="\U0001f6e1️", layout="wide")
inject()

if not actions.GENUINE.exists():
    st.error("No documents found. Run `python -m synth.passport`, `python -m synth.forge`, "
             "and `python -m synth.sign` first.")
    st.stop()

# Self-heals a fresh clone / fresh Streamlit Cloud container: committed
# .sod.json sidecars were signed on whichever machine generated them, and
# data/pki/ (the keys) is gitignored and per-machine -- see
# synth/sign.py::ensure_corpus_signed for what this actually detects and
# why. Guarded so it only runs once per session, not on every rerun.
if "corpus_signed_checked" not in st.session_state:
    from synth.sign import ensure_corpus_signed
    ensure_corpus_signed()
    st.session_state.corpus_signed_checked = True

if "page" not in st.session_state:
    st.session_state.page = "overview"

# Four destinations, each answering a different question: what is
# happening (command), screen this person (new screening), what is wrong
# with THIS case (case file), is the record trustworthy (audit trail).
# The previous five split one case across three of them -- see
# ui/pages.py::render_case for why that was merged.
_NAV_ITEMS = [
    ("overview", "Overview", "info"),
    ("dashboard", "Command", "dashboard"),
    ("capture", "New screening", "person_search"),
    ("case", "Case file", "assignment_ind"),
    ("audit", "Audit trail", "history"),
    ("status", "System status", "monitor_heart"),
]
_LEGACY_PAGES = {"evidence": "case", "risk": "case", "investigation": "audit"}
st.session_state.page = _LEGACY_PAGES.get(st.session_state.page, st.session_state.page)

with st.sidebar:
    st.markdown(screens.sidebar_brand_html(), unsafe_allow_html=True)
    st.markdown(screens.sidebar_identity_html(), unsafe_allow_html=True)
    for page_id, label, icon in _NAV_ITEMS:
        with st.container(key=f"navbtn_{page_id}"):
            if st.button(label, icon=f":material/{icon}:", use_container_width=True, key=f"navbtn_btn_{page_id}"):
                st.session_state.page = page_id
                st.rerun()
    if st.session_state.get("screening_mode_radio") == "Real Document":
        st.markdown(
            "<div class='bsx-nav-note'>Case file and Audit trail cover Demo Document "
            "(Attack Wall) cases. Real Document results appear inline on New "
            "screening, directly under the upload.</div>", unsafe_allow_html=True)

# Highlights whichever nav item is active this rerun. Scoped to a stable,
# self-assigned container key (st.container(key=...)) rather than any of
# Streamlit's own internal button/testid attributes -- those are a version
# implementation detail and have already renamed across releases.
st.markdown(
    f"<style>.st-key-navbtn_{st.session_state.page} button {{ "
    f"color:var(--text) !important; border-left-color:var(--accent) !important; "
    f"font-weight:600 !important; }}</style>",
    unsafe_allow_html=True,
)

_PAGES = {
    "overview": pages.render_landing,
    "dashboard": pages.render_dashboard,
    "capture": pages.render_capture,
    "case": pages.render_case,
    "audit": pages.render_audit,
    "status": pages.render_status,
}
_PAGES.get(st.session_state.page, pages.render_landing)()