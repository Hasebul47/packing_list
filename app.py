"""
Unified PO -> Packing List router
=================================
One upload box. Page 1 of the PDF is read to find the buyer:
  * VF / Vans       -> runs vans/vans_app.py  (run(pdf) if present, else as a script)
  * GAP / Old Navy  -> runs gap/gap_app.py  run(pdf)  (your GAP project)
Neither app's code is edited. The router only hands them the uploaded PDF.

Run:  streamlit run app.py
"""
import importlib
import io
import runpy
import sys
from pathlib import Path

import pdfplumber
import streamlit as st

BASE = Path(__file__).resolve().parent
APPS = {
    "VF": (BASE / "vans" / "vans_app.py", BASE / "vans", "VF (Vans)"),
    "GAP": (BASE / "gap" / "gap_app.py", BASE / "gap", "GAP (Old Navy)"),
}

st.set_page_config(page_title="PO -> Packing List", layout="wide", page_icon="📦")


def detect_buyer(pdf_bytes: bytes):
    """Return 'VF', 'GAP' or None, from page 1 text only."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        t = (pdf.pages[0].extract_text() or "").upper()
    if "VF OUTDOOR" in t or ("VANS" in t and "BUYER CODE" in t):
        return "VF"
    if "OLD NAVY" in t or "GAP INTL" in t or "DESTINATION PURCHASE ORDER" in t:
        return "GAP"
    return None


def run_app(key, pdf_file):
    script, folder, _ = APPS[key]
    if not script.exists():
        st.error(f"Missing file: {script}")
        st.stop()

    # Fresh state when the buyer changes (the two apps use different keys)
    if st.session_state.get("_active_buyer") != key:
        for k in list(st.session_state.keys()):
            if not k.startswith(("_active_buyer", "router_")):
                st.session_state.pop(k, None)
        st.session_state["_active_buyer"] = key

    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

    # Preferred: the app is a real module exposing run(pdf_file).
    if "def run(" in script.read_text(encoding="utf-8"):
        mod = importlib.import_module(script.stem)
        mod = importlib.reload(mod) if st.session_state.get("router_reload") else mod
        mod.run(pdf_file)
        return

    # Fallback for a plain top-level Streamlit script (e.g. Vans app.py not yet converted):
    # make set_page_config a no-op and feed it the router's PDF instead of its own uploader.
    real_cfg, real_up = st.set_page_config, st.file_uploader

    def fake_uploader(label, type=None, *a, **kw):
        if type and [str(x).lower() for x in type] == ["pdf"]:
            return pdf_file
        return real_up(label, type=type, *a, **kw)

    st.set_page_config = lambda *a, **kw: None
    st.file_uploader = fake_uploader
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        st.set_page_config, st.file_uploader = real_cfg, real_up


st.title("📦 PO to Packing List")
c1, c2 = st.columns([3, 1])
with c1:
    up = st.file_uploader("Upload PO PDF (VF/Vans or GAP/Old Navy)", type=["pdf"], key="router_pdf")
with c2:
    override = st.selectbox("Buyer", ["Auto-detect", "VF (Vans)", "GAP (Old Navy)"], key="router_override")

buyer = {"VF (Vans)": "VF", "GAP (Old Navy)": "GAP"}.get(override)

if up is not None:
    if buyer is None:
        try:
            buyer = detect_buyer(up.getvalue())
        except Exception as e:
            st.error(f"Could not read the PDF: {e}")
            st.stop()
    if buyer is None:
        st.warning("Could not recognise the buyer. Pick VF (Vans) or GAP (Old Navy) in the Buyer box.")
        st.stop()
    st.success(f"Detected buyer: **{APPS[buyer][2]}**" if override == "Auto-detect"
               else f"Buyer set manually: **{APPS[buyer][2]}**")
    st.divider()
    run_app(buyer, up)
elif buyer == "GAP":
    # lets the GAP app's "load an existing JSON" option work without a PDF
    st.divider()
    run_app("GAP", None)
else:
    st.info("Upload a PO PDF to get started.")
