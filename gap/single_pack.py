# """
# single_pack.py
# --------------
# Streamlit app: read parsed PO JSON → build SINGLE PACK packing list.
# Each COLOR gets its own separate table.
# """

# import io
# import json
# from pathlib import Path

# import pandas as pd
# import streamlit as st


# st.set_page_config(page_title="Packing List — Single Pack", layout="wide")
# st.title("📦 Packing List — Single Pack")

# DEFAULT_JSON = "61480360.json"
# SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# RIGHT_STATIC = ["QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# @st.cache_data(show_spinner=False)
# def load_json(path: str) -> dict:
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def color_display(raw: str) -> str:
#     if not raw:
#         return ""
#     parts = raw.rsplit(" ", 1)
#     return parts[-1] if len(parts) > 1 else raw


# def build_single_pack_grouped(data: dict) -> dict:
#     groups: dict[str, list] = {}
#     ctn_counter: dict[str, int] = {}

#     for tname, table in data["tables"].items():
#         trows = table.get("rows") or []
#         total = table.get("total") or {}
#         if not trows:
#             continue

#         first = trows[0]
#         if first.get("PrePack Type") != "Single":
#             continue

#         color = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
#         ctn_counter[color] = ctn_counter.get(color, 0) + 1
#         row_no = ctn_counter[color]

#         prepack           = first.get("PrePack")
#         size              = first.get("Size Desc")
#         units_per_prepack = first.get("Units per PrePack")
#         qty_ordered       = first.get("Qty Ordered (eaches)")
#         prepacks_ordered  = total.get("#PrePackets Ordered")

#         data_row = {
#             "CTN NO":          row_no,
#             "CTN MES:":        prepacks_ordered,
#             "CTN QTY":         prepacks_ordered,
#             "COLOR":           color,
#             "PREPACK STECKER": str(prepack),
#         }
#         for s in SIZE_ORDER:
#             data_row[s] = units_per_prepack if s == size else None
#         data_row["QTY PER CTN"]  = units_per_prepack
#         data_row["TOTAL QTY"]    = qty_ordered
#         data_row["GROSS WEIGHT"] = None
#         data_row["NET WEIGHT"]   = None

#         groups.setdefault(color, []).append(data_row)

#     # append TOTAL row per color
#     for color, rows in groups.items():
#         total_packs = sum((r.get("CTN MES:") or 0) for r in rows)
#         total_qty   = sum((r.get("TOTAL QTY") or 0) for r in rows)

#         tot = {
#             "CTN NO":          "TOTAL",
#             "CTN MES:":        None,
#             "CTN QTY":         f"{total_packs} CTNS" if total_packs else None,
#             "COLOR":           None,
#             "PREPACK STECKER": None,
#         }
#         for s in SIZE_ORDER:
#             pieces = sum(
#                 (r.get("TOTAL QTY") or 0)
#                 for r in rows
#                 if r.get(s) is not None
#             )
#             tot[s] = pieces if pieces else None
#         tot["QTY PER CTN"]  = None
#         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
#         tot["GROSS WEIGHT"] = None
#         tot["NET WEIGHT"]   = None
#         rows.append(tot)

#     return groups


# # ===========================================================================
# # UI
# # ===========================================================================
# json_path = st.sidebar.text_input("JSON file path", DEFAULT_JSON)

# if not Path(json_path).exists():
#     st.error(f"File not found: `{json_path}`")
#     st.stop()

# data = load_json(json_path)
# groups = build_single_pack_grouped(data)

# if not groups:
#     st.warning("No Single Pack tables found in the JSON.")
#     st.stop()


# all_frames: list[tuple[str, pd.DataFrame]] = []

# for color, rows in groups.items():
#     present_sizes = [s for s in SIZE_ORDER if any(s in r for r in rows)]
#     columns = LEFT_STATIC + present_sizes + RIGHT_STATIC
#     df = pd.DataFrame(rows).reindex(columns=columns)

#     st.subheader(f"🎨 {color}")
#     st.caption(f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} prepack row(s)")

#     col_cfg = {
#         "CTN NO":          st.column_config.TextColumn("CTN NO", width="small"),
#         "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small"),
#         "CTN QTY":         st.column_config.TextColumn("CTN QTY", width="small"),
#         "COLOR":           st.column_config.TextColumn("COLOR", width="medium"),
#         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium"),
#         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small"),
#         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY", width="small"),
#         "GROSS WEIGHT":    st.column_config.NumberColumn(
#             "GROSS WEIGHT", width="small", format="%.2f"
#         ),
#         "NET WEIGHT":      st.column_config.NumberColumn(
#             "NET WEIGHT", width="small", format="%.2f"
#         ),
#     }
#     for s in present_sizes:
#         col_cfg[s] = st.column_config.NumberColumn(s, width="small")

#     try:
#         edited = st.data_editor(
#             data=df,
#             use_container_width=True,
#             hide_index=True,
#             num_rows="fixed",
#             column_config=col_cfg,
#             key=f"single_editor_{color}",
#         )
#     except TypeError:
#         st.warning(
#             "Your Streamlit version doesn't support data_editor with these options. "
#             "Showing read-only table instead. Upgrade with: pip install -U streamlit"
#         )
#         st.dataframe(df, use_container_width=True, hide_index=True)
#         edited = df

#     all_frames.append((color, edited))
#     st.divider()


# # ===========================================================================
# # Downloads
# # ===========================================================================
# st.markdown("### Download")

# export_rows: list[dict] = []
# for i, (color, frame) in enumerate(all_frames):
#     if i > 0:
#         export_rows.append({})
#     export_rows.extend(frame.to_dict(orient="records"))

# combined = pd.DataFrame(export_rows)

# col1, col2 = st.columns(2)

# with col1:
#     csv = combined.to_csv(index=False).encode("utf-8")
#     st.download_button(
#         "⬇ Download CSV (all colors)",
#         data=csv,
#         file_name="packing_list_single.csv",
#         mime="text/csv",
#         use_container_width=True,
#     )

# with col2:
#     try:
#         buf = io.BytesIO()
#         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
#             for color, frame in all_frames:
#                 sheet = color[:31].replace("/", "-").replace("\\", "-")
#                 frame.to_excel(writer, index=False, sheet_name=sheet)
#         st.download_button(
#             "⬇ Download Excel (one sheet per color)",
#             data=buf.getvalue(),
#             file_name="packing_list_single.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             use_container_width=True,
#         )
#     except ImportError:
#         st.info("Install `openpyxl` to enable Excel export:  pip install openpyxl")


# with st.sidebar:
#     st.markdown("### Colors detected")
#     for color, rows in groups.items():
#         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
#         st.write(f"- **{color}** — {n} prepack row(s)")




"""
single_pack.py
--------------
Streamlit app: read parsed PO JSON → build SINGLE PACK packing list.
Each COLOR gets its own separate section (matching the yellow SINGLE PACK design).
"""

import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from multi_n_core import multi_n_carton_total

# ===========================================================================
# Config
# ===========================================================================
st.set_page_config(page_title="Packing List — Single Pack", layout="wide")
st.title("📦 Packing List — Single Pack")

DEFAULT_JSON = "61480360.json"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# ---- Fixed weight config (kg) ----
DEFAULT_NW    = {"XS": 0.510, "S": 0.520, "M": 0.550, "L": 0.560, "XL": 0.610, "XXL": 0.650, "XXL+": 0.690}
DEFAULT_NNW   = {"XS": 0.490, "S": 0.500, "M": 0.530, "L": 0.540, "XL": 0.590, "XXL": 0.630, "XXL+": 0.670}
DEFAULT_EMPTY = {"XS": 0.49,  "S": 1.00,  "M": 1.00,  "L": 1.00,  "XL": 1.00,  "XXL": 1.00,  "XXL+": 1.00}

# Carton MES per size (from your template's G81 / G82 / G84 / G85 column)
# We assign a deterministic carton type per size for the Single Pack.
SIZE_CTN_MES = {"XS": "G81", "S": "G81", "M": "G81", "L": "G81", "XL": "G81", "XXL": "G81", "XXL+": "G82"}

DEFAULT_CTN_MEAS = [
    "58.67 X 38.48 X 29.71 CM.G8. SL",
    "58.67 X 38.48 X 14.86 CM.G8S. SL",
    "38.48 X 29.33 X 14.86 CM.G-8M",
    "29.33 X 19.25 X 14.86 CM.G-8XS",
    "55.88 X 38.1  X 15.24 CM G13",
]

DEFAULT_BUYER = "OLD NAVY"
DEFAULT_STYLE = "905518-00-1"
DEFAULT_PO_NO = "61480360"

# Multi Pack ends at this number → Single Pack starts at Multi-End + 1
# We auto-detect this by summing Multi Pack "#PrePackets Ordered".
MULTI_PACK_START = 1

LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
RIGHT_STATIC = ["QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# ===========================================================================
# Helpers
# ===========================================================================
@st.cache_data(show_spinner=False)
def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def color_display(raw: str) -> str:
    if not raw:
        return ""
    parts = raw.rsplit(" ", 1)
    return parts[-1] if len(parts) > 1 else raw


def color_code(raw: str) -> str:
    if not raw:
        return "000"
    first = raw.split()[0] if raw.split() else ""
    if "-" in first:
        return first.split("-")[-1]
    return "000"


def _int_or_none(v):
    if v is None:
        return None
    try:
        return int(float(str(v).strip().split()[0]))
    except (TypeError, ValueError, IndexError):
        return None


def _default_weights_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SIZE":          SIZE_ORDER,
            "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
            "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
            "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
        }
    ).set_index("SIZE")


def _init_state():
    if "single_weights_df" not in st.session_state:
        st.session_state.single_weights_df = _default_weights_df()
    if "single_ctn_meas" not in st.session_state:
        st.session_state.single_ctn_meas = list(DEFAULT_CTN_MEAS)
    if "single_ctn_edits" not in st.session_state:
        st.session_state.single_ctn_edits = {}  # { (color, prepack): ctn_qty }


# ===========================================================================
# Multi Pack auto-detect: how many cartons total?
# ===========================================================================
def compute_multi_pack_total(data: dict) -> int:
    """Sum '#PrePackets Ordered' across all Multi Pack (Y) tables."""
    total = 0
    for _, table in data.get("tables", {}).items():
        rows = table.get("rows") or []
        if not rows:
            continue
        first = rows[0]
        if first.get("PrePack Type") == "Multi" and first.get("Full Carton") == "Y":
            total += _int_or_none((table.get("total") or {}).get("#PrePackets Ordered")) or 0
    # Multi Pack (N): several prepacks share a carton -> count real cartons
    total += multi_n_carton_total(data)
    return total


# ===========================================================================
# TOP BLOCK: Title + address + weight reference table
# ===========================================================================
def render_company_header(weights_df: pd.DataFrame) -> None:
    sizes = list(weights_df.index)
    nw_vals  = [f"{float(weights_df.loc[s,'N.W.']):.3f}"    for s in sizes]
    nnw_vals = [f"{float(weights_df.loc[s,'N.N.W.']):.3f}"  for s in sizes]

    size_cells = "".join(f"<th>{s}</th>" for s in sizes)
    nw_cells   = "".join(f"<td>{v}</td>" for v in nw_vals)
    nnw_cells  = "".join(f"<td>{v}</td>" for v in nnw_vals)

    html = f"""
    <style>
      .cc-title {{ text-align:center; font-family:'Courier New',monospace; font-weight:bold;
                   font-size:20px; text-decoration:underline; margin-bottom:2px; }}
      .cc-addr  {{ text-align:center; font-family:'Courier New',monospace; font-weight:bold;
                   font-size:15px; margin-bottom:12px; }}
      .cc-weight-wrap {{ display:flex; justify-content:center; margin-bottom:14px; }}
      .cc-weight {{ border-collapse:collapse; font-family:'Courier New',monospace; font-size:13px; }}
      .cc-weight th, .cc-weight td {{ border:1px solid #000; padding:2px 10px;
                                      text-align:center; min-width:48px; }}
      .cc-weight th.label {{ text-align:left; background:#fff; font-weight:bold; min-width:90px; }}
    </style>
    <div class="cc-title">CREATIVE COLLECTIONS LTD-1A.</div>
    <div class="cc-addr">Nishat Nagar , Tongi , Gazipur .</div>
    <div class="cc-weight-wrap">
      <table class="cc-weight">
        <tr>
          <th class="label">SIZE</th>
          <th class="label">SIZE</th>
          {size_cells}
        </tr>
        <tr>
          <td class="label">N.W</td>
          <td class="label">N.WT</td>
          {nw_cells}
        </tr>
        <tr>
          <td class="label">N.N.W</td>
          <td class="label">N.N.WT</td>
          {nnw_cells}
        </tr>
        <tr>
          <td class="label">EMPTY CTN WET</td>
          <td class="label"></td>
          <td colspan="{len(sizes)}"></td>
        </tr>
      </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ===========================================================================
# Yellow section strip:  SINGLE PACK
# ===========================================================================
def render_section_strip(title: str) -> None:
    html = f"""
    <style>
      .cc-strip {{
        text-align:center; font-family:'Courier New',monospace; font-weight:bold;
        font-size:15px; letter-spacing:2px;
        background:#FFFF00; border:1px solid #000;
        padding:5px 0; margin:16px 0 10px 0;
      }}
    </style>
    <div class="cc-strip">{title}</div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ===========================================================================
# Compact PO header (13-line left + 4-line right)
# ===========================================================================
def render_po_header(
    buyer: str, style: str, po_no: str,
    oiqty: int, ship_qty: int, ex_short: int, ctn_qty: int,
    ctn_meas_list: list, sku_item: str,
    unit_prepack: str, carton_label: str,
) -> None:
    meas_left = "".join(
        f'<div class="po-line"><span class="po-label">CTN MEAS.</span>'
        f'<span class="po-colon">:</span>'
        f'<span class="po-value">{m}</span></div>'
        for m in ctn_meas_list
    )

    html = f"""
    <style>
      .po-wrap {{
        display:grid; grid-template-columns:1.4fr 1fr; gap:20px;
        font-family:'Courier New',monospace; font-size:13.5px; line-height:1.5;
        margin-bottom:10px;
      }}
      .po-line {{ display:flex; align-items:baseline; }}
      .po-label {{ display:inline-block; width:110px; font-weight:bold; }}
      .po-colon {{ width:14px; display:inline-block; text-align:center; }}
      .po-value {{ display:inline-block; }}
      .po-right {{ margin-top:60px; }}
    </style>
    <div class="po-wrap">
      <div class="po-left">
        <div class="po-line"><span class="po-label">BUYER</span><span class="po-colon">:</span><span class="po-value">{buyer}</span></div>
        <div class="po-line"><span class="po-label">STYLE</span><span class="po-colon">:</span><span class="po-value">{style}</span></div>
        <div class="po-line"><span class="po-label">P. O. #</span><span class="po-colon">:</span><span class="po-value">{po_no}</span></div>
        <div class="po-line"><span class="po-label">O/QTY</span><span class="po-colon">:</span><span class="po-value">{oiqty} PCS</span></div>
        <div class="po-line"><span class="po-label">SHIP QTY</span><span class="po-colon">:</span><span class="po-value">{ship_qty} PCS</span></div>
        <div class="po-line"><span class="po-label">EX/SHORT</span><span class="po-colon">:</span><span class="po-value">{ex_short} PCS</span></div>
        <div class="po-line"><span class="po-label">CTN QTY</span><span class="po-colon">:</span><span class="po-value">{ctn_qty} CTNS</span></div>
        {meas_left}
      </div>
      <div class="po-right">
        <div class="po-line"><span class="po-label">PO #</span><span class="po-colon">:</span><span class="po-value">{po_no}</span></div>
        <div class="po-line"><span class="po-label">SKU / Item</span><span class="po-colon">:</span><span class="po-value">{sku_item}</span></div>
        <div class="po-line"><span class="po-label">Unit / Prepack</span><span class="po-colon">:</span><span class="po-value">{unit_prepack}</span></div>
        <div class="po-line"><span class="po-label">CARTON</span><span class="po-colon">:</span><span class="po-value">{carton_label}</span></div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ===========================================================================
# Build Single Pack grouped data
# ===========================================================================
def build_single_pack_grouped(
    data: dict, nw: dict, empty_weights: dict,
    multi_pack_total: int, grand_total_ctn: int,
) -> tuple[dict, dict]:
    """
    Returns (groups, header_map):
      groups[color]       = list of row dicts (data + TOTAL)
      header_map[color]   = { oiqty, ship_qty, ex_short, ctn_qty, ... }
    """
    raw: dict[str, list] = {}

    for tname, table in data["tables"].items():
        trows = table.get("rows") or []
        total = table.get("total") or {}
        if not trows:
            continue
        first = trows[0]
        if first.get("PrePack Type") != "Single":
            continue

        color = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
        raw.setdefault(color, []).append((tname, table))

    # ---- Compute header info per color ----
    header_map: dict[str, dict] = {}
    for color, tables in raw.items():
        oiqty_total = 0
        ship_qty_total = 0
        ex_short_total = 0
        ctn_qty_total = 0
        total_units_per_prepack = 0
        total_prepacks = 0
        first_row = tables[0][1]["rows"][0]
        color_cd = color_code(first_row.get("Universal CC #Color Desc", ""))

        for _, table in tables:
            trows = table.get("rows") or []
            total = table.get("total") or {}
            first_r = trows[0] if trows else {}

            oiqty = _int_or_none(total.get("ORDER QTY")) or _int_or_none(first_r.get("Qty Ordered (eaches)")) or 0
            shipq = _int_or_none(total.get("SHIP QTY"))  or oiqty
            exs   = max(oiqty - shipq, 0)
            cq    = _int_or_none(total.get("#PrePackets Ordered")) or _int_or_none(first_r.get("#PrePackets Ordered")) or 0
            upp   = _int_or_none(first_r.get("Units per PrePack")) or 0

            oiqty_total    += oiqty
            ship_qty_total += shipq
            ex_short_total += exs
            ctn_qty_total  += cq
            total_units_per_prepack += upp
            total_prepacks += cq

        header_map[color] = {
            "color_code": color_cd,
            "oiqty": oiqty_total,
            "ship_qty": ship_qty_total,
            "ex_short": ex_short_total,
            "ctn_qty": ctn_qty_total,
            "total_units_per_prepack": total_units_per_prepack,
            "total_prepacks": total_prepacks,
        }

    # ---- Build rows ----
    groups: dict[str, list] = {}
    global_carton_cursor = multi_pack_total + 1   # continue from Multi Pack

    for color, tables in raw.items():
        rows: list[dict] = []
        # Sort by source table order so carton counter is deterministic
        tables_sorted = sorted(tables, key=lambda kv: kv[0])

        for _, table in tables_sorted:
            trows = table.get("rows") or []
            total = table.get("total") or {}
            if not trows:
                continue

            first = trows[0]
            size  = first.get("Size Desc")
            units = _int_or_none(first.get("Units per PrePack")) or 0
            prepack = str(first.get("PrePack"))
            cq = _int_or_none(total.get("#PrePackets Ordered")) or 0
            if cq <= 0:
                continue

            # ---- carton start/end ----
            ctn_start = global_carton_cursor
            ctn_end   = ctn_start + cq - 1
            global_carton_cursor = ctn_end + 1

            # ---- QTY PER CTN = units × 2 (2 units per prepack) ----
            qty_per_ctn = units * 2

            # ---- TOTAL QTY = CTN QTY × QTY PER CTN ----
            total_qty = cq * qty_per_ctn

            # ---- NET / GROSS per carton ----
            nw_size = nw.get(size, 0.0)
            net_per_carton   = round(qty_per_ctn * nw_size, 2)
            empty_wt         = empty_weights.get(size, 0.0)
            gross_per_carton = round(net_per_carton + empty_wt, 2)

            row = {
                "CTN NO":          ctn_start,   # Column A — start
                "CTN MES:":        ctn_end,     # Column B — end
                "CTN QTY":         cq,
                "COLOR":           color if not rows else "",
                "PREPACK STECKER": prepack,
            }
            for s in SIZE_ORDER:
                row[s] = units if s == size else None
            row["QTY PER CTN"]  = qty_per_ctn
            row["TOTAL QTY"]    = total_qty
            row["GROSS WEIGHT"] = gross_per_carton
            row["NET WEIGHT"]   = net_per_carton
            rows.append(row)

        # ---- TOTAL row ----
        tot_ctn  = sum((r.get("CTN QTY") or 0) for r in rows)
        tot_qty  = sum((r.get("TOTAL QTY") or 0) for r in rows)
        tot_row = {
            "CTN NO":          "TOTAL",
            "CTN MES:":        None,
            "CTN QTY":         f"{tot_ctn} CTN",
            "COLOR":           None,
            "PREPACK STECKER": None,
        }
        for s in SIZE_ORDER:
            pieces = sum((r.get("TOTAL QTY") or 0) for r in rows if r.get(s) is not None)
            tot_row[s] = pieces if pieces else None
        tot_row["QTY PER CTN"]  = None
        tot_row["TOTAL QTY"]    = f"{tot_qty} PCS"
        tot_row["GROSS WEIGHT"] = None
        tot_row["NET WEIGHT"]   = None
        rows.append(tot_row)

        groups[color] = rows

    return groups, header_map


# ===========================================================================
# EXCEL EXPORT — mirrors yellow SINGLE PACK layout
# ===========================================================================
def export_excel_single(
    groups: dict, header_map: dict, weights_df: pd.DataFrame,
    ctn_meas: list, buyer: str, style: str, po_no: str,
    grand_total_ctn: int,
) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "SINGLE PACK"

    thin = Side(style="thin", color="000000")
    med  = Side(style="medium", color="000000")
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)

    font_title   = Font(name="Courier New", size=18, bold=True, underline="single")
    font_addr    = Font(name="Courier New", size=13, bold=True)
    font_section = Font(name="Courier New", size=13, bold=True)
    font_bold    = Font(name="Courier New", size=11, bold=True)
    font_normal  = Font(name="Courier New", size=11)

    align_center = Alignment(horizontal="center", vertical="center")
    align_left   = Alignment(horizontal="left",   vertical="center")

    fill_header = PatternFill("solid", fgColor="D9D9D9")
    fill_yellow = PatternFill("solid", fgColor="FFFF00")
    fill_total  = PatternFill("solid", fgColor="F2F2F2")

    # Column widths
    widths = {
        "A": 8,  "B": 8,  "C": 8,  "D": 8,  "E": 14, "F": 16,
        "G": 7,  "H": 7,  "I": 7,  "J": 7,  "K": 7,  "L": 7,  "M": 8,
        "N": 12, "O": 12, "P": 12, "Q": 12,
    }
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    # Title + address
    ws.merge_cells("A1:Q1")
    ws["A1"] = "CREATIVE COLLECTIONS LTD-1A."
    ws["A1"].font = font_title; ws["A1"].alignment = align_center

    ws.merge_cells("A2:Q2")
    ws["A2"] = "Nishat Nagar , Tongi , Gazipur ."
    ws["A2"].font = font_addr; ws["A2"].alignment = align_center

    # Weight reference
    ws["D4"] = "SIZE"; ws["D4"].font = font_bold; ws["D4"].border = border_all
    ws["F4"] = "SIZE"; ws["F4"].font = font_bold; ws["F4"].border = border_all
    for i, s in enumerate(SIZE_ORDER):
        c = ws.cell(row=4, column=7 + i, value=s)
        c.font = font_bold; c.alignment = align_center; c.border = border_all

    ws["D5"] = "N.W";  ws["D5"].font = font_bold; ws["D5"].border = border_all
    ws["F5"] = "N.WT"; ws["F5"].font = font_bold; ws["F5"].border = border_all
    for i, s in enumerate(SIZE_ORDER):
        c = ws.cell(row=5, column=7 + i, value=float(weights_df.loc[s, "N.W."]))
        c.number_format = "0.000"; c.alignment = align_center; c.border = border_all

    ws["D6"] = "N.N.W";  ws["D6"].font = font_bold; ws["D6"].border = border_all
    ws["F6"] = "N.N.WT"; ws["F6"].font = font_bold; ws["F6"].border = border_all
    for i, s in enumerate(SIZE_ORDER):
        c = ws.cell(row=6, column=7 + i, value=float(weights_df.loc[s, "N.N.W."]))
        c.number_format = "0.000"; c.alignment = align_center; c.border = border_all

    ws["D7"] = "EMPTY CTN WET"; ws["D7"].font = font_bold; ws["D7"].border = border_all

    r = 9
    for color, rows in groups.items():
        hdr = header_map.get(color, {})
        style_code = hdr.get("color_code", "000")
        style_full = f"{DEFAULT_STYLE.rsplit('-', 2)[0]}-{style_code}-1"

        # Yellow section strip
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=17)
        c = ws.cell(row=r, column=1, value="SINGLE PACK")
        c.font = font_section; c.alignment = align_center
        c.fill = fill_yellow
        c.border = Border(top=med, bottom=med)
        r += 1

        # PO header — left block (7 lines + 4 CTN MEAS)
        po_left = [
            ("BUYER",      buyer),
            ("STYLE",      style_full),
            ("P. O. #",    po_no),
            ("O/QTY",      f"{hdr.get('oiqty', 0)} PCS"),
            ("SHIP QTY",   f"{hdr.get('ship_qty', 0)} PCS"),
            ("EX/SHORT",   f"{hdr.get('ex_short', 0)} PCS"),
            ("CTN QTY",    f"{hdr.get('ctn_qty', 0)} CTNS"),
        ]
        left_start = r
        for label, value in po_left:
            ws.cell(row=r, column=1, value=label).font = font_bold
            ws.cell(row=r, column=2, value=":").alignment = align_center
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
            ws.cell(row=r, column=3, value=value).font = font_normal
            r += 1

        # CTN MEAS lines
        for m in ctn_meas[:4]:
            ws.cell(row=r, column=1, value="CTN MEAS.").font = font_bold
            ws.cell(row=r, column=2, value=":").alignment = align_center
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
            ws.cell(row=r, column=3, value=m).font = font_normal
            r += 1

        # PO header — right block (offset by 6 rows)
        right_start = left_start + 6
        first_ctn = rows[0].get("CTN NO", 1) if rows else 1
        po_right = [
            ("PO #",           po_no),
            ("SKU / Item",     style_full),
            ("Unit / Prepack", f"{hdr.get('total_units_per_prepack', 0)}/{hdr.get('total_prepacks', 0)}"),
            ("CARTON",         f"{first_ctn} of {grand_total_ctn}"),
        ]
        rr = right_start
        for label, value in po_right:
            ws.cell(row=rr, column=12, value=label).font = font_bold
            ws.cell(row=rr, column=13, value=":").alignment = align_center
            ws.merge_cells(start_row=rr, start_column=14, end_row=rr, end_column=17)
            ws.cell(row=rr, column=14, value=value).font = font_normal
            rr += 1

        # Main table
        sizes = [s for s in SIZE_ORDER if any(s in row for row in rows)]
        size_cols = len(sizes)
        base_right = 7 + size_cols

        # Header row 1
        left_hdr = ["CTN", "CTN", "CTN", "COLOR", "PREPACK STECKER"]
        for i, h in enumerate(left_hdr):
            c = ws.cell(row=r, column=1 + i, value=h)
            c.font = font_bold; c.alignment = align_center
            c.border = border_all; c.fill = fill_header
        ws.cell(row=r, column=1).value = "CTN"
        ws.cell(row=r, column=2).value = "NO"
        ws.cell(row=r, column=3).value = "MES:"

        ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=7 + size_cols - 1)
        c = ws.cell(row=r, column=7, value="SIZE")
        c.font = font_bold; c.alignment = align_center
        c.border = border_all; c.fill = fill_header
        for i in range(1, size_cols):
            ws.cell(row=r, column=7 + i).border = border_all
            ws.cell(row=r, column=7 + i).fill = fill_header

        right_hdr = ["QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]
        for i, h in enumerate(right_hdr):
            c = ws.cell(row=r, column=base_right + i, value=h)
            c.font = font_bold; c.alignment = align_center
            c.border = border_all; c.fill = fill_header
        r += 1

        # Header row 2 (size labels)
        for i, s in enumerate(sizes):
            c = ws.cell(row=r, column=7 + i, value=s)
            c.font = font_bold; c.alignment = align_center
            c.border = border_all; c.fill = fill_header
        for i in range(6):
            ws.cell(row=r, column=1 + i).border = border_all
            ws.cell(row=r, column=1 + i).fill = fill_header
        for i in range(len(right_hdr)):
            ws.cell(row=r, column=base_right + i).border = border_all
            ws.cell(row=r, column=base_right + i).fill = fill_header
        r += 1

        # Data rows
        for row in rows[:-1]:  # exclude TOTAL
            ws.cell(row=r, column=1, value=row.get("CTN NO")).alignment = align_center
            ws.cell(row=r, column=2, value=row.get("CTN MES:")).alignment = align_center
            ws.cell(row=r, column=3, value=row.get("CTN QTY")).alignment = align_center
            ws.cell(row=r, column=4, value=row.get("CTN MES:") and "" or "").alignment = align_center
            ws.cell(row=r, column=4, value="").alignment = align_center
            ws.cell(row=r, column=5, value=row.get("COLOR", "")).alignment = align_center
            ws.cell(row=r, column=6, value=row.get("PREPACK STECKER", "")).alignment = align_center
            for i, s in enumerate(sizes):
                v = row.get(s)
                if v is not None:
                    ws.cell(row=r, column=7 + i, value=v).alignment = align_center
            ws.cell(row=r, column=base_right + 0, value=row.get("QTY PER CTN")).alignment = align_center
            ws.cell(row=r, column=base_right + 1, value=row.get("TOTAL QTY")).alignment = align_center
            ws.cell(row=r, column=base_right + 2, value=row.get("GROSS WEIGHT")).alignment = align_center
            ws.cell(row=r, column=base_right + 2).number_format = "0.00"
            ws.cell(row=r, column=base_right + 3, value=row.get("NET WEIGHT")).alignment = align_center
            ws.cell(row=r, column=base_right + 3).number_format = "0.00"
            for c_idx in range(1, base_right + 4):
                ws.cell(row=r, column=c_idx).border = border_all
            r += 1

        # TOTAL row
        tot = rows[-1]
        ws.cell(row=r, column=1, value="TOTAL").font = font_bold
        ws.cell(row=r, column=1).alignment = align_center
        ws.cell(row=r, column=1).fill = fill_total
        ws.cell(row=r, column=3, value=tot.get("CTN QTY")).alignment = align_center
        ws.cell(row=r, column=3).fill = fill_total
        for i, s in enumerate(sizes):
            v = tot.get(s)
            if v is not None:
                c = ws.cell(row=r, column=7 + i, value=v)
                c.alignment = align_center; c.fill = fill_total
        ws.cell(row=r, column=base_right + 1, value=tot.get("TOTAL QTY")).alignment = align_center
        ws.cell(row=r, column=base_right + 1).fill = fill_total
        for c_idx in range(1, base_right + 4):
            ws.cell(row=r, column=c_idx).border = border_all
        r += 2

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ===========================================================================
# UI
# ===========================================================================
_init_state()

with st.sidebar:
    st.markdown("### ⚖️ Weight settings (kg)")
    edited_w = st.data_editor(
        st.session_state.single_weights_df,
        use_container_width=True, num_rows="fixed",
        column_config={
            "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
            "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
            "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
        },
        key="single_weights_editor",
    )
    if not edited_w.equals(st.session_state.single_weights_df):
        st.session_state.single_weights_df = edited_w
        st.rerun()

    if st.button("↺ Reset weights", use_container_width=True):
        st.session_state.single_weights_df = _default_weights_df()
        st.rerun()

    st.divider()
    st.markdown("### 📦 CTN MEAS.")
    for i, m in enumerate(st.session_state.single_ctn_meas):
        new_m = st.text_input(f"Line {i+1}", value=m, key=f"single_ctn_meas_{i}")
        if new_m != m:
            st.session_state.single_ctn_meas[i] = new_m

    st.divider()
    json_path = st.text_input("JSON file path", DEFAULT_JSON)


if not Path(json_path).exists():
    st.error(f"File not found: `{json_path}`")
    st.stop()

data = load_json(json_path)

# compute how many cartons Multi Pack already consumed
multi_total = compute_multi_pack_total(data)
GRAND_TOTAL_CTN = multi_total + sum(
    _int_or_none((t.get("total") or {}).get("#PrePackets Ordered")) or 0
    for t in data.get("tables", {}).values()
    if (t.get("rows") or [{}])[0].get("PrePack Type") == "Single"
)

weights = {
    "NW":    {s: float(st.session_state.single_weights_df.loc[s, "N.W."])          for s in st.session_state.single_weights_df.index},
    "EMPTY": {s: float(st.session_state.single_weights_df.loc[s, "EMPTY CTN WT."]) for s in st.session_state.single_weights_df.index},
}

groups, header_map = build_single_pack_grouped(
    data, weights["NW"], weights["EMPTY"], multi_total, GRAND_TOTAL_CTN,
)

if not groups:
    st.warning("No Single Pack tables found in the JSON.")
    st.stop()

po_header = data.get("PO_HEADER", {}) or {}
buyer_fixed = po_header.get("BUYER") or DEFAULT_BUYER
po_no_fixed = po_header.get("P.O._#") or DEFAULT_PO_NO

# ===========================================================================
# Render
# ===========================================================================
render_company_header(st.session_state.single_weights_df)

all_frames: list = []
for color, rows in groups.items():
    sizes = [s for s in SIZE_ORDER if any(s in r for r in rows)]
    columns = LEFT_STATIC + sizes + RIGHT_STATIC
    df = pd.DataFrame(rows).reindex(columns=columns)

    hdr = header_map.get(color, {})
    style_full = f"{DEFAULT_STYLE.rsplit('-', 2)[0]}-{hdr.get('color_code', '000')}-1"
    unit_prepack = f"{hdr.get('total_units_per_prepack', 0)}/{hdr.get('total_prepacks', 0)}"
    first_ctn = rows[0].get("CTN NO", 1) if rows else 1
    carton_label = f"{first_ctn} of {GRAND_TOTAL_CTN}"

    render_section_strip("SINGLE PACK")
    render_po_header(
        buyer=buyer_fixed, style=style_full, po_no=po_no_fixed,
        oiqty=hdr.get("oiqty", 0), ship_qty=hdr.get("ship_qty", 0),
        ex_short=hdr.get("ex_short", 0), ctn_qty=hdr.get("ctn_qty", 0),
        ctn_meas_list=st.session_state.single_ctn_meas[:4],
        sku_item=style_full, unit_prepack=unit_prepack, carton_label=carton_label,
    )

    col_cfg = {
        "CTN NO":          st.column_config.NumberColumn("CTN NO", width="small"),
        "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small"),
        "CTN QTY":         st.column_config.NumberColumn("CTN QTY", width="small"),
        "COLOR":           st.column_config.TextColumn("COLOR", width="medium"),
        "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium"),
        "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small"),
        "TOTAL QTY":       st.column_config.NumberColumn("TOTAL QTY", width="small"),
        "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f"),
        "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT",   width="small", format="%.2f"),
    }
    for s in sizes:
        col_cfg[s] = st.column_config.NumberColumn(s, width="small")

    edited = st.data_editor(
        data=df, use_container_width=True, hide_index=True,
        num_rows="fixed", column_config=col_cfg,
        key=f"single_editor_{color}",
    )
    all_frames.append((color, edited))
    st.divider()


# ===========================================================================
# Downloads
# ===========================================================================
st.markdown("### Download")

export_rows: list[dict] = []
for i, (color, frame) in enumerate(all_frames):
    if i > 0:
        export_rows.append({})
    export_rows.extend(frame.to_dict(orient="records"))
combined = pd.DataFrame(export_rows)

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "⬇ Download CSV (all colors)",
        data=combined.to_csv(index=False).encode("utf-8"),
        file_name="packing_list_single.csv",
        mime="text/csv", use_container_width=True,
    )
with col2:
    try:
        xlsx = export_excel_single(
            groups=groups, header_map=header_map,
            weights_df=st.session_state.single_weights_df,
            ctn_meas=st.session_state.single_ctn_meas,
            buyer=buyer_fixed, style=DEFAULT_STYLE, po_no=po_no_fixed,
            grand_total_ctn=GRAND_TOTAL_CTN,
        )
        st.download_button(
            "⬇ Download Excel (SINGLE PACK format)",
            data=xlsx, file_name="packing_list_single.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Excel export failed: {e}")


with st.sidebar:
    st.markdown("### Colors detected")
    for color, rows in groups.items():
        n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
        st.write(f"- **{color}** — {n} prepack row(s)")