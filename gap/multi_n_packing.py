"""
multi_n_packing.py
------------------
Streamlit app: read parsed PO JSON -> build MULTI PACK ( N ) packing list.

    Multi Y  (multi_y_packing.py) : Full Carton = Y  -> 1 prepack  = 1 carton
    Multi N  (this file)          : Full Carton = N  -> N prepacks = 1 carton
                                    (e.g. 247 prepacks, 4 per carton
                                          = 61 CTNS x 4  +  1 CTN x 3)

Excel export mirrors:  Style - 908546 PO - 61429740 - Qty - 6431 Pcs  Multi.xlsx
    Sheet 'PKL' : packing list (live formulas)
    Sheet 'sum' : packing list summary

Run:
    streamlit run multi_n_packing.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from multi_n_core import (
    DEFAULT_CTN_CODE, DEFAULT_CTN_MEAS, DEFAULT_NET_DEDUCT, DEFAULT_NNW,
    DEFAULT_NW, DEFAULT_PREPACKS_PER_CTN, DEFAULT_TARE, build_multi_n,
    is_multi_n, load_json, size_family,
)
from multi_n_export import export_multi_n_excel

st.set_page_config(page_title="Packing List — Multi Pack (N)", layout="wide")
st.title("📦 Packing List — Multi Pack (N)")

DEFAULT_JSON = "61429740.json"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def _init_state():
    if "mn_weights" not in st.session_state:
        st.session_state.mn_weights = pd.DataFrame({
            "SIZE": list(DEFAULT_NW),
            "N.W.": list(DEFAULT_NW.values()),
            "N.N.W.": [DEFAULT_NNW[s] for s in DEFAULT_NW],
        }).set_index("SIZE")
    if "mn_tare" not in st.session_state:
        st.session_state.mn_tare = pd.DataFrame({
            "CTN CODE": list(DEFAULT_TARE),
            "EMPTY CTN WT.": list(DEFAULT_TARE.values()),
        }).set_index("CTN CODE")
    if "mn_meas" not in st.session_state:
        st.session_state.mn_meas = list(DEFAULT_CTN_MEAS)


_init_state()


@st.cache_data(show_spinner=False)
def _load(path: str, mtime: float) -> dict:
    return load_json(path)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    json_path = st.text_input("JSON file path", DEFAULT_JSON)

    st.markdown("### ⚖️ Weight settings (kg)")
    st.session_state.mn_weights = st.data_editor(
        st.session_state.mn_weights, use_container_width=True, num_rows="fixed",
        column_config={
            "N.W.": st.column_config.NumberColumn(format="%.3f", step=0.001),
            "N.N.W.": st.column_config.NumberColumn(format="%.3f", step=0.001),
        },
        key="mn_weights_editor",
    )

    st.markdown("### 📦 Empty carton weight")
    st.session_state.mn_tare = st.data_editor(
        st.session_state.mn_tare, use_container_width=True, num_rows="fixed",
        column_config={"EMPTY CTN WT.": st.column_config.NumberColumn(format="%.3f", step=0.01)},
        key="mn_tare_editor",
    )
    net_deduct = st.number_input("GROSS − NET (MULTI)", value=DEFAULT_NET_DEDUCT,
                                 step=0.01, format="%.2f")

    st.divider()
    default_per_ctn = st.number_input(
        "Prepacks per carton (all prepacks)", min_value=1, max_value=50,
        value=DEFAULT_PREPACKS_PER_CTN, step=1,
        help="247 prepacks ÷ 4 = 61 full cartons + 1 carton of 3.",
    )
    ctn_code = st.selectbox(
        "CTN MES: (carton code)", list(st.session_state.mn_tare.index),
        index=list(st.session_state.mn_tare.index).index(DEFAULT_CTN_CODE)
        if DEFAULT_CTN_CODE in st.session_state.mn_tare.index else 0,
    )

    st.divider()
    st.markdown("### CTN MEAS. (carton dimensions)")
    for i, m in enumerate(st.session_state.mn_meas):
        st.session_state.mn_meas[i] = st.text_input(f"Line {i + 1}", value=m, key=f"mn_meas_{i}")


# ---------------------------------------------------------------------------
# Load + build
# ---------------------------------------------------------------------------
p = Path(json_path)
if not p.exists():
    st.error(f"File not found: `{json_path}`")
    st.stop()

data = _load(str(p), p.stat().st_mtime)
if not any(is_multi_n(t) for t in (data.get("tables") or {}).values()):
    st.warning("No Multi Pack (N) tables (PrePack Type = Multi, Full Carton = N) "
               "found in this JSON.")
    st.stop()

w = st.session_state.mn_weights
nw = {s: float(w.loc[s, "N.W."]) for s in w.index}
nnw = {s: float(w.loc[s, "N.N.W."]) for s in w.index}
tare = {c: float(v) for c, v in st.session_state.mn_tare["EMPTY CTN WT."].items()}

po_header = data.get("PO_HEADER") or {}
buyer = po_header.get("BUYER") or "OLD NAVY"
po_no = po_header.get("P.O._#") or p.stem

# per-prepack "prepacks per carton" overrides (widgets live in each section)
overrides = {}
for t in data["tables"].values():
    if is_multi_n(t):
        pp = str(t["rows"][0].get("PrePack"))
        overrides[pp] = int(st.session_state.get(f"mn_per_ctn_{pp}", default_per_ctn))

sections = build_multi_n(data, nw, tare, net_deduct, int(default_per_ctn),
                         overrides, ctn_code)

# 'NN of TTT' denominator: Multi-N cartons + the PO's Multi-Y / Single / Bulk cartons
# are numbered by their own pages; here we use the sheet's own total unless the
# user sets the PO-wide total.
own_total = sum(s["ctn_total"] for s in sections)
grand_total = st.sidebar.number_input(
    "Total cartons in PO (for 'CARTON 01 of …')", min_value=1, value=int(own_total),
    help="Reference sheet for PO 61429740 shows 177 (Multi 124 + Single 4 + Bulk 49).",
)

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
st.markdown("#### Size / weight reference")
all_sizes = [s for sec in sections for s in sec["sizes"]]
cols = size_family(all_sizes)
ref = pd.DataFrame(
    {"N.W": [nw.get(s) for s in cols], "N.N.W": [nnw.get(s) for s in cols]},
    index=cols,
).T
st.dataframe(ref, use_container_width=True)

for sec in sections:
    st.markdown("---")
    st.markdown(f"<h4 style='text-align:center'>MULTY PACK ( N ) — {sec['color']}</h4>",
                unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(
            f"**BUYER** : {buyer}  \n**STYLE** : {sec['style_full']}  \n"
            f"**P. O. #** : {po_no}  \n**O/QTY** : {sec['qty_ordered']} PCS  \n"
            f"**SHIP QTY** : {sec['ship_qty']} PCS  \n"
            f"**EX/SHORT** : {sec['ship_qty'] - sec['qty_ordered']} PCS  \n"
            f"**CTN QTY** : {sec['ctn_total']} CTNS"
        )
    with c2:
        st.markdown(
            f"**PO #** : {po_no}  \n**SKU / Item** : {sec['style_full']}  \n"
            f"**Unit / Prepack** : {sec['units_per_prepack']}/{sec['per_ctn']}  \n"
            f"**PREPACKS** : {sec['prepackets']}"
        )
        st.number_input(
            f"Prepacks per carton — {sec['prepack']}", min_value=1, max_value=50,
            value=int(sec["per_ctn"]), step=1, key=f"mn_per_ctn_{sec['prepack']}",
        )

    recs = []
    for r in sec["rows"]:
        rec = {
            "CTN NO": f"{r['ctn_from']}-{r['ctn_to']}" if r["ctn_to"] != r["ctn_from"]
            else str(r["ctn_from"]),
            "CTN MES:": r["ctn_mes"], "CTN QTY": r["ctn_qty"],
            "COLOR": sec["color"], "PREPACK STECKER": sec["prepack"],
        }
        for s in sec["sizes"]:
            rec[s] = sec["units"][s]
        rec.update({"PER BLST": r["per_blst"], "QTY PER CTN": r["qty_per_ctn"],
                    "TOTAL QTY": r["total_qty"], "GROSS WEIGHT": r["gross"],
                    "NET WEIGHT": r["net"]})
        recs.append(rec)
    tot = {"CTN NO": "TOTAL", "CTN QTY": f"{sec['ctn_total']} CTNS",
           "TOTAL QTY": f"{sec['ship_qty']} PCS"}
    for s in sec["sizes"]:
        tot[s] = sum(r["ctn_qty"] * r["prepacks_per_ctn"] for r in sec["rows"]) * sec["units"][s]
    recs.append(tot)
    # TOTAL row mixes numbers and text ('62 CTNS') -> show everything as text
    view = pd.DataFrame(recs, dtype=object).fillna("").astype(str)
    st.dataframe(view, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
st.markdown("### Download")
try:
    xlsx = export_multi_n_excel(
        sections, nw, nnw, tare, net_deduct, st.session_state.mn_meas,
        buyer, po_no, int(grand_total),
    )
    st.download_button(
        "⬇ Download Excel (template format)", data=xlsx,
        file_name=f"packing_list_multi_n_{po_no}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
except Exception as e:  # pragma: no cover
    st.error(f"Excel export failed: {e}")
