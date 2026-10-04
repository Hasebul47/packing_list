


# # """
# # po_app.py
# # ---------
# # Streamlit app: PDF → Raw Text → JSON

# # - pdfplumber দিয়ে PDF থেকে টেক্সট বের করে
# # - corrected parser দিয়ে সেটিকে structured JSON বানায়
# # - raw text এবং JSON — দুটোই ডাউনলোড করা যায়
# # """

# # import io
# # import re
# # import json
# # import streamlit as st
# # import pdfplumber


# # # ===========================================================================
# # # 1. Shared column schema
# # # ===========================================================================
# # COLUMNS = [
# #     "Dept",
# #     "Style No",
# #     "Full Carton",
# #     "PrePack",
# #     "PrePack Type",
# #     "PrePack Pack Factor",
# #     "Sku",
# #     "Units per PrePack",
# #     "Style Description",
# #     "Item Carton Pack Factor",
# #     "Qty Ordered (eaches)",
# #     "#PrePackets Ordered",
# #     "Universal CC #Color Desc",
# #     "Size Desc",
# #     "Unit Cost",
# #     "Total Cost",
# # ]


# # # ===========================================================================
# # # 2. Lines that must never be treated as a color name
# # # ===========================================================================
# # IGNORE_PATTERNS = [
# #     "Print Date", "OLD NAVY", "61480360", "Global Reference", "Market:",
# #     "Market Channel", "Department:", "Destination Purchase Order", "Vendor",
# #     "Factory", "Agent Name", "Payment Type", "Payment Terms", "Payment Method",
# #     "Purchaser Currency", "Contract Ship", "Ship Cancel", "Terms of Sale",
# #     "Freight Paid By", "Transfer Point", "Special Instructions", "Ship Mode",
# #     "Country of Origin", "Country of Destination", "Powered by Infor Nexus",
# #     "Dept Style No", "Total Units", "Total BULK", "Total SINGLE", "Total MULTIPLE",
# #     "Total ASSORTED", "GRAND TOTAL", "THIS PURCHASE ORDER", "1 THIS EDI",
# #     "2 VENDOR SHALL", "3 NOTHWITHSTANDING", "4 PLEASE PUT", "5 THE TRACEABILITY",
# #     "6 A VARIANCE", "NOTE: FOR VENDORS", "=====",
# # ]


# # def is_color_name(line: str) -> bool:
# #     """Return True if the line looks like an all-uppercase color description."""
# #     if not line or not line.strip():
# #         return False
# #     s = line.strip()
# #     if not s.isupper():
# #         return False
# #     if not all(c.isalpha() or c.isspace() for c in s):
# #         return False
# #     for pat in IGNORE_PATTERNS:
# #         if pat in s:
# #             return False
# #     return True


# # # ===========================================================================
# # # 3. Item row parser
# # # ===========================================================================
# # def parse_line_item(line: str):
# #     """Parse a single '3340 ...' line into a row dict."""
# #     tokens = line.split()
# #     dept = tokens[0]
# #     style_no = tokens[1]
# #     idx = 2

# #     full_carton = None
# #     if idx < len(tokens) and tokens[idx] in ("N", "Y"):
# #         full_carton = tokens[idx]
# #         idx += 1

# #     prepack = tokens[idx]; idx += 1
# #     prepack_type = tokens[idx]; idx += 1

# #     prepack_pack_factor = None
# #     if idx < len(tokens) and tokens[idx].isdigit():
# #         prepack_pack_factor = int(tokens[idx]); idx += 1

# #     sku = tokens[idx]; idx += 1

# #     units_per_prepack = tokens[idx]
# #     if units_per_prepack.isdigit():
# #         units_per_prepack = int(units_per_prepack)
# #     idx += 1

# #     # Style Description: collect alphabetic tokens until a numeric token
# #     style_desc_tokens = []
# #     while idx < len(tokens):
# #         tok = tokens[idx]
# #         if re.fullmatch(r'\d+', tok.replace(',', '')):
# #             break
# #         style_desc_tokens.append(tok)
# #         idx += 1
# #     style_description = " ".join(style_desc_tokens)

# #     remaining = len(tokens) - idx
# #     item_carton_pack_factor = None
# #     qty_ordered = None

# #     if remaining == 6:
# #         item_carton_pack_factor = int(tokens[idx])
# #         qty_ordered = int(tokens[idx + 1])
# #         idx += 2
# #     elif remaining == 5:
# #         qty_ordered = int(tokens[idx])
# #         idx += 1
# #     else:
# #         qty_ordered = int(tokens[idx])
# #         idx += 1

# #     color_code = tokens[idx]; idx += 1
# #     size = tokens[idx]; idx += 1
# #     unit_cost = float(tokens[idx].replace(',', '')); idx += 1
# #     total_cost = float(tokens[idx].replace(',', ''))

# #     return {
# #         "Dept": dept,
# #         "Style No": style_no,
# #         "Full Carton": full_carton,
# #         "PrePack": prepack,
# #         "PrePack Type": prepack_type,
# #         "PrePack Pack Factor": prepack_pack_factor,
# #         "Sku": sku,
# #         "Units per PrePack": units_per_prepack,
# #         "Style Description": style_description,
# #         "Item Carton Pack Factor": item_carton_pack_factor,
# #         "Qty Ordered (eaches)": qty_ordered,
# #         "#PrePackets Ordered": None,
# #         "Universal CC #Color Desc": color_code,
# #         "Size Desc": size,
# #         "Unit Cost": unit_cost,
# #         "Total Cost": total_cost,
# #     }


# # # ===========================================================================
# # # 4. Total row parser
# # # ===========================================================================
# # def parse_total(line: str):
# #     """
# #     5 tokens → Bulk total   : style filled, PrePack = null
# #     6 tokens → PrePack total: style = null, PrePack filled
# #     """
# #     tokens = line.split()
# #     if len(tokens) < 2 or not tokens[1].isdigit():
# #         return None

# #     if len(tokens) == 5:
# #         return {
# #             "style": int(tokens[1]),
# #             "PrePack": None,
# #             "PrePack Pack Factor": None,
# #             "Qty Ordered (eaches)": int(tokens[2]),
# #             "#PrePackets Ordered": None,
# #             "Universal CC #Color Desc": tokens[3],
# #             "Total Cost": float(tokens[4].replace(',', '')),
# #         }
# #     elif len(tokens) == 6:
# #         return {
# #             "style": None,
# #             "PrePack": int(tokens[1]),
# #             "PrePack Pack Factor": int(tokens[2]),
# #             "Qty Ordered (eaches)": int(tokens[3]),
# #             "#PrePackets Ordered": int(tokens[4]),
# #             "Universal CC #Color Desc": None,
# #             "Total Cost": float(tokens[5].replace(',', '')),
# #         }
# #     return None


# # # ===========================================================================
# # # 5. Main parser
# # # ===========================================================================
# # def parse_text(text: str) -> dict:
# #     lines = text.splitlines()
# #     tables = []
# #     current_rows = []
# #     i = 0

# #     while i < len(lines):
# #         line = lines[i].strip()

# #         if line.startswith("3340 "):
# #             row = parse_line_item(line)
# #             # look ahead for color name
# #             if i + 1 < len(lines):
# #                 nxt = lines[i + 1].strip()
# #                 if is_color_name(nxt):
# #                     row["Universal CC #Color Desc"] = (
# #                         row["Universal CC #Color Desc"] + " " + nxt
# #                     )
# #                     i += 1
# #             current_rows.append(row)

# #         elif line.startswith("Total "):
# #             total = parse_total(line)
# #             if total is not None:
# #                 # look ahead for color name (Bulk totals only)
# #                 if i + 1 < len(lines):
# #                     nxt = lines[i + 1].strip()
# #                     if is_color_name(nxt) and total["Universal CC #Color Desc"] is not None:
# #                         total["Universal CC #Color Desc"] = (
# #                             total["Universal CC #Color Desc"] + " " + nxt
# #                         )
# #                         i += 1

# #                 # propagate #PrePackets Ordered into Single/Multi rows
# #                 for row in current_rows:
# #                     if row["PrePack Type"] in ("Single", "Multi"):
# #                         if total.get("#PrePackets Ordered") is not None:
# #                             row["#PrePackets Ordered"] = total["#PrePackets Ordered"]

# #                 tables.append({"rows": current_rows, "total": total})
# #                 current_rows = []

# #         i += 1

# #     return {
# #         "columns": COLUMNS,
# #         "tables": {f"table {idx + 1}": t for idx, t in enumerate(tables)},
# #     }


# # # ===========================================================================
# # # 6. PDF → Text
# # # ===========================================================================
# # def extract_text(file_obj) -> str:
# #     with pdfplumber.open(file_obj) as pdf:
# #         return "\n".join(
# #             f"===== PAGE {i} =====\n{page.extract_text() or ''}\n"
# #             for i, page in enumerate(pdf.pages, start=1)
# #         )


# # # ===========================================================================
# # # 7. Cached wrappers
# # # ===========================================================================
# # @st.cache_data(show_spinner=False)
# # def cached_extract(file_bytes: bytes) -> str:
# #     return extract_text(io.BytesIO(file_bytes))


# # @st.cache_data(show_spinner=False)
# # def cached_parse(text: str) -> dict:
# #     return parse_text(text)


# # # ===========================================================================
# # # 8. Streamlit UI
# # # ===========================================================================
# # st.set_page_config(page_title="PO PDF Extractor", layout="wide")
# # st.title("PO PDF Extractor")
# # st.caption("PDF → Raw Text → JSON")

# # uploaded = st.file_uploader("Upload a PDF", type=["pdf"])

# # if uploaded is not None:
# #     file_bytes = uploaded.getvalue()

# #     # --- step 1: PDF → Text ------------------------------------------------
# #     try:
# #         text = cached_extract(file_bytes)
# #     except Exception as e:
# #         st.error(f"PDF পড়তে সমস্যা হয়েছে: {e}")
# #         st.stop()

# #     st.success(f"Extracted {len(text):,} characters from **{uploaded.name}**")

# #     # --- step 2: Text → JSON ----------------------------------------------
# #     try:
# #         result = cached_parse(text)
# #         parse_error = None
# #     except Exception as e:
# #         result = None
# #         parse_error = str(e)

# #     # --- step 3: download buttons -----------------------------------------
# #     base_name = uploaded.name.rsplit(".", 1)[0]

# #     col1, col2 = st.columns(2)
# #     with col1:
# #         st.download_button(
# #             "⬇ Download raw text",
# #             data=text,
# #             file_name=f"{base_name}_raw_text.txt",
# #             mime="text/plain",
# #             use_container_width=True,
# #         )
# #     with col2:
# #         if result is not None:
# #             st.download_button(
# #                 "⬇ Download JSON",
# #                 data=json.dumps(result, indent=2, ensure_ascii=False),
# #                 file_name=f"{base_name}.json",
# #                 mime="application/json",
# #                 use_container_width=True,
# #             )

# #     # --- step 4: tabs -----------------------------------------------------
# #     tab1, tab2, tab3 = st.tabs(["📋 Parsed tables", "🔢 JSON", "📄 Raw text"])

# #     with tab1:
# #         if parse_error:
# #             st.error(f"Parse failed: {parse_error}")
# #         elif not result["tables"]:
# #             st.warning("কোনো table পাওয়া যায়নি। raw text দেখে ফরম্যাট মিলিয়ে নিন।")
# #         else:
# #             st.write(f"**{len(result['tables'])} table detected**")
# #             for name, t in result["tables"].items():
# #                 total = t.get("total")
# #                 style = total.get("style") if total else "-"
# #                 cost = total.get("Total Cost") if total else "-"
# #                 with st.expander(
# #                     f"{name}: {len(t['rows'])} rows | style={style} | cost={cost}"
# #                 ):
# #                     if t["rows"]:
# #                         st.dataframe(t["rows"], use_container_width=True)
# #                     if total:
# #                         st.markdown("**Total row:**")
# #                         st.json(total)

# #     with tab2:
# #         if result is not None:
# #             st.json(result)
# #         else:
# #             st.info("JSON পাওয়া যায়নি।")

# #     with tab3:
# #         st.text_area("Raw text", text, height=500)

# # else:
# #     st.info("একটি PDF আপলোড করুন।")


















# """
# po_app.py
# ---------
# Streamlit app: PDF → Raw Text → JSON (updated format)

# New JSON structure:
# {
#   "PO_HEADER": { "BUYER", "STYLE", "P.O._#", "OIQTY", "SHIP_QTY", "EX_SHORT", "CTN_QTY" },
#   "columns": [...],
#   "tables": {
#      "table N": {
#         "rows": [ { ..., "ORDER QTY", "SHIP QTY", "EX-SHORT", "UNIT / PREPACK",
#                         "CTN QTY", "CARTON QTY", "SKU / ITEM", ... } ],
#         "total": { ... }
#      }
#   }
# }
# """

# import io
# import re
# import json
# import math
# import streamlit as st
# import pdfplumber


# # ===========================================================================
# # 1. Shared column schema (updated)
# # ===========================================================================
# COLUMNS = [
#     "BUYER",
#     "STYLE",
#     "P.O. #",
#     "Dept",
#     "Style No",
#     "Full Carton",
#     "PrePack",
#     "PrePack Type",
#     "PrePack Pack Factor",
#     "SKU / ITEM",
#     "Units per PrePack",
#     "UNIT / PREPACK",
#     "Style Description",
#     "Item Carton Pack Factor",
#     "ORDER QTY",
#     "SHIP QTY",
#     "EX-SHORT",
#     "CTN QTY",
#     "CARTON QTY",
#     "#PrePackets Ordered",
#     "Universal CC #Color Desc",
#     "Size Desc",
#     "Unit Cost",
#     "Total Cost",
# ]


# # ===========================================================================
# # 2. Lines that must never be treated as a color name
# # ===========================================================================
# IGNORE_PATTERNS = [
#     "Print Date", "OLD NAVY", "Global Reference", "Market:",
#     "Market Channel", "Department:", "Destination Purchase Order", "Vendor",
#     "Factory", "Agent Name", "Payment Type", "Payment Terms", "Payment Method",
#     "Purchaser Currency", "Contract Ship", "Ship Cancel", "Terms of Sale",
#     "Freight Paid By", "Transfer Point", "Special Instructions", "Ship Mode",
#     "Country of Origin", "Country of Destination", "Powered by Infor Nexus",
#     "Dept Style No", "Total Units", "Total BULK", "Total SINGLE", "Total MULTIPLE",
#     "Total ASSORTED", "GRAND TOTAL", "THIS PURCHASE ORDER", "1 THIS EDI",
#     "2 VENDOR SHALL", "3 NOTHWITHSTANDING", "4 PLEASE PUT", "5 THE TRACEABILITY",
#     "6 A VARIANCE", "NOTE: FOR VENDORS", "=====", "BUYER", "STYLE", "P.O.",
#     "OIQTY", "SHIP QTY", "EX/SHORT", "CTN QTY", "CTN MEAS",
# ]


# def is_color_name(line: str) -> bool:
#     """Return True if the line looks like an all-uppercase color description."""
#     if not line or not line.strip():
#         return False
#     s = line.strip()
#     if not s.isupper():
#         return False
#     if not all(c.isalpha() or c.isspace() for c in s):
#         return False
#     for pat in IGNORE_PATTERNS:
#         if pat in s:
#             return False
#     return True


# # ===========================================================================
# # 3. PO header parser
# # ===========================================================================
# def parse_po_header(text: str) -> dict:
#     """
#     Extract PO-level fields that are FIXED for all tables:
#         BUYER, STYLE, P.O. #
#     plus derived totals:
#         OIQTY, SHIP_QTY, EX_SHORT, CTN_QTY
#     """
#     header = {
#         "BUYER": None,
#         "STYLE": None,
#         "P.O._#": None,
#         "OIQTY": 0,
#         "SHIP_QTY": 0,
#         "EX_SHORT": 0,
#         "CTN_QTY": 0,
#     }

#     # ---- BUYER ----
#     m = re.search(r"BUYER\s*[:\-]\s*([A-Z][A-Za-z0-9 &\.\-']+)", text)
#     if m:
#         header["BUYER"] = m.group(1).strip()

#     # ---- STYLE ----
#     m = re.search(r"STYLE\s*[:\-]\s*([0-9A-Za-z\-]+)", text)
#     if m:
#         header["STYLE"] = m.group(1).strip()

#     # ---- P.O. # ----
#     m = re.search(r"P\.?\s*O\.?\s*#?\s*[:\-]\s*([0-9A-Za-z\-]+)", text)
#     if m:
#         header["P.O._#"] = m.group(1).strip()

#     # ---- OIQTY / SHIP QTY / EX/SHORT / CTN QTY ----
#     m = re.search(r"OIQTY\s*[:\-]?\s*([\d,]+)", text)
#     if m:
#         header["OIQTY"] = int(m.group(1).replace(",", ""))

#     m = re.search(r"SHIP\s*QTY\s*[:\-]?\s*([\d,]+)", text)
#     if m:
#         header["SHIP_QTY"] = int(m.group(1).replace(",", ""))

#     m = re.search(r"EX\s*/?\s*SHORT\s*[:\-]?\s*([\d,]+)", text)
#     if m:
#         header["EX_SHORT"] = int(m.group(1).replace(",", ""))

#     m = re.search(r"CTN\s*QTY\s*[:\-]?\s*([\d,]+)", text)
#     if m:
#         header["CTN_QTY"] = int(m.group(1).replace(",", ""))

#     # Fallback: if OIQTY not found, sum from all "Total" lines later
#     return header


# # ===========================================================================
# # 4. Item row parser
# # ===========================================================================
# def parse_line_item(line: str):
#     """Parse a single '3340 ...' line into a row dict (new format)."""
#     tokens = line.split()
#     dept = tokens[0]
#     style_no = tokens[1]
#     idx = 2

#     full_carton = None
#     if idx < len(tokens) and tokens[idx] in ("N", "Y"):
#         full_carton = tokens[idx]
#         idx += 1

#     prepack = tokens[idx]; idx += 1
#     prepack_type = tokens[idx]; idx += 1

#     prepack_pack_factor = None
#     if idx < len(tokens) and tokens[idx].isdigit():
#         prepack_pack_factor = int(tokens[idx]); idx += 1

#     sku = tokens[idx]; idx += 1

#     units_per_prepack = tokens[idx]
#     if units_per_prepack.isdigit():
#         units_per_prepack = int(units_per_prepack)
#     idx += 1

#     # Style Description: collect alphabetic tokens until a numeric token
#     style_desc_tokens = []
#     while idx < len(tokens):
#         tok = tokens[idx]
#         if re.fullmatch(r'\d+', tok.replace(',', '')):
#             break
#         style_desc_tokens.append(tok)
#         idx += 1
#     style_description = " ".join(style_desc_tokens)

#     remaining = len(tokens) - idx
#     item_carton_pack_factor = None
#     qty_ordered = None

#     if remaining == 6:
#         item_carton_pack_factor = int(tokens[idx])
#         qty_ordered = int(tokens[idx + 1])
#         idx += 2
#     elif remaining == 5:
#         qty_ordered = int(tokens[idx])
#         idx += 1
#     else:
#         qty_ordered = int(tokens[idx])
#         idx += 1

#     color_code = tokens[idx]; idx += 1
#     size = tokens[idx]; idx += 1
#     unit_cost = float(tokens[idx].replace(',', '')); idx += 1
#     total_cost = float(tokens[idx].replace(',', ''))

#     # ---- derived fields ----
#     order_qty = qty_ordered or 0
#     ship_qty = order_qty           # placeholder — refine when ship data exists
#     ex_short = max(order_qty - ship_qty, 0)

#     # UNIT / PREPACK
#     unit_prepack = units_per_prepack if isinstance(units_per_prepack, int) else 1

#     # CTN QTY / CARTON QTY
#     if item_carton_pack_factor and item_carton_pack_factor > 0:
#         ctn_qty = math.ceil(order_qty / item_carton_pack_factor)
#     elif isinstance(units_per_prepack, int) and units_per_prepack > 0:
#         ctn_qty = math.ceil(order_qty / units_per_prepack)
#     else:
#         ctn_qty = order_qty
#     carton_qty = ctn_qty

#     return {
#         "BUYER": None,                    # filled from PO header later
#         "STYLE": None,                    # filled from PO header later
#         "P.O. #": None,                   # filled from PO header later
#         "Dept": dept,
#         "Style No": style_no,
#         "Full Carton": full_carton,
#         "PrePack": prepack,
#         "PrePack Type": prepack_type,
#         "PrePack Pack Factor": prepack_pack_factor,
#         "SKU / ITEM": sku,
#         "Units per PrePack": units_per_prepack,
#         "UNIT / PREPACK": unit_prepack,
#         "Style Description": style_description,
#         "Item Carton Pack Factor": item_carton_pack_factor,
#         "ORDER QTY": order_qty,
#         "SHIP QTY": ship_qty,
#         "EX-SHORT": ex_short,
#         "CTN QTY": ctn_qty,
#         "CARTON QTY": carton_qty,
#         "#PrePackets Ordered": None,
#         "Universal CC #Color Desc": color_code,
#         "Size Desc": size,
#         "Unit Cost": unit_cost,
#         "Total Cost": total_cost,
#     }


# # ===========================================================================
# # 5. Total row parser
# # ===========================================================================
# def parse_total(line: str):
#     """
#     5 tokens → Bulk total   : style filled, PrePack = null
#     6 tokens → PrePack total: style = null, PrePack filled
#     """
#     tokens = line.split()
#     if len(tokens) < 2 or not tokens[1].isdigit():
#         return None

#     if len(tokens) == 5:
#         return {
#             "style": int(tokens[1]),
#             "PrePack": None,
#             "PrePack Pack Factor": None,
#             "ORDER QTY": int(tokens[2]),
#             "SHIP QTY": int(tokens[2]),
#             "EX-SHORT": 0,
#             "CTN QTY": None,             # computed later from rows
#             "CARTON QTY": None,
#             "#PrePackets Ordered": None,
#             "Universal CC #Color Desc": tokens[3],
#             "Total Cost": float(tokens[4].replace(',', '')),
#         }
#     elif len(tokens) == 6:
#         return {
#             "style": None,
#             "PrePack": int(tokens[1]),
#             "PrePack Pack Factor": int(tokens[2]),
#             "ORDER QTY": int(tokens[3]),
#             "SHIP QTY": int(tokens[3]),
#             "EX-SHORT": 0,
#             "CTN QTY": None,
#             "CARTON QTY": None,
#             "#PrePackets Ordered": int(tokens[4]),
#             "Universal CC #Color Desc": None,
#             "Total Cost": float(tokens[5].replace(',', '')),
#         }
#     return None


# # ===========================================================================
# # 6. Main parser
# # ===========================================================================
# def parse_text(text: str) -> dict:
#     lines = text.splitlines()
#     po_header = parse_po_header(text)

#     tables = []
#     current_rows = []
#     i = 0

#     while i < len(lines):
#         line = lines[i].strip()

#         if line.startswith("3340 "):
#             row = parse_line_item(line)
#             # look ahead for color name
#             if i + 1 < len(lines):
#                 nxt = lines[i + 1].strip()
#                 if is_color_name(nxt):
#                     row["Universal CC #Color Desc"] = (
#                         row["Universal CC #Color Desc"] + " " + nxt
#                     )
#                     i += 1
#             current_rows.append(row)

#         elif line.startswith("Total "):
#             total = parse_total(line)
#             if total is not None:
#                 # look ahead for color name (Bulk totals only)
#                 if i + 1 < len(lines):
#                     nxt = lines[i + 1].strip()
#                     if is_color_name(nxt) and total["Universal CC #Color Desc"] is not None:
#                         total["Universal CC #Color Desc"] = (
#                             total["Universal CC #Color Desc"] + " " + nxt
#                         )
#                         i += 1

#                 # propagate #PrePackets Ordered into Single/Multi rows
#                 for row in current_rows:
#                     if row["PrePack Type"] in ("Single", "Multi"):
#                         if total.get("#PrePackets Ordered") is not None:
#                             row["#PrePackets Ordered"] = total["#PrePackets Ordered"]

#                 # aggregate CTN QTY / CARTON QTY for the total row
#                 total["CTN QTY"] = sum(
#                     r.get("CTN QTY") or 0 for r in current_rows
#                 )
#                 total["CARTON QTY"] = total["CTN QTY"]

#                 # inject PO header fields into every row
#                 for row in current_rows:
#                     row["BUYER"] = po_header["BUYER"]
#                     row["STYLE"] = po_header["STYLE"]
#                     row["P.O. #"] = po_header["P.O._#"]

#                 tables.append({"rows": current_rows, "total": total})
#                 current_rows = []

#         i += 1

#     # Fallback: if OIQTY / CTN_QTY missing from header, sum from totals
#     if not po_header["OIQTY"]:
#         po_header["OIQTY"] = sum(t["total"]["ORDER QTY"] for t in tables)
#     if not po_header["SHIP_QTY"]:
#         po_header["SHIP_QTY"] = sum(t["total"]["SHIP QTY"] for t in tables)
#     if not po_header["CTN_QTY"]:
#         po_header["CTN_QTY"] = sum(t["total"]["CTN QTY"] for t in tables)
#     po_header["EX_SHORT"] = max(
#         po_header["OIQTY"] - po_header["SHIP_QTY"], 0
#     )

#     return {
#         "PO_HEADER": po_header,
#         "columns": COLUMNS,
#         "tables": {f"table {idx + 1}": t for idx, t in enumerate(tables)},
#     }


# # ===========================================================================
# # 7. PDF → Text
# # ===========================================================================
# def extract_text(file_obj) -> str:
#     with pdfplumber.open(file_obj) as pdf:
#         return "\n".join(
#             f"===== PAGE {i} =====\n{page.extract_text() or ''}\n"
#             for i, page in enumerate(pdf.pages, start=1)
#         )


# # ===========================================================================
# # 8. Cached wrappers
# # ===========================================================================
# @st.cache_data(show_spinner=False)
# def cached_extract(file_bytes: bytes) -> str:
#     return extract_text(io.BytesIO(file_bytes))


# @st.cache_data(show_spinner=False)
# def cached_parse(text: str) -> dict:
#     return parse_text(text)


# # ===========================================================================
# # 9. Streamlit UI
# # ===========================================================================
# st.set_page_config(page_title="PO PDF Extractor", layout="wide")
# st.title("PO PDF Extractor")
# st.caption("PDF → Raw Text → JSON (updated format)")

# uploaded = st.file_uploader("Upload a PDF", type=["pdf"])

# if uploaded is not None:
#     file_bytes = uploaded.getvalue()

#     # --- step 1: PDF → Text ------------------------------------------------
#     try:
#         text = cached_extract(file_bytes)
#     except Exception as e:
#         st.error(f"PDF পড়তে সমস্যা হয়েছে: {e}")
#         st.stop()

#     st.success(f"Extracted {len(text):,} characters from **{uploaded.name}**")

#     # --- step 2: Text → JSON ----------------------------------------------
#     try:
#         result = cached_parse(text)
#         parse_error = None
#     except Exception as e:
#         result = None
#         parse_error = str(e)

#     # --- step 3: download buttons -----------------------------------------
#     base_name = uploaded.name.rsplit(".", 1)[0]

#     col1, col2 = st.columns(2)
#     with col1:
#         st.download_button(
#             "⬇ Download raw text",
#             data=text,
#             file_name=f"{base_name}_raw_text.txt",
#             mime="text/plain",
#             use_container_width=True,
#         )
#     with col2:
#         if result is not None:
#             st.download_button(
#                 "⬇ Download JSON",
#                 data=json.dumps(result, indent=2, ensure_ascii=False),
#                 file_name=f"{base_name}.json",
#                 mime="application/json",
#                 use_container_width=True,
#             )

#     # --- step 4: PO header preview ----------------------------------------
#     if result is not None:
#         with st.expander("🧾 PO_HEADER (fixed for all tables)", expanded=True):
#             st.json(result.get("PO_HEADER", {}))

#     # --- step 5: tabs -----------------------------------------------------
#     tab1, tab2, tab3 = st.tabs(["📋 Parsed tables", "🔢 JSON", "📄 Raw text"])

#     with tab1:
#         if parse_error:
#             st.error(f"Parse failed: {parse_error}")
#         elif not result["tables"]:
#             st.warning("কোনো table পাওয়া যায়নি। raw text দেখে ফরম্যাট মিলিয়ে নিন।")
#         else:
#             st.write(f"**{len(result['tables'])} table detected**")
#             for name, t in result["tables"].items():
#                 total = t.get("total")
#                 style = total.get("style") if total else "-"
#                 cost = total.get("Total Cost") if total else "-"
#                 with st.expander(
#                     f"{name}: {len(t['rows'])} rows | style={style} | cost={cost}"
#                 ):
#                     if t["rows"]:
#                         st.dataframe(t["rows"], use_container_width=True)
#                     if total:
#                         st.markdown("**Total row:**")
#                         st.json(total)

#     with tab2:
#         if result is not None:
#             st.json(result)
#         else:
#             st.info("JSON পাওয়া যায়নি।")

#     with tab3:
#         st.text_area("Raw text", text, height=500)

# else:
#     st.info("একটি PDF আপলোড করুন।")


"""
po_app.py
---------
Streamlit app: PDF → Raw Text → JSON (updated format)

New JSON structure:
{
  "PO_HEADER": { "BUYER", "STYLE", "P.O._#", "OIQTY", "SHIP_QTY", "EX_SHORT", "CTN_QTY" },
  "columns": [...],
  "tables": {
     "table N": {
        "rows": [ { ..., "ORDER QTY", "SHIP QTY", "EX-SHORT", "UNIT / PREPACK",
                        "CTN QTY", "CARTON QTY", "SKU / ITEM", ... } ],
        "total": { ... }
     }
  }
}
"""

import io
import re
import json
import math
import streamlit as st
import pdfplumber


# ===========================================================================
# 1. Shared column schema (updated)
# ===========================================================================
COLUMNS = [
    "BUYER",
    "STYLE",
    "P.O. #",
    "Dept",
    "Style No",
    "Full Carton",
    "PrePack",
    "PrePack Type",
    "PrePack Pack Factor",
    "SKU / ITEM",
    "Units per PrePack",
    "UNIT / PREPACK",
    "Style Description",
    "Item Carton Pack Factor",
    "ORDER QTY",
    "SHIP QTY",
    "EX-SHORT",
    "CTN QTY",
    "CARTON QTY",
    "#PrePackets Ordered",
    "Universal CC #Color Desc",
    "Size Desc",
    "Unit Cost",
    "Total Cost",
]


# ===========================================================================
# 2. Lines that must never be treated as a color name
# ===========================================================================
IGNORE_PATTERNS = [
    "Print Date", "OLD NAVY", "Global Reference", "Market:",
    "Market Channel", "Department:", "Destination Purchase Order", "Vendor",
    "Factory", "Agent Name", "Payment Type", "Payment Terms", "Payment Method",
    "Purchaser Currency", "Contract Ship", "Ship Cancel", "Terms of Sale",
    "Freight Paid By", "Transfer Point", "Special Instructions", "Ship Mode",
    "Country of Origin", "Country of Destination", "Powered by Infor Nexus",
    "Dept Style No", "Total Units", "Total BULK", "Total SINGLE", "Total MULTIPLE",
    "Total ASSORTED", "GRAND TOTAL", "THIS PURCHASE ORDER", "1 THIS EDI",
    "2 VENDOR SHALL", "3 NOTHWITHSTANDING", "4 PLEASE PUT", "5 THE TRACEABILITY",
    "6 A VARIANCE", "NOTE: FOR VENDORS", "=====", "BUYER", "STYLE", "P.O.",
    "OIQTY", "SHIP QTY", "EX/SHORT", "CTN QTY", "CTN MEAS",
]


# Any item line: <4-digit dept> <6-digit style> ...  (was hard-coded to dept 3340)
ITEM_LINE_RE = re.compile(r"^\d{4}\s+\d{6}\s+")


def _to_int(tok: str) -> int:
    """'2,223' -> 2223"""
    return int(tok.replace(",", ""))


def is_color_name(line: str) -> bool:
    """Return True if the line looks like an all-uppercase color description."""
    if not line or not line.strip():
        return False
    s = line.strip()
    if not s.isupper():
        return False
    if not all(c.isalpha() or c.isspace() for c in s):
        return False
    for pat in IGNORE_PATTERNS:
        if pat in s:
            return False
    return True


# ===========================================================================
# 3. PO header parser
# ===========================================================================
def parse_po_header(text: str) -> dict:
    """
    Extract PO-level fields that are FIXED for all tables:
        BUYER, STYLE, P.O. #
    plus derived totals:
        OIQTY, SHIP_QTY, EX_SHORT, CTN_QTY
    """
    header = {
        "BUYER": None,
        "STYLE": None,
        "P.O._#": None,
        "OIQTY": 0,
        "SHIP_QTY": 0,
        "EX_SHORT": 0,
        "CTN_QTY": None,
    }

    # ---- BUYER ----
    m = re.search(r"BUYER\s*[:\-]\s*([A-Z][A-Za-z0-9 &\.\-']+)", text)
    if m:
        header["BUYER"] = m.group(1).strip()

    # ---- STYLE ----
    m = re.search(r"STYLE\s*[:\-]\s*([0-9A-Za-z\-]+)", text)
    if m:
        header["STYLE"] = m.group(1).strip()

    # ---- P.O. # ----
    m = re.search(r"P\.?\s*O\.?\s*#?\s*[:\-]\s*([0-9A-Za-z\-]+)", text)
    if m:
        header["P.O._#"] = m.group(1).strip()

    # ---- OIQTY / SHIP QTY / EX/SHORT / CTN QTY ----
    m = re.search(r"OIQTY\s*[:\-]?\s*([\d,]+)", text)
    if m:
        header["OIQTY"] = int(m.group(1).replace(",", ""))

    m = re.search(r"SHIP\s*QTY\s*[:\-]?\s*([\d,]+)", text)
    if m:
        header["SHIP_QTY"] = int(m.group(1).replace(",", ""))

    m = re.search(r"EX\s*/?\s*SHORT\s*[:\-]?\s*([\d,]+)", text)
    if m:
        header["EX_SHORT"] = int(m.group(1).replace(",", ""))

    m = re.search(r"CTN\s*QTY\s*[:\-]?\s*([\d,]+)", text)
    if m:
        header["CTN_QTY"] = int(m.group(1).replace(",", ""))

    # ---- FIX 2: the PO PDF has no "BUYER:" / "P.O.:" labels — use its own labels ----
    if not header["BUYER"]:
        m = re.search(r"Brand:\s*([A-Z ]+?)\s+Global Reference", text)
        header["BUYER"] = m.group(1).strip() if m else None
    if not header["P.O._#"]:
        m = re.search(r"Destination Purchase Order # (\d+)", text)
        header["P.O._#"] = m.group(1) if m else None
    if not header["STYLE"]:
        m = re.search(r"^\d{4} (\d{6}) ", text, re.M)
        header["STYLE"] = m.group(1) if m else None

    # Fallback: if OIQTY not found, sum from all "Total" lines later
    return header


# ===========================================================================
# 4. Item row parser
# ===========================================================================
def parse_line_item(line: str):
    """Parse a single '3340 ...' line into a row dict (new format)."""
    tokens = line.split()
    dept = tokens[0]
    style_no = tokens[1]
    idx = 2

    full_carton = None
    if idx < len(tokens) and tokens[idx] in ("N", "Y"):
        full_carton = tokens[idx]
        idx += 1

    prepack = tokens[idx]; idx += 1
    prepack_type = tokens[idx]; idx += 1

    # FIX 1: there is no pack-factor column on these lines. The next number is
    # the 13-digit SKU, then units per prepack (2 / 1, or "Bulk" for Bulk lines).
    prepack_pack_factor = None
    sku = tokens[idx]; idx += 1

    units_per_prepack = tokens[idx]
    if units_per_prepack.isdigit():
        units_per_prepack = int(units_per_prepack)
    idx += 1

    # Style Description: collect alphabetic tokens until a numeric token
    style_desc_tokens = []
    while idx < len(tokens):
        tok = tokens[idx]
        if re.fullmatch(r'\d+', tok.replace(',', '')):
            break
        style_desc_tokens.append(tok)
        idx += 1
    style_description = " ".join(style_desc_tokens)

    remaining = len(tokens) - idx
    item_carton_pack_factor = None
    qty_ordered = None

    if remaining == 6:
        item_carton_pack_factor = int(tokens[idx])
        qty_ordered = int(tokens[idx + 1])
        idx += 2
    elif remaining == 5:
        qty_ordered = int(tokens[idx])
        idx += 1
    else:
        qty_ordered = int(tokens[idx])
        idx += 1

    color_code = tokens[idx]; idx += 1
    size = tokens[idx]; idx += 1
    unit_cost = float(tokens[idx].replace(',', '')); idx += 1
    total_cost = float(tokens[idx].replace(',', ''))

    # ---- derived fields ----
    order_qty = qty_ordered or 0
    ship_qty = order_qty           # placeholder — refine when ship data exists
    ex_short = max(order_qty - ship_qty, 0)

    # UNIT / PREPACK
    unit_prepack = units_per_prepack if isinstance(units_per_prepack, int) else 1

    # FIX 3: carton count depends on how prepacks are split into cartons
    # (packing-list step), so it is not guessed here.
    ctn_qty = None
    carton_qty = None

    return {
        "BUYER": None,                    # filled from PO header later
        "STYLE": None,                    # filled from PO header later
        "P.O. #": None,                   # filled from PO header later
        "Dept": dept,
        "Style No": style_no,
        "Full Carton": full_carton,
        "PrePack": prepack,
        "PrePack Type": prepack_type,
        "PrePack Pack Factor": prepack_pack_factor,
        "SKU / ITEM": sku,
        "Units per PrePack": units_per_prepack,
        "UNIT / PREPACK": unit_prepack,
        "Style Description": style_description,
        "Item Carton Pack Factor": item_carton_pack_factor,
        "ORDER QTY": order_qty,
        "SHIP QTY": ship_qty,
        "EX-SHORT": ex_short,
        "CTN QTY": ctn_qty,
        "CARTON QTY": carton_qty,
        "#PrePackets Ordered": None,
        "Universal CC #Color Desc": color_code,
        "Size Desc": size,
        "Unit Cost": unit_cost,
        "Total Cost": total_cost,
    }


# ===========================================================================
# 5. Total row parser
# ===========================================================================
def parse_total(line: str):
    """
    5 tokens → Bulk total   : style filled, PrePack = null
    6 tokens → PrePack total: style = null, PrePack filled
    """
    tokens = line.split()
    if len(tokens) < 2 or not tokens[1].replace(",", "").isdigit():
        return None

    if len(tokens) == 5:
        return {
            "style": _to_int(tokens[1]),
            "PrePack": None,
            "PrePack Pack Factor": None,
            "ORDER QTY": _to_int(tokens[2]),
            "SHIP QTY": _to_int(tokens[2]),
            "EX-SHORT": 0,
            "CTN QTY": None,
            "CARTON QTY": None,
            "#PrePackets Ordered": None,
            "Universal CC #Color Desc": tokens[3],
            "Total Cost": float(tokens[4].replace(',', '')),
        }
    elif len(tokens) == 6:
        return {
            "style": None,
            "PrePack": _to_int(tokens[1]),
            "PrePack Pack Factor": _to_int(tokens[2]),
            "ORDER QTY": _to_int(tokens[3]),
            "SHIP QTY": _to_int(tokens[3]),
            "EX-SHORT": 0,
            "CTN QTY": None,
            "CARTON QTY": None,
            "#PrePackets Ordered": _to_int(tokens[4]),
            "Universal CC #Color Desc": None,
            "Total Cost": float(tokens[5].replace(',', '')),
        }
    return None


# ===========================================================================
# 6. Main parser
# ===========================================================================
def parse_text(text: str) -> dict:
    lines = text.splitlines()
    po_header = parse_po_header(text)

    tables = []
    current_rows = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if ITEM_LINE_RE.match(line):
            row = parse_line_item(line)
            # look ahead for color name
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if is_color_name(nxt):
                    row["Universal CC #Color Desc"] = (
                        row["Universal CC #Color Desc"] + " " + nxt
                    )
                    i += 1
            current_rows.append(row)

        elif line.startswith("Total "):
            total = parse_total(line)
            if total is not None:
                # look ahead for color name (Bulk totals only)
                if i + 1 < len(lines):
                    nxt = lines[i + 1].strip()
                    if is_color_name(nxt) and total["Universal CC #Color Desc"] is not None:
                        total["Universal CC #Color Desc"] = (
                            total["Universal CC #Color Desc"] + " " + nxt
                        )
                        i += 1

                # propagate #PrePackets Ordered into Single/Multi rows
                for row in current_rows:
                    if row["PrePack Type"] in ("Single", "Multi"):
                        if total.get("#PrePackets Ordered") is not None:
                            row["#PrePackets Ordered"] = total["#PrePackets Ordered"]

                # inject PO header fields into every row
                for row in current_rows:
                    row["BUYER"] = po_header["BUYER"]
                    row["STYLE"] = po_header["STYLE"]
                    row["P.O. #"] = po_header["P.O._#"]

                tables.append({"rows": current_rows, "total": total})
                current_rows = []

        i += 1

    # Fallback: if OIQTY missing from header, sum from totals
    if not po_header["OIQTY"]:
        po_header["OIQTY"] = sum(t["total"]["ORDER QTY"] for t in tables)
    if not po_header["SHIP_QTY"]:
        po_header["SHIP_QTY"] = sum(t["total"]["SHIP QTY"] for t in tables)
    po_header["EX_SHORT"] = max(
        po_header["OIQTY"] - po_header["SHIP_QTY"], 0
    )

    return {
        "PO_HEADER": po_header,
        "columns": COLUMNS,
        "tables": {f"table {idx + 1}": t for idx, t in enumerate(tables)},
    }


# ===========================================================================
# 7. PDF → Text
# ===========================================================================
def extract_text(file_obj) -> str:
    with pdfplumber.open(file_obj) as pdf:
        return "\n".join(
            f"===== PAGE {i} =====\n{page.extract_text() or ''}\n"
            for i, page in enumerate(pdf.pages, start=1)
        )


# ===========================================================================
# 8. Cached wrappers
# ===========================================================================
@st.cache_data(show_spinner=False)
def cached_extract(file_bytes: bytes) -> str:
    return extract_text(io.BytesIO(file_bytes))


@st.cache_data(show_spinner=False)
def cached_parse(text: str) -> dict:
    return parse_text(text)


# ===========================================================================
# 9. Streamlit UI
# ===========================================================================
st.set_page_config(page_title="PO PDF Extractor", layout="wide")
st.title("PO PDF Extractor")
st.caption("PDF → Raw Text → JSON (updated format)")

uploaded = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded is not None:
    file_bytes = uploaded.getvalue()

    # --- step 1: PDF → Text ------------------------------------------------
    try:
        text = cached_extract(file_bytes)
    except Exception as e:
        st.error(f"PDF পড়তে সমস্যা হয়েছে: {e}")
        st.stop()

    st.success(f"Extracted {len(text):,} characters from **{uploaded.name}**")

    # --- step 2: Text → JSON ----------------------------------------------
    try:
        result = cached_parse(text)
        parse_error = None
    except Exception as e:
        result = None
        parse_error = str(e)

    # --- step 3: download buttons -----------------------------------------
    base_name = uploaded.name.rsplit(".", 1)[0]

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇ Download raw text",
            data=text,
            file_name=f"{base_name}_raw_text.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col2:
        if result is not None:
            st.download_button(
                "⬇ Download JSON",
                data=json.dumps(result, indent=2, ensure_ascii=False),
                file_name=f"{base_name}.json",
                mime="application/json",
                use_container_width=True,
            )

    # --- step 4: PO header preview ----------------------------------------
    if result is not None:
        with st.expander("🧾 PO_HEADER (fixed for all tables)", expanded=True):
            st.json(result.get("PO_HEADER", {}))

    # --- step 5: tabs -----------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["📋 Parsed tables", "🔢 JSON", "📄 Raw text"])

    with tab1:
        if parse_error:
            st.error(f"Parse failed: {parse_error}")
        elif not result["tables"]:
            st.warning("কোনো table পাওয়া যায়নি। raw text দেখে ফরম্যাট মিলিয়ে নিন।")
        else:
            st.write(f"**{len(result['tables'])} table detected**")
            for name, t in result["tables"].items():
                total = t.get("total")
                style = total.get("style") if total else "-"
                cost = total.get("Total Cost") if total else "-"
                with st.expander(
                    f"{name}: {len(t['rows'])} rows | style={style} | cost={cost}"
                ):
                    if t["rows"]:
                        st.dataframe(t["rows"], use_container_width=True)
                    if total:
                        st.markdown("**Total row:**")
                        st.json(total)

    with tab2:
        if result is not None:
            st.json(result)
        else:
            st.info("JSON পাওয়া যায়নি।")

    with tab3:
        st.text_area("Raw text", text, height=500)

else:
    st.info("একটি PDF আপলোড করুন।")