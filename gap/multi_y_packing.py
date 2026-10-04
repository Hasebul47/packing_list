# # # # # # # # # # """
# # # # # # # # # # packing_list_app.py
# # # # # # # # # # -------------------
# # # # # # # # # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.
# # # # # # # # # # Each COLOR gets its own separate table.

# # # # # # # # # # Run:
# # # # # # # # # #     streamlit run packing_list_app.py

# # # # # # # # # # Requires: streamlit, pandas, openpyxl (optional, for Excel export)
# # # # # # # # # # """

# # # # # # # # # # import io
# # # # # # # # # # import json
# # # # # # # # # # from pathlib import Path

# # # # # # # # # # import pandas as pd
# # # # # # # # # # import streamlit as st


# # # # # # # # # # # ===========================================================================
# # # # # # # # # # # Config
# # # # # # # # # # # ===========================================================================
# # # # # # # # # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # # # # # # # # st.title("📦 Packing List — Multi Pack (Y)")

# # # # # # # # # # DEFAULT_JSON = "61480360.json"
# # # # # # # # # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # # # # # # # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # # # # # # # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # # # # # # # # ===========================================================================
# # # # # # # # # # # Helpers
# # # # # # # # # # # ===========================================================================
# # # # # # # # # # @st.cache_data(show_spinner=False)
# # # # # # # # # # def load_json(path: str) -> dict:
# # # # # # # # # #     with open(path, "r", encoding="utf-8") as f:
# # # # # # # # # #         return json.load(f)


# # # # # # # # # # def color_display(raw: str) -> str:
# # # # # # # # # #     """'000905518-000 TEAKWOOD' → 'TEAKWOOD'"""
# # # # # # # # # #     if not raw:
# # # # # # # # # #         return ""
# # # # # # # # # #     parts = raw.rsplit(" ", 1)
# # # # # # # # # #     return parts[-1] if len(parts) > 1 else raw


# # # # # # # # # # # ===========================================================================
# # # # # # # # # # # Build packing list — grouped by color
# # # # # # # # # # # ===========================================================================
# # # # # # # # # # def build_packing_list_grouped(data: dict) -> dict:
# # # # # # # # # #     """
# # # # # # # # # #     Returns:
# # # # # # # # # #         {
# # # # # # # # # #           "TEAKWOOD":    [row, total_row],
# # # # # # # # # #           "NAVY CAPTAIN":[row, total_row],
# # # # # # # # # #           ...
# # # # # # # # # #         }
# # # # # # # # # #     """
# # # # # # # # # #     groups: dict[str, list] = {}
# # # # # # # # # #     ctn_counter: dict[str, int] = {}

# # # # # # # # # #     for tname, table in data["tables"].items():
# # # # # # # # # #         trows = table.get("rows") or []
# # # # # # # # # #         total = table.get("total") or {}
# # # # # # # # # #         if not trows:
# # # # # # # # # #             continue

# # # # # # # # # #         first = trows[0]
# # # # # # # # # #         if first.get("PrePack Type") != "Multi":
# # # # # # # # # #             continue
# # # # # # # # # #         if first.get("Full Carton") != "Y":
# # # # # # # # # #             continue

# # # # # # # # # #         color = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # # # # # # # # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # # # # # # # # #         row_no = ctn_counter[color]

# # # # # # # # # #         ctn_mes     = total.get("#PrePackets Ordered")
# # # # # # # # # #         qty_per_ctn = total.get("PrePack Pack Factor") or sum(
# # # # # # # # # #             r.get("Units per PrePack") or 0 for r in trows
# # # # # # # # # #         )
# # # # # # # # # #         total_qty   = total.get("Qty Ordered (eaches)") or sum(
# # # # # # # # # #             r.get("Qty Ordered (eaches)") or 0 for r in trows
# # # # # # # # # #         )
# # # # # # # # # #         prepack = first.get("PrePack")

# # # # # # # # # #         # ---- data row ----
# # # # # # # # # #         data_row = {
# # # # # # # # # #             "CTN NO":          row_no,
# # # # # # # # # #             "CTN MES:":        ctn_mes,
# # # # # # # # # #             "CTN QTY":         ctn_mes,
# # # # # # # # # #             "COLOR":           color,
# # # # # # # # # #             "PREPACK STECKER": str(prepack),
# # # # # # # # # #         }
# # # # # # # # # #         for r in trows:
# # # # # # # # # #             data_row[r["Size Desc"]] = r.get("Units per PrePack")
# # # # # # # # # #         data_row["PER BLST"]     = f"{qty_per_ctn} X 1"
# # # # # # # # # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # # # # # # # # #         data_row["TOTAL QTY"]    = total_qty
# # # # # # # # # #         data_row["GROSS WEIGHT"] = None
# # # # # # # # # #         data_row["NET WEIGHT"]   = None

# # # # # # # # # #         # ---- total row ----
# # # # # # # # # #         tot = {
# # # # # # # # # #             "CTN NO":          "TOTAL",
# # # # # # # # # #             "CTN MES:":        None,
# # # # # # # # # #             "CTN QTY":         f"{ctn_mes} CTNS" if ctn_mes else None,
# # # # # # # # # #             "COLOR":           None,
# # # # # # # # # #             "PREPACK STECKER": None,
# # # # # # # # # #         }
# # # # # # # # # #         for r in trows:
# # # # # # # # # #             u = r.get("Units per PrePack") or 0
# # # # # # # # # #             tot[r["Size Desc"]] = (ctn_mes * u) if ctn_mes else None
# # # # # # # # # #         tot["PER BLST"]     = None
# # # # # # # # # #         tot["QTY PER CTN"]  = None
# # # # # # # # # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # # # # # # # # #         tot["GROSS WEIGHT"] = None
# # # # # # # # # #         tot["NET WEIGHT"]   = None

# # # # # # # # # #         groups.setdefault(color, []).append(data_row)
# # # # # # # # # #         groups[color].append(tot)

# # # # # # # # # #     return groups


# # # # # # # # # # # ===========================================================================
# # # # # # # # # # # UI
# # # # # # # # # # # ===========================================================================
# # # # # # # # # # json_path = st.sidebar.text_input("JSON file path", DEFAULT_JSON)

# # # # # # # # # # if not Path(json_path).exists():
# # # # # # # # # #     st.error(f"File not found: `{json_path}`")
# # # # # # # # # #     st.stop()

# # # # # # # # # # data = load_json(json_path)
# # # # # # # # # # groups = build_packing_list_grouped(data)

# # # # # # # # # # if not groups:
# # # # # # # # # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # # # # # # # # #     st.stop()


# # # # # # # # # # # ===========================================================================
# # # # # # # # # # # Render one table per color
# # # # # # # # # # # ===========================================================================
# # # # # # # # # # all_frames: list[pd.DataFrame] = []

# # # # # # # # # # for color, rows in groups.items():
# # # # # # # # # #     present_sizes = [s for s in SIZE_ORDER if any(s in r for r in rows)]
# # # # # # # # # #     columns = LEFT_STATIC + present_sizes + RIGHT_STATIC
# # # # # # # # # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # # # # # # # # #     st.subheader(f"🎨 {color}")
# # # # # # # # # #     st.caption(f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s)")

# # # # # # # # # #     col_cfg = {
# # # # # # # # # #         "CTN NO":          st.column_config.TextColumn("CTN NO", width="small"),
# # # # # # # # # #         "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small"),
# # # # # # # # # #         "CTN QTY":         st.column_config.TextColumn("CTN QTY", width="small"),
# # # # # # # # # #         "COLOR":           st.column_config.TextColumn("COLOR", width="medium"),
# # # # # # # # # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium"),
# # # # # # # # # #         "PER BLST":        st.column_config.TextColumn("PER BLST", width="small"),
# # # # # # # # # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small"),
# # # # # # # # # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY", width="small"),
# # # # # # # # # #         "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f"),
# # # # # # # # # #         "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT", width="small", format="%.2f"),
# # # # # # # # # #     }
# # # # # # # # # #     for s in present_sizes:
# # # # # # # # # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small")

# # # # # # # # # #     edited = st.data_editor(
# # # # # # # # # #         df,
# # # # # # # # # #         use_container_width=True,
# # # # # # # # # #         hide_index=True,
# # # # # # # # # #         num_rows="fixed",
# # # # # # # # # #         column_config=col_cfg,
# # # # # # # # # #         key=f"packing_editor_{color}",
# # # # # # # # # #     )

# # # # # # # # # #     # tag color so the combined Excel gets a COLOR column already present
# # # # # # # # # #     all_frames.append(edited)

# # # # # # # # # #     st.divider()


# # # # # # # # # # # ===========================================================================
# # # # # # # # # # # Downloads
# # # # # # # # # # # ===========================================================================
# # # # # # # # # # st.markdown("### Download")

# # # # # # # # # # # Combine for export: add a blank separator row between colors
# # # # # # # # # # export_rows: list[dict] = []
# # # # # # # # # # for i, (color, _rows) in enumerate(groups.items()):
# # # # # # # # # #     if i > 0:
# # # # # # # # # #         export_rows.append({})  # blank separator
# # # # # # # # # #     export_rows.extend(all_frames[i].to_dict(orient="records"))

# # # # # # # # # # combined = pd.DataFrame(export_rows)

# # # # # # # # # # col1, col2 = st.columns(2)

# # # # # # # # # # with col1:
# # # # # # # # # #     csv = combined.to_csv(index=False).encode("utf-8")
# # # # # # # # # #     st.download_button(
# # # # # # # # # #         "⬇ Download CSV (all colors)",
# # # # # # # # # #         data=csv,
# # # # # # # # # #         file_name="packing_list_multi.csv",
# # # # # # # # # #         mime="text/csv",
# # # # # # # # # #         use_container_width=True,
# # # # # # # # # #     )

# # # # # # # # # # with col2:
# # # # # # # # # #     try:
# # # # # # # # # #         buf = io.BytesIO()
# # # # # # # # # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # # # # # # # # #             for color, df in zip(groups.keys(), all_frames):
# # # # # # # # # #                 # Excel sheet names: max 31 chars, no special chars
# # # # # # # # # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # # # # # # # # #                 df.to_excel(writer, index=False, sheet_name=sheet)
# # # # # # # # # #         st.download_button(
# # # # # # # # # #             "⬇ Download Excel (one sheet per color)",
# # # # # # # # # #             data=buf.getvalue(),
# # # # # # # # # #             file_name="packing_list_multi.xlsx",
# # # # # # # # # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # # # # # # # # #             use_container_width=True,
# # # # # # # # # #         )
# # # # # # # # # #     except ImportError:
# # # # # # # # # #         st.info("Install `openpyxl` to enable Excel export:  `pip install openpyxl`")


# # # # # # # # # # # ===========================================================================
# # # # # # # # # # # Sidebar info
# # # # # # # # # # # ===========================================================================
# # # # # # # # # # with st.sidebar:
# # # # # # # # # #     st.markdown("### Colors detected")
# # # # # # # # # #     for color, rows in groups.items():
# # # # # # # # # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # # # # # # # # #         st.write(f"- **{color}** — {n} group(s)")



# # # # # # # # # """
# # # # # # # # # multi_pack.py
# # # # # # # # # -------------
# # # # # # # # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.
# # # # # # # # # Each COLOR gets its own separate table.
# # # # # # # # # Shows a SIZE → N.W. / N.N.W. / EMPTY CTN WT. reference header
# # # # # # # # # and auto-fills NET WEIGHT.

# # # # # # # # # Run:
# # # # # # # # #     streamlit run multi_pack.py
# # # # # # # # # """

# # # # # # # # # import io
# # # # # # # # # import json
# # # # # # # # # from pathlib import Path

# # # # # # # # # import pandas as pd
# # # # # # # # # import streamlit as st


# # # # # # # # # # ===========================================================================
# # # # # # # # # # Config
# # # # # # # # # # ===========================================================================
# # # # # # # # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # # # # # # # st.title("📦 Packing List — Multi Pack (Y)")

# # # # # # # # # DEFAULT_JSON = "61480360.json"

# # # # # # # # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # # # # # # # # --- weights (kg) ----------------------------------------------------------
# # # # # # # # # SIZE_NET_WEIGHT = {
# # # # # # # # #     "XS":   0.510,
# # # # # # # # #     "S":    0.520,
# # # # # # # # #     "M":    0.550,
# # # # # # # # #     "L":    0.560,
# # # # # # # # #     "XL":   0.610,
# # # # # # # # #     "XXL":  0.650,
# # # # # # # # #     "XXL+": 0.690,
# # # # # # # # # }

# # # # # # # # # SIZE_NEW_NET_WEIGHT = {
# # # # # # # # #     "XS":   0.49,
# # # # # # # # #     "S":    0.50,
# # # # # # # # #     "M":    0.53,
# # # # # # # # #     "L":    0.54,
# # # # # # # # #     "XL":   0.59,
# # # # # # # # #     "XXL":  0.63,
# # # # # # # # #     "XXL+": 0.67,
# # # # # # # # # }

# # # # # # # # # SIZE_EMPTY_CTN_WEIGHT = {
# # # # # # # # #     "XS":   0.49,
# # # # # # # # #     "S":    1.0,
# # # # # # # # #     "M":    1.0,
# # # # # # # # #     "L":    1.0,
# # # # # # # # #     "XL":   1.0,
# # # # # # # # #     "XXL":  1.0,
# # # # # # # # #     "XXL+": 1.0,
# # # # # # # # # }

# # # # # # # # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # # # # # # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # # # # # # # ===========================================================================
# # # # # # # # # # Helpers
# # # # # # # # # # ===========================================================================
# # # # # # # # # @st.cache_data(show_spinner=False)
# # # # # # # # # def load_json(path: str) -> dict:
# # # # # # # # #     with open(path, "r", encoding="utf-8") as f:
# # # # # # # # #         return json.load(f)


# # # # # # # # # def color_display(raw: str) -> str:
# # # # # # # # #     """'000905518-000 TEAKWOOD' → 'TEAKWOOD'"""
# # # # # # # # #     if not raw:
# # # # # # # # #         return ""
# # # # # # # # #     parts = raw.rsplit(" ", 1)
# # # # # # # # #     return parts[-1] if len(parts) > 1 else raw


# # # # # # # # # def present_sizes(rows: list) -> list:
# # # # # # # # #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # # # # # # # # def render_size_weight_header(sizes: list) -> None:
# # # # # # # # #     """
# # # # # # # # #     Reference table shown above every packing table:
# # # # # # # # #         SIZE           XS     S      M      L      XL     XXL    XXL+
# # # # # # # # #         N.W.           0.510  ...
# # # # # # # # #         N.N.W.         0.490  ...
# # # # # # # # #         EMPTY CTN WT.  0.490  ...
# # # # # # # # #     """
# # # # # # # # #     rows = {
# # # # # # # # #         "N.W.":          [f"{SIZE_NET_WEIGHT[s]:.3f}"        for s in sizes],
# # # # # # # # #         "N.N.W.":        [f"{SIZE_NEW_NET_WEIGHT[s]:.3f}"    for s in sizes],
# # # # # # # # #         "EMPTY CTN WT.": [f"{SIZE_EMPTY_CTN_WEIGHT[s]:.3f}"  for s in sizes],
# # # # # # # # #     }
# # # # # # # # #     header_df = pd.DataFrame(rows, index=sizes).T
# # # # # # # # #     header_df.index.name = "SIZE"
# # # # # # # # #     st.dataframe(header_df, use_container_width=False)


# # # # # # # # # def net_weight_per_carton_multi(rows: list):
# # # # # # # # #     """
# # # # # # # # #     Multi: per-carton net = sum over sizes (units_in_carton × N.W.).
# # # # # # # # #     Uses SIZE_NET_WEIGHT (N.W.).
# # # # # # # # #     """
# # # # # # # # #     total = 0.0
# # # # # # # # #     found = False
# # # # # # # # #     for r in rows:
# # # # # # # # #         size  = r.get("Size Desc")
# # # # # # # # #         units = r.get("Units per PrePack") or 0
# # # # # # # # #         if size in SIZE_NET_WEIGHT:
# # # # # # # # #             total += units * SIZE_NET_WEIGHT[size]
# # # # # # # # #             found = True
# # # # # # # # #     return round(total, 2) if found else None


# # # # # # # # # # ===========================================================================
# # # # # # # # # # Build packing list — grouped by color
# # # # # # # # # # ===========================================================================
# # # # # # # # # def build_grouped(data: dict) -> dict:
# # # # # # # # #     groups: dict = {}
# # # # # # # # #     ctn_counter: dict = {}

# # # # # # # # #     for _, table in data["tables"].items():
# # # # # # # # #         trows = table.get("rows") or []
# # # # # # # # #         total = table.get("total") or {}
# # # # # # # # #         if not trows:
# # # # # # # # #             continue

# # # # # # # # #         first = trows[0]
# # # # # # # # #         if first.get("PrePack Type") != "Multi":
# # # # # # # # #             continue
# # # # # # # # #         if first.get("Full Carton") != "Y":
# # # # # # # # #             continue

# # # # # # # # #         color = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # # # # # # # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # # # # # # # #         row_no = ctn_counter[color]

# # # # # # # # #         ctn_mes     = total.get("#PrePackets Ordered")
# # # # # # # # #         qty_per_ctn = total.get("PrePack Pack Factor") or sum(
# # # # # # # # #             r.get("Units per PrePack") or 0 for r in trows
# # # # # # # # #         )
# # # # # # # # #         total_qty   = total.get("Qty Ordered (eaches)") or sum(
# # # # # # # # #             r.get("Qty Ordered (eaches)") or 0 for r in trows
# # # # # # # # #         )
# # # # # # # # #         prepack = first.get("PrePack")

# # # # # # # # #         net_per_carton = net_weight_per_carton_multi(trows)
# # # # # # # # #         total_net = (
# # # # # # # # #             round(ctn_mes * net_per_carton, 2)
# # # # # # # # #             if (ctn_mes and net_per_carton) else None
# # # # # # # # #         )

# # # # # # # # #         # ---- data row ----
# # # # # # # # #         data_row = {
# # # # # # # # #             "CTN NO":          row_no,
# # # # # # # # #             "CTN MES:":        ctn_mes,
# # # # # # # # #             "CTN QTY":         ctn_mes,
# # # # # # # # #             "COLOR":           color,
# # # # # # # # #             "PREPACK STECKER": str(prepack),
# # # # # # # # #         }
# # # # # # # # #         for r in trows:
# # # # # # # # #             data_row[r["Size Desc"]] = r.get("Units per PrePack")
# # # # # # # # #         data_row["PER BLST"]     = f"{qty_per_ctn} X 1"
# # # # # # # # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # # # # # # # #         data_row["TOTAL QTY"]    = total_qty
# # # # # # # # #         data_row["GROSS WEIGHT"] = None
# # # # # # # # #         data_row["NET WEIGHT"]   = net_per_carton

# # # # # # # # #         # ---- total row ----
# # # # # # # # #         tot = {
# # # # # # # # #             "CTN NO":          "TOTAL",
# # # # # # # # #             "CTN MES:":        None,
# # # # # # # # #             "CTN QTY":         f"{ctn_mes} CTNS" if ctn_mes else None,
# # # # # # # # #             "COLOR":           None,
# # # # # # # # #             "PREPACK STECKER": None,
# # # # # # # # #         }
# # # # # # # # #         for r in trows:
# # # # # # # # #             u = r.get("Units per PrePack") or 0
# # # # # # # # #             tot[r["Size Desc"]] = (ctn_mes * u) if ctn_mes else None
# # # # # # # # #         tot["PER BLST"]     = None
# # # # # # # # #         tot["QTY PER CTN"]  = None
# # # # # # # # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # # # # # # # #         tot["GROSS WEIGHT"] = None
# # # # # # # # #         tot["NET WEIGHT"]   = total_net

# # # # # # # # #         groups.setdefault(color, []).append(data_row)
# # # # # # # # #         groups[color].append(tot)

# # # # # # # # #     return groups


# # # # # # # # # # ===========================================================================
# # # # # # # # # # UI
# # # # # # # # # # ===========================================================================
# # # # # # # # # json_path = st.sidebar.text_input("JSON file path", DEFAULT_JSON)

# # # # # # # # # if not Path(json_path).exists():
# # # # # # # # #     st.error(f"File not found: `{json_path}`")
# # # # # # # # #     st.stop()

# # # # # # # # # data = load_json(json_path)
# # # # # # # # # groups = build_grouped(data)

# # # # # # # # # if not groups:
# # # # # # # # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # # # # # # # #     st.stop()


# # # # # # # # # # ===========================================================================
# # # # # # # # # # Render one table per color
# # # # # # # # # # ===========================================================================
# # # # # # # # # all_frames: list = []

# # # # # # # # # for color, rows in groups.items():
# # # # # # # # #     sizes = present_sizes(rows)
# # # # # # # # #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# # # # # # # # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # # # # # # # #     st.subheader(f"🎨 {color}")
# # # # # # # # #     st.caption(f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s)")

# # # # # # # # #     # --- (A) SIZE → N.W. / N.N.W. / EMPTY CTN WT. reference header ---
# # # # # # # # #     render_size_weight_header(sizes)

# # # # # # # # #     col_cfg = {
# # # # # # # # #         "CTN NO":          st.column_config.TextColumn("CTN NO", width="small"),
# # # # # # # # #         "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small"),
# # # # # # # # #         "CTN QTY":         st.column_config.TextColumn("CTN QTY", width="small"),
# # # # # # # # #         "COLOR":           st.column_config.TextColumn("COLOR", width="medium"),
# # # # # # # # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium"),
# # # # # # # # #         "PER BLST":        st.column_config.TextColumn("PER BLST", width="small"),
# # # # # # # # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small"),
# # # # # # # # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY", width="small"),
# # # # # # # # #         "GROSS WEIGHT":    st.column_config.NumberColumn(
# # # # # # # # #             "GROSS WEIGHT", width="small", format="%.2f"
# # # # # # # # #         ),
# # # # # # # # #         "NET WEIGHT":      st.column_config.NumberColumn(
# # # # # # # # #             "NET WEIGHT", width="small", format="%.2f"
# # # # # # # # #         ),
# # # # # # # # #     }
# # # # # # # # #     for s in sizes:
# # # # # # # # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small")

# # # # # # # # #     try:
# # # # # # # # #         edited = st.data_editor(
# # # # # # # # #             data=df,
# # # # # # # # #             use_container_width=True,
# # # # # # # # #             hide_index=True,
# # # # # # # # #             num_rows="fixed",
# # # # # # # # #             column_config=col_cfg,
# # # # # # # # #             key=f"multi_editor_{color}",
# # # # # # # # #         )
# # # # # # # # #     except TypeError:
# # # # # # # # #         st.warning(
# # # # # # # # #             "Your Streamlit version doesn't support data_editor with these options. "
# # # # # # # # #             "Upgrade with: pip install -U streamlit"
# # # # # # # # #         )
# # # # # # # # #         st.dataframe(df, use_container_width=True, hide_index=True)
# # # # # # # # #         edited = df

# # # # # # # # #     all_frames.append((color, edited))
# # # # # # # # #     st.divider()


# # # # # # # # # # ===========================================================================
# # # # # # # # # # Downloads
# # # # # # # # # # ===========================================================================
# # # # # # # # # st.markdown("### Download")

# # # # # # # # # export_rows: list = []
# # # # # # # # # for i, (_, frame) in enumerate(all_frames):
# # # # # # # # #     if i > 0:
# # # # # # # # #         export_rows.append({})
# # # # # # # # #     export_rows.extend(frame.to_dict(orient="records"))

# # # # # # # # # combined = pd.DataFrame(export_rows)

# # # # # # # # # col1, col2 = st.columns(2)

# # # # # # # # # with col1:
# # # # # # # # #     st.download_button(
# # # # # # # # #         "⬇ Download CSV (all colors)",
# # # # # # # # #         data=combined.to_csv(index=False).encode("utf-8"),
# # # # # # # # #         file_name="packing_list_multi.csv",
# # # # # # # # #         mime="text/csv",
# # # # # # # # #         use_container_width=True,
# # # # # # # # #     )

# # # # # # # # # with col2:
# # # # # # # # #     try:
# # # # # # # # #         buf = io.BytesIO()
# # # # # # # # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # # # # # # # #             for color, frame in all_frames:
# # # # # # # # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # # # # # # # #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# # # # # # # # #         st.download_button(
# # # # # # # # #             "⬇ Download Excel (one sheet per color)",
# # # # # # # # #             data=buf.getvalue(),
# # # # # # # # #             file_name="packing_list_multi.xlsx",
# # # # # # # # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # # # # # # # #             use_container_width=True,
# # # # # # # # #         )
# # # # # # # # #     except ImportError:
# # # # # # # # #         st.info("Install `openpyxl` to enable Excel export:  pip install openpyxl")


# # # # # # # # # # ===========================================================================
# # # # # # # # # # Sidebar info
# # # # # # # # # # ===========================================================================
# # # # # # # # # with st.sidebar:
# # # # # # # # #     st.markdown("### Colors detected")
# # # # # # # # #     for color, rows in groups.items():
# # # # # # # # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # # # # # # # #         st.write(f"- **{color}** — {n} group(s)")



# # # # # # # # """
# # # # # # # # multi_pack.py
# # # # # # # # -------------
# # # # # # # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.
# # # # # # # # Each COLOR gets its own separate table.

# # # # # # # # Reference header: N.W. / N.N.W. / EMPTY CTN WT.
# # # # # # # # Auto-fills: NET WEIGHT = Σ(units × N.W.)
# # # # # # # #             GROSS WEIGHT = Σ(units × N.W.) + EMPTY_CTN_WEIGHT

# # # # # # # # Run:
# # # # # # # #     streamlit run multi_pack.py
# # # # # # # # """

# # # # # # # # import io
# # # # # # # # import json
# # # # # # # # from pathlib import Path

# # # # # # # # import pandas as pd
# # # # # # # # import streamlit as st


# # # # # # # # # ===========================================================================
# # # # # # # # # Config
# # # # # # # # # ===========================================================================
# # # # # # # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # # # # # # st.title("📦 Packing List — Multi Pack (Y)")

# # # # # # # # DEFAULT_JSON = "61480360.json"

# # # # # # # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # # # # # # # --- weights (kg) ----------------------------------------------------------
# # # # # # # # SIZE_NET_WEIGHT = {
# # # # # # # #     "XS":   0.510,
# # # # # # # #     "S":    0.520,
# # # # # # # #     "M":    0.550,
# # # # # # # #     "L":    0.560,
# # # # # # # #     "XL":   0.610,
# # # # # # # #     "XXL":  0.650,
# # # # # # # #     "XXL+": 0.690,
# # # # # # # # }

# # # # # # # # SIZE_NEW_NET_WEIGHT = {
# # # # # # # #     "XS":   0.49,
# # # # # # # #     "S":    0.50,
# # # # # # # #     "M":    0.53,
# # # # # # # #     "L":    0.54,
# # # # # # # #     "XL":   0.59,
# # # # # # # #     "XXL":  0.63,
# # # # # # # #     "XXL+": 0.67,
# # # # # # # # }

# # # # # # # # SIZE_EMPTY_CTN_WEIGHT = {
# # # # # # # #     "XS":   0.49,
# # # # # # # #     "S":    1.0,
# # # # # # # #     "M":    1.0,
# # # # # # # #     "L":    1.0,
# # # # # # # #     "XL":   1.0,
# # # # # # # #     "XXL":  1.0,
# # # # # # # #     "XXL+": 1.0,
# # # # # # # # }

# # # # # # # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # # # # # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # # # # # # ===========================================================================
# # # # # # # # # Helpers
# # # # # # # # # ===========================================================================
# # # # # # # # @st.cache_data(show_spinner=False)
# # # # # # # # def load_json(path: str) -> dict:
# # # # # # # #     with open(path, "r", encoding="utf-8") as f:
# # # # # # # #         return json.load(f)


# # # # # # # # def color_display(raw: str) -> str:
# # # # # # # #     """'000905518-000 TEAKWOOD' → 'TEAKWOOD'"""
# # # # # # # #     if not raw:
# # # # # # # #         return ""
# # # # # # # #     parts = raw.rsplit(" ", 1)
# # # # # # # #     return parts[-1] if len(parts) > 1 else raw


# # # # # # # # def present_sizes(rows: list) -> list:
# # # # # # # #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # # # # # # # def render_size_weight_header(sizes: list) -> None:
# # # # # # # #     """
# # # # # # # #     Reference table shown above every packing table:
# # # # # # # #         SIZE           XS     S      M      L      XL     XXL    XXL+
# # # # # # # #         N.W.           0.510  ...
# # # # # # # #         N.N.W.         0.490  ...
# # # # # # # #         EMPTY CTN WT.  0.490  ...
# # # # # # # #     """
# # # # # # # #     rows = {
# # # # # # # #         "N.W.":          [f"{SIZE_NET_WEIGHT[s]:.3f}"       for s in sizes],
# # # # # # # #         "N.N.W.":        [f"{SIZE_NEW_NET_WEIGHT[s]:.3f}"   for s in sizes],
# # # # # # # #         "EMPTY CTN WT.": [f"{SIZE_EMPTY_CTN_WEIGHT[s]:.3f}" for s in sizes],
# # # # # # # #     }
# # # # # # # #     header_df = pd.DataFrame(rows, index=sizes).T
# # # # # # # #     header_df.index.name = "SIZE"
# # # # # # # #     st.dataframe(header_df, use_container_width=False)


# # # # # # # # def _empty_ctn_weight_for(sizes: list) -> float:
# # # # # # # #     """
# # # # # # # #     Multi Pack: one carton holds all sizes.
# # # # # # # #     Use the max of EMPTY_CTN_WEIGHT over the sizes present
# # # # # # # #     (in your data that yields 1.0).
# # # # # # # #     """
# # # # # # # #     weights = [SIZE_EMPTY_CTN_WEIGHT.get(s) for s in sizes]
# # # # # # # #     weights = [w for w in weights if w is not None]
# # # # # # # #     return max(weights) if weights else 0.0


# # # # # # # # def net_weight_per_carton_multi(rows: list):
# # # # # # # #     """Per-carton NET = Σ(units × N.W.)."""
# # # # # # # #     total, found = 0.0, False
# # # # # # # #     for r in rows:
# # # # # # # #         size  = r.get("Size Desc")
# # # # # # # #         units = r.get("Units per PrePack") or 0
# # # # # # # #         if size in SIZE_NET_WEIGHT:
# # # # # # # #             total += units * SIZE_NET_WEIGHT[size]
# # # # # # # #             found = True
# # # # # # # #     return round(total, 2) if found else None


# # # # # # # # def gross_weight_per_carton_multi(rows: list, sizes: list):
# # # # # # # #     """Per-carton GROSS = Σ(units × N.W.) + EMPTY_CTN_WEIGHT."""
# # # # # # # #     net = net_weight_per_carton_multi(rows)
# # # # # # # #     if net is None:
# # # # # # # #         return None
# # # # # # # #     empty = _empty_ctn_weight_for(sizes)
# # # # # # # #     return round(net + empty, 2)


# # # # # # # # # ===========================================================================
# # # # # # # # # Build packing list — grouped by color
# # # # # # # # # ===========================================================================
# # # # # # # # def build_grouped(data: dict) -> dict:
# # # # # # # #     groups: dict = {}
# # # # # # # #     ctn_counter: dict = {}

# # # # # # # #     for _, table in data["tables"].items():
# # # # # # # #         trows = table.get("rows") or []
# # # # # # # #         total = table.get("total") or {}
# # # # # # # #         if not trows:
# # # # # # # #             continue

# # # # # # # #         first = trows[0]
# # # # # # # #         if first.get("PrePack Type") != "Multi":
# # # # # # # #             continue
# # # # # # # #         if first.get("Full Carton") != "Y":
# # # # # # # #             continue

# # # # # # # #         color = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # # # # # # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # # # # # # #         row_no = ctn_counter[color]

# # # # # # # #         ctn_mes     = total.get("#PrePackets Ordered")
# # # # # # # #         qty_per_ctn = total.get("PrePack Pack Factor") or sum(
# # # # # # # #             r.get("Units per PrePack") or 0 for r in trows
# # # # # # # #         )
# # # # # # # #         total_qty   = total.get("Qty Ordered (eaches)") or sum(
# # # # # # # #             r.get("Qty Ordered (eaches)") or 0 for r in trows
# # # # # # # #         )
# # # # # # # #         prepack = first.get("PrePack")

# # # # # # # #         sizes = [r.get("Size Desc") for r in trows if r.get("Size Desc")]

# # # # # # # #         net_per_carton   = net_weight_per_carton_multi(trows)
# # # # # # # #         gross_per_carton = gross_weight_per_carton_multi(trows, sizes)

# # # # # # # #         total_net = (
# # # # # # # #             round(ctn_mes * net_per_carton, 2)
# # # # # # # #             if (ctn_mes and net_per_carton) else None
# # # # # # # #         )
# # # # # # # #         total_gross = (
# # # # # # # #             round(ctn_mes * gross_per_carton, 2)
# # # # # # # #             if (ctn_mes and gross_per_carton) else None
# # # # # # # #         )

# # # # # # # #         # ---- data row ----
# # # # # # # #         data_row = {
# # # # # # # #             "CTN NO":          row_no,
# # # # # # # #             "CTN MES:":        ctn_mes,
# # # # # # # #             "CTN QTY":         ctn_mes,
# # # # # # # #             "COLOR":           color,
# # # # # # # #             "PREPACK STECKER": str(prepack),
# # # # # # # #         }
# # # # # # # #         for r in trows:
# # # # # # # #             data_row[r["Size Desc"]] = r.get("Units per PrePack")
# # # # # # # #         data_row["PER BLST"]     = f"{qty_per_ctn} X 1"
# # # # # # # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # # # # # # #         data_row["TOTAL QTY"]    = total_qty
# # # # # # # #         data_row["GROSS WEIGHT"] = gross_per_carton
# # # # # # # #         data_row["NET WEIGHT"]   = net_per_carton

# # # # # # # #         # ---- total row ----
# # # # # # # #         tot = {
# # # # # # # #             "CTN NO":          "TOTAL",
# # # # # # # #             "CTN MES:":        None,
# # # # # # # #             "CTN QTY":         f"{ctn_mes} CTNS" if ctn_mes else None,
# # # # # # # #             "COLOR":           None,
# # # # # # # #             "PREPACK STECKER": None,
# # # # # # # #         }
# # # # # # # #         for r in trows:
# # # # # # # #             u = r.get("Units per PrePack") or 0
# # # # # # # #             tot[r["Size Desc"]] = (ctn_mes * u) if ctn_mes else None
# # # # # # # #         tot["PER BLST"]     = None
# # # # # # # #         tot["QTY PER CTN"]  = None
# # # # # # # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # # # # # # #         tot["GROSS WEIGHT"] = total_gross
# # # # # # # #         tot["NET WEIGHT"]   = total_net

# # # # # # # #         groups.setdefault(color, []).append(data_row)
# # # # # # # #         groups[color].append(tot)

# # # # # # # #     return groups


# # # # # # # # # ===========================================================================
# # # # # # # # # UI
# # # # # # # # # ===========================================================================
# # # # # # # # json_path = st.sidebar.text_input("JSON file path", DEFAULT_JSON)

# # # # # # # # if not Path(json_path).exists():
# # # # # # # #     st.error(f"File not found: `{json_path}`")
# # # # # # # #     st.stop()

# # # # # # # # data = load_json(json_path)
# # # # # # # # groups = build_grouped(data)

# # # # # # # # if not groups:
# # # # # # # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # # # # # # #     st.stop()


# # # # # # # # # ===========================================================================
# # # # # # # # # Render one table per color
# # # # # # # # # ===========================================================================
# # # # # # # # all_frames: list = []

# # # # # # # # for color, rows in groups.items():
# # # # # # # #     sizes = present_sizes(rows)
# # # # # # # #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# # # # # # # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # # # # # # #     st.subheader(f"🎨 {color}")
# # # # # # # #     st.caption(f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s)")

# # # # # # # #     # --- (A) reference header: N.W. / N.N.W. / EMPTY CTN WT. ---
# # # # # # # #     render_size_weight_header(sizes)

# # # # # # # #     col_cfg = {
# # # # # # # #         "CTN NO":          st.column_config.TextColumn("CTN NO", width="small"),
# # # # # # # #         "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small"),
# # # # # # # #         "CTN QTY":         st.column_config.TextColumn("CTN QTY", width="small"),
# # # # # # # #         "COLOR":           st.column_config.TextColumn("COLOR", width="medium"),
# # # # # # # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium"),
# # # # # # # #         "PER BLST":        st.column_config.TextColumn("PER BLST", width="small"),
# # # # # # # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small"),
# # # # # # # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY", width="small"),
# # # # # # # #         "GROSS WEIGHT":    st.column_config.NumberColumn(
# # # # # # # #             "GROSS WEIGHT", width="small", format="%.2f"
# # # # # # # #         ),
# # # # # # # #         "NET WEIGHT":      st.column_config.NumberColumn(
# # # # # # # #             "NET WEIGHT", width="small", format="%.2f"
# # # # # # # #         ),
# # # # # # # #     }
# # # # # # # #     for s in sizes:
# # # # # # # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small")

# # # # # # # #     try:
# # # # # # # #         edited = st.data_editor(
# # # # # # # #             data=df,
# # # # # # # #             use_container_width=True,
# # # # # # # #             hide_index=True,
# # # # # # # #             num_rows="fixed",
# # # # # # # #             column_config=col_cfg,
# # # # # # # #             key=f"multi_editor_{color}",
# # # # # # # #         )
# # # # # # # #     except TypeError:
# # # # # # # #         st.warning(
# # # # # # # #             "Your Streamlit version doesn't support data_editor with these options. "
# # # # # # # #             "Upgrade with: pip install -U streamlit"
# # # # # # # #         )
# # # # # # # #         st.dataframe(df, use_container_width=True, hide_index=True)
# # # # # # # #         edited = df

# # # # # # # #     all_frames.append((color, edited))
# # # # # # # #     st.divider()


# # # # # # # # # ===========================================================================
# # # # # # # # # Downloads
# # # # # # # # # ===========================================================================
# # # # # # # # st.markdown("### Download")

# # # # # # # # export_rows: list = []
# # # # # # # # for i, (_, frame) in enumerate(all_frames):
# # # # # # # #     if i > 0:
# # # # # # # #         export_rows.append({})
# # # # # # # #     export_rows.extend(frame.to_dict(orient="records"))

# # # # # # # # combined = pd.DataFrame(export_rows)

# # # # # # # # col1, col2 = st.columns(2)

# # # # # # # # with col1:
# # # # # # # #     st.download_button(
# # # # # # # #         "⬇ Download CSV (all colors)",
# # # # # # # #         data=combined.to_csv(index=False).encode("utf-8"),
# # # # # # # #         file_name="packing_list_multi.csv",
# # # # # # # #         mime="text/csv",
# # # # # # # #         use_container_width=True,
# # # # # # # #     )

# # # # # # # # with col2:
# # # # # # # #     try:
# # # # # # # #         buf = io.BytesIO()
# # # # # # # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # # # # # # #             for color, frame in all_frames:
# # # # # # # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # # # # # # #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# # # # # # # #         st.download_button(
# # # # # # # #             "⬇ Download Excel (one sheet per color)",
# # # # # # # #             data=buf.getvalue(),
# # # # # # # #             file_name="packing_list_multi.xlsx",
# # # # # # # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # # # # # # #             use_container_width=True,
# # # # # # # #         )
# # # # # # # #     except ImportError:
# # # # # # # #         st.info("Install `openpyxl` to enable Excel export:  pip install openpyxl")


# # # # # # # # # ===========================================================================
# # # # # # # # # Sidebar info
# # # # # # # # # ===========================================================================
# # # # # # # # with st.sidebar:
# # # # # # # #     st.markdown("### Colors detected")
# # # # # # # #     for color, rows in groups.items():
# # # # # # # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # # # # # # #         st.write(f"- **{color}** — {n} group(s)")




# # # # # # # """
# # # # # # # multi_pack.py
# # # # # # # -------------
# # # # # # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.
# # # # # # # Each COLOR gets its own separate table.

# # # # # # # Reference header: N.W. / N.N.W. / EMPTY CTN WT. — all editable in sidebar.
# # # # # # # Auto-fills: NET WEIGHT   = Σ(units × N.W.)
# # # # # # #             GROSS WEIGHT = Σ(units × N.W.) + EMPTY_CTN_WEIGHT

# # # # # # # Run:
# # # # # # #     streamlit run multi_pack.py
# # # # # # # """

# # # # # # # import io
# # # # # # # import json
# # # # # # # from pathlib import Path

# # # # # # # import pandas as pd
# # # # # # # import streamlit as st


# # # # # # # # ===========================================================================
# # # # # # # # Config
# # # # # # # # ===========================================================================
# # # # # # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # # # # # st.title("📦 Packing List — Multi Pack (Y)")

# # # # # # # DEFAULT_JSON = "61480360.json"

# # # # # # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # # # # # # --- defaults (kg) — editable from the sidebar -----------------------------
# # # # # # # DEFAULT_NW = {
# # # # # # #     "XS":   0.510, "S":  0.520, "M":  0.550, "L":  0.560,
# # # # # # #     "XL":   0.610, "XXL": 0.650, "XXL+": 0.690,
# # # # # # # }
# # # # # # # DEFAULT_NNW = {
# # # # # # #     "XS":   0.49,  "S":  0.50,  "M":  0.53,  "L":  0.54,
# # # # # # #     "XL":   0.59,  "XXL": 0.63,  "XXL+": 0.67,
# # # # # # # }
# # # # # # # DEFAULT_EMPTY = {
# # # # # # #     "XS":   0.49,  "S":  1.0,   "M":  1.0,   "L":  1.0,
# # # # # # #     "XL":   1.0,   "XXL": 1.0,   "XXL+": 1.0,
# # # # # # # }

# # # # # # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # # # # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # # # # # ===========================================================================
# # # # # # # # Session state — weight tables
# # # # # # # # ===========================================================================
# # # # # # # def _init_state():
# # # # # # #     if "weights_df" not in st.session_state:
# # # # # # #         st.session_state.weights_df = pd.DataFrame(
# # # # # # #             {
# # # # # # #                 "SIZE":          SIZE_ORDER,
# # # # # # #                 "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
# # # # # # #                 "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
# # # # # # #                 "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
# # # # # # #             }
# # # # # # #         ).set_index("SIZE")

# # # # # # #     if "weights_reset" not in st.session_state:
# # # # # # #         st.session_state.weights_reset = False


# # # # # # # def get_weights() -> tuple[dict, dict, dict]:
# # # # # # #     """Return (NW, NNW, EMPTY) dicts from the current session state."""
# # # # # # #     df = st.session_state.weights_df
# # # # # # #     nw    = {s: float(df.loc[s, "N.W."])          for s in df.index}
# # # # # # #     nnw   = {s: float(df.loc[s, "N.N.W."])        for s in df.index}
# # # # # # #     empty = {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index}
# # # # # # #     return nw, nnw, empty


# # # # # # # # ===========================================================================
# # # # # # # # Helpers
# # # # # # # # ===========================================================================
# # # # # # # @st.cache_data(show_spinner=False)
# # # # # # # def load_json(path: str) -> dict:
# # # # # # #     with open(path, "r", encoding="utf-8") as f:
# # # # # # #         return json.load(f)


# # # # # # # def color_display(raw: str) -> str:
# # # # # # #     if not raw:
# # # # # # #         return ""
# # # # # # #     parts = raw.rsplit(" ", 1)
# # # # # # #     return parts[-1] if len(parts) > 1 else raw


# # # # # # # def present_sizes(rows: list) -> list:
# # # # # # #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # # # # # # def render_size_weight_header(sizes: list, weights_df: pd.DataFrame) -> None:
# # # # # # #     """
# # # # # # #     Read-only reference table shown above each packing table:
# # # # # # #         SIZE           XS     S      M      L      XL     XXL    XXL+
# # # # # # #         N.W.           ...
# # # # # # #         N.N.W.         ...
# # # # # # #         EMPTY CTN WT.  ...
# # # # # # #     Values come from the sidebar-edited weights_df.
# # # # # # #     """
# # # # # # #     sub = weights_df.loc[sizes]                       # rows = sizes
# # # # # # #     header_df = sub.T                                 # rows = weight types
# # # # # # #     header_df.index.name = "SIZE"
# # # # # # #     st.dataframe(header_df.style.format("{:.3f}"), use_container_width=False)


# # # # # # # def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
# # # # # # #     """Multi Pack: use the max EMPTY CTN WT. over the sizes present."""
# # # # # # #     ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
# # # # # # #     return max(ws) if ws else 0.0


# # # # # # # def net_weight_per_carton_multi(rows: list, nw: dict):
# # # # # # #     """Per-carton NET = Σ(units × N.W.)."""
# # # # # # #     total, found = 0.0, False
# # # # # # #     for r in rows:
# # # # # # #         size  = r.get("Size Desc")
# # # # # # #         units = r.get("Units per PrePack") or 0
# # # # # # #         if size in nw:
# # # # # # #             total += units * nw[size]
# # # # # # #             found = True
# # # # # # #     return round(total, 2) if found else None


# # # # # # # def gross_weight_per_carton_multi(rows: list, sizes: list, nw: dict, empty_weights: dict):
# # # # # # #     """Per-carton GROSS = Σ(units × N.W.) + EMPTY_CTN_WEIGHT."""
# # # # # # #     net = net_weight_per_carton_multi(rows, nw)
# # # # # # #     if net is None:
# # # # # # #         return None
# # # # # # #     return round(net + _empty_ctn_weight_for(sizes, empty_weights), 2)


# # # # # # # # ===========================================================================
# # # # # # # # Build packing list — grouped by color
# # # # # # # # ===========================================================================
# # # # # # # def build_grouped(data: dict, nw: dict, empty_weights: dict) -> dict:
# # # # # # #     groups: dict = {}
# # # # # # #     ctn_counter: dict = {}

# # # # # # #     for _, table in data["tables"].items():
# # # # # # #         trows = table.get("rows") or []
# # # # # # #         total = table.get("total") or {}
# # # # # # #         if not trows:
# # # # # # #             continue

# # # # # # #         first = trows[0]
# # # # # # #         if first.get("PrePack Type") != "Multi":
# # # # # # #             continue
# # # # # # #         if first.get("Full Carton") != "Y":
# # # # # # #             continue

# # # # # # #         color = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # # # # # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # # # # # #         row_no = ctn_counter[color]

# # # # # # #         ctn_mes     = total.get("#PrePackets Ordered")
# # # # # # #         qty_per_ctn = total.get("PrePack Pack Factor") or sum(
# # # # # # #             r.get("Units per PrePack") or 0 for r in trows
# # # # # # #         )
# # # # # # #         total_qty   = total.get("Qty Ordered (eaches)") or sum(
# # # # # # #             r.get("Qty Ordered (eaches)") or 0 for r in trows
# # # # # # #         )
# # # # # # #         prepack = first.get("PrePack")

# # # # # # #         sizes = [r.get("Size Desc") for r in trows if r.get("Size Desc")]

# # # # # # #         net_per_carton   = net_weight_per_carton_multi(trows, nw)
# # # # # # #         gross_per_carton = gross_weight_per_carton_multi(trows, sizes, nw, empty_weights)

# # # # # # #         total_net   = round(ctn_mes * net_per_carton,   2) if (ctn_mes and net_per_carton)   else None
# # # # # # #         total_gross = round(ctn_mes * gross_per_carton, 2) if (ctn_mes and gross_per_carton) else None

# # # # # # #         # ---- data row ----
# # # # # # #         data_row = {
# # # # # # #             "CTN NO":          row_no,
# # # # # # #             "CTN MES:":        ctn_mes,
# # # # # # #             "CTN QTY":         ctn_mes,
# # # # # # #             "COLOR":           color,
# # # # # # #             "PREPACK STECKER": str(prepack),
# # # # # # #         }
# # # # # # #         for r in trows:
# # # # # # #             data_row[r["Size Desc"]] = r.get("Units per PrePack")
# # # # # # #         data_row["PER BLST"]     = f"{qty_per_ctn} X 1"
# # # # # # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # # # # # #         data_row["TOTAL QTY"]    = total_qty
# # # # # # #         data_row["GROSS WEIGHT"] = gross_per_carton
# # # # # # #         data_row["NET WEIGHT"]   = net_per_carton

# # # # # # #         # ---- total row ----
# # # # # # #         tot = {
# # # # # # #             "CTN NO":          "TOTAL",
# # # # # # #             "CTN MES:":        None,
# # # # # # #             "CTN QTY":         f"{ctn_mes} CTNS" if ctn_mes else None,
# # # # # # #             "COLOR":           None,
# # # # # # #             "PREPACK STECKER": None,
# # # # # # #         }
# # # # # # #         for r in trows:
# # # # # # #             u = r.get("Units per PrePack") or 0
# # # # # # #             tot[r["Size Desc"]] = (ctn_mes * u) if ctn_mes else None
# # # # # # #         tot["PER BLST"]     = None
# # # # # # #         tot["QTY PER CTN"]  = None
# # # # # # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # # # # # #         tot["GROSS WEIGHT"] = total_gross
# # # # # # #         tot["NET WEIGHT"]   = total_net

# # # # # # #         groups.setdefault(color, []).append(data_row)
# # # # # # #         groups[color].append(tot)

# # # # # # #     return groups


# # # # # # # # ===========================================================================
# # # # # # # # UI
# # # # # # # # ===========================================================================
# # # # # # # _init_state()

# # # # # # # # --- Sidebar: editable weight tables --------------------------------------
# # # # # # # with st.sidebar:
# # # # # # #     st.markdown("### ⚖️ Weight settings (kg)")
# # # # # # #     st.caption("Edit any cell — values recalculate instantly.")

# # # # # # #     edited_weights = st.data_editor(
# # # # # # #         st.session_state.weights_df,
# # # # # # #         use_container_width=True,
# # # # # # #         num_rows="fixed",
# # # # # # #         column_config={
# # # # # # #             "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
# # # # # # #             "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
# # # # # # #             "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
# # # # # # #         },
# # # # # # #         key="weights_editor",
# # # # # # #     )

# # # # # # #     # persist edits
# # # # # # #     if not edited_weights.equals(st.session_state.weights_df):
# # # # # # #         st.session_state.weights_df = edited_weights

# # # # # # #     if st.button("↺ Reset to defaults", use_container_width=True):
# # # # # # #         st.session_state.weights_df = pd.DataFrame(
# # # # # # #             {
# # # # # # #                 "SIZE":          SIZE_ORDER,
# # # # # # #                 "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
# # # # # # #                 "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
# # # # # # #                 "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
# # # # # # #             }
# # # # # # #         ).set_index("SIZE")
# # # # # # #         st.rerun()

# # # # # # #     st.divider()
# # # # # # #     json_path = st.text_input("JSON file path", DEFAULT_JSON)

# # # # # # # # --- Load + compute --------------------------------------------------------
# # # # # # # if not Path(json_path).exists():
# # # # # # #     st.error(f"File not found: `{json_path}`")
# # # # # # #     st.stop()

# # # # # # # nw, nnw, empty_weights = get_weights()
# # # # # # # data = load_json(json_path)
# # # # # # # groups = build_grouped(data, nw, empty_weights)

# # # # # # # if not groups:
# # # # # # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # # # # # #     st.stop()


# # # # # # # # ===========================================================================
# # # # # # # # Render one table per color
# # # # # # # # ===========================================================================
# # # # # # # all_frames: list = []

# # # # # # # for color, rows in groups.items():
# # # # # # #     sizes = present_sizes(rows)
# # # # # # #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# # # # # # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # # # # # #     st.subheader(f"🎨 {color}")
# # # # # # #     st.caption(f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s)")

# # # # # # #     # --- (A) reference header: N.W. / N.N.W. / EMPTY CTN WT. ---
# # # # # # #     render_size_weight_header(sizes, st.session_state.weights_df)

# # # # # # #     col_cfg = {
# # # # # # #         "CTN NO":          st.column_config.TextColumn("CTN NO", width="small"),
# # # # # # #         "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small"),
# # # # # # #         "CTN QTY":         st.column_config.TextColumn("CTN QTY", width="small"),
# # # # # # #         "COLOR":           st.column_config.TextColumn("COLOR", width="medium"),
# # # # # # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium"),
# # # # # # #         "PER BLST":        st.column_config.TextColumn("PER BLST", width="small"),
# # # # # # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small"),
# # # # # # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY", width="small"),
# # # # # # #         "GROSS WEIGHT":    st.column_config.NumberColumn(
# # # # # # #             "GROSS WEIGHT", width="small", format="%.2f"
# # # # # # #         ),
# # # # # # #         "NET WEIGHT":      st.column_config.NumberColumn(
# # # # # # #             "NET WEIGHT", width="small", format="%.2f"
# # # # # # #         ),
# # # # # # #     }
# # # # # # #     for s in sizes:
# # # # # # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small")

# # # # # # #     try:
# # # # # # #         edited = st.data_editor(
# # # # # # #             data=df,
# # # # # # #             use_container_width=True,
# # # # # # #             hide_index=True,
# # # # # # #             num_rows="fixed",
# # # # # # #             column_config=col_cfg,
# # # # # # #             key=f"multi_editor_{color}",
# # # # # # #         )
# # # # # # #     except TypeError:
# # # # # # #         st.warning(
# # # # # # #             "Your Streamlit version doesn't support data_editor with these options. "
# # # # # # #             "Upgrade with: pip install -U streamlit"
# # # # # # #         )
# # # # # # #         st.dataframe(df, use_container_width=True, hide_index=True)
# # # # # # #         edited = df

# # # # # # #     all_frames.append((color, edited))
# # # # # # #     st.divider()


# # # # # # # # ===========================================================================
# # # # # # # # Downloads
# # # # # # # # ===========================================================================
# # # # # # # st.markdown("### Download")

# # # # # # # export_rows: list = []
# # # # # # # for i, (_, frame) in enumerate(all_frames):
# # # # # # #     if i > 0:
# # # # # # #         export_rows.append({})
# # # # # # #     export_rows.extend(frame.to_dict(orient="records"))

# # # # # # # combined = pd.DataFrame(export_rows)

# # # # # # # col1, col2 = st.columns(2)

# # # # # # # with col1:
# # # # # # #     st.download_button(
# # # # # # #         "⬇ Download CSV (all colors)",
# # # # # # #         data=combined.to_csv(index=False).encode("utf-8"),
# # # # # # #         file_name="packing_list_multi.csv",
# # # # # # #         mime="text/csv",
# # # # # # #         use_container_width=True,
# # # # # # #     )

# # # # # # # with col2:
# # # # # # #     try:
# # # # # # #         buf = io.BytesIO()
# # # # # # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # # # # # #             # weights sheet
# # # # # # #             st.session_state.weights_df.to_excel(writer, sheet_name="Weights")
# # # # # # #             # one sheet per color
# # # # # # #             for color, frame in all_frames:
# # # # # # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # # # # # #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# # # # # # #         st.download_button(
# # # # # # #             "⬇ Download Excel (one sheet per color)",
# # # # # # #             data=buf.getvalue(),
# # # # # # #             file_name="packing_list_multi.xlsx",
# # # # # # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # # # # # #             use_container_width=True,
# # # # # # #         )
# # # # # # #     except ImportError:
# # # # # # #         st.info("Install `openpyxl` to enable Excel export:  pip install openpyxl")


# # # # # # # # ===========================================================================
# # # # # # # # Sidebar info
# # # # # # # # ===========================================================================
# # # # # # # with st.sidebar:
# # # # # # #     st.markdown("### Colors detected")
# # # # # # #     for color, rows in groups.items():
# # # # # # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # # # # # #         st.write(f"- **{color}** — {n} group(s)")



# # # # # # """
# # # # # # multi_pack.py
# # # # # # -------------
# # # # # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.
# # # # # # Each COLOR gets its own separate table.

# # # # # # - Reference header (editable): N.W. / N.N.W. / EMPTY CTN WT.
# # # # # # - Size cells are editable → recalculates:
# # # # # #       QTY PER CTN   = Σ units_per_size
# # # # # #       PER BLST      = "Σ units_per_size X C"   (C = sidebar number, default 1)
# # # # # #       NET WEIGHT    = Σ(units × N.W.)
# # # # # #       GROSS WEIGHT  = Σ(units × N.W.) + EMPTY_CTN_WEIGHT
# # # # # #       TOTAL row     = recalculated from current size cells

# # # # # # Run:
# # # # # #     streamlit run multi_pack.py
# # # # # # """

# # # # # # import io
# # # # # # import json
# # # # # # from pathlib import Path

# # # # # # import pandas as pd
# # # # # # import streamlit as st


# # # # # # # ===========================================================================
# # # # # # # Config
# # # # # # # ===========================================================================
# # # # # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # # # # st.title("📦 Packing List — Multi Pack (Y)")

# # # # # # DEFAULT_JSON = "61480360.json"

# # # # # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # # # # DEFAULT_NW = {
# # # # # #     "XS":   0.510, "S":  0.520, "M":  0.550, "L":  0.560,
# # # # # #     "XL":   0.610, "XXL": 0.650, "XXL+": 0.690,
# # # # # # }
# # # # # # DEFAULT_NNW = {
# # # # # #     "XS":   0.49,  "S":  0.50,  "M":  0.53,  "L":  0.54,
# # # # # #     "XL":   0.59,  "XXL": 0.63,  "XXL+": 0.67,
# # # # # # }
# # # # # # DEFAULT_EMPTY = {
# # # # # #     "XS":   0.49,  "S":  1.0,   "M":  1.0,   "L":  1.0,
# # # # # #     "XL":   1.0,   "XXL": 1.0,   "XXL+": 1.0,
# # # # # # }

# # # # # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # # # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # # # # ===========================================================================
# # # # # # # Session state
# # # # # # # ===========================================================================
# # # # # # def _default_weights_df() -> pd.DataFrame:
# # # # # #     return pd.DataFrame(
# # # # # #         {
# # # # # #             "SIZE":          SIZE_ORDER,
# # # # # #             "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
# # # # # #             "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
# # # # # #             "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
# # # # # #         }
# # # # # #     ).set_index("SIZE")


# # # # # # def _init_state():
# # # # # #     if "weights_df" not in st.session_state:
# # # # # #         st.session_state.weights_df = _default_weights_df()
# # # # # #     if "size_edits" not in st.session_state:
# # # # # #         st.session_state.size_edits = {}       # { color: { prepack: { size: units } } }


# # # # # # def get_weights() -> dict:
# # # # # #     df = st.session_state.weights_df
# # # # # #     return {
# # # # # #         "NW":    {s: float(df.loc[s, "N.W."])          for s in df.index},
# # # # # #         "NNW":   {s: float(df.loc[s, "N.N.W."])        for s in df.index},
# # # # # #         "EMPTY": {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index},
# # # # # #     }


# # # # # # # ===========================================================================
# # # # # # # Helpers
# # # # # # # ===========================================================================
# # # # # # @st.cache_data(show_spinner=False)
# # # # # # def load_json(path: str) -> dict:
# # # # # #     with open(path, "r", encoding="utf-8") as f:
# # # # # #         return json.load(f)


# # # # # # def color_display(raw: str) -> str:
# # # # # #     if not raw:
# # # # # #         return ""
# # # # # #     parts = raw.rsplit(" ", 1)
# # # # # #     return parts[-1] if len(parts) > 1 else raw


# # # # # # def present_sizes(rows: list) -> list:
# # # # # #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # # # # # def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
# # # # # #     ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
# # # # # #     return max(ws) if ws else 0.0


# # # # # # def render_size_weight_header(sizes: list, key_suffix: str = "") -> None:
# # # # # #     master = st.session_state.weights_df
# # # # # #     view = master.loc[sizes].T.copy()
# # # # # #     view.index.name = "SIZE"

# # # # # #     edited = st.data_editor(
# # # # # #         view,
# # # # # #         use_container_width=False,
# # # # # #         num_rows="fixed",
# # # # # #         column_config={
# # # # # #             s: st.column_config.NumberColumn(s, format="%.3f", step=0.001, width="small")
# # # # # #             for s in view.columns
# # # # # #         },
# # # # # #         key=f"header_editor_{key_suffix}",
# # # # # #     )

# # # # # #     if not edited.equals(view):
# # # # # #         for s in edited.columns:
# # # # # #             st.session_state.weights_df.loc[s, "N.W."]          = float(edited.loc["N.W.", s])
# # # # # #             st.session_state.weights_df.loc[s, "N.N.W."]        = float(edited.loc["N.N.W.", s])
# # # # # #             st.session_state.weights_df.loc[s, "EMPTY CTN WT."] = float(edited.loc["EMPTY CTN WT.", s])
# # # # # #         st.rerun()


# # # # # # # ===========================================================================
# # # # # # # Build packing list — grouped by color (uses session_state.size_edits)
# # # # # # # ===========================================================================
# # # # # # def build_grouped(data: dict, nw: dict, empty_weights: dict, blst_c: int) -> dict:
# # # # # #     groups: dict = {}
# # # # # #     ctn_counter: dict = {}

# # # # # #     for _, table in data["tables"].items():
# # # # # #         trows = table.get("rows") or []
# # # # # #         total = table.get("total") or {}
# # # # # #         if not trows:
# # # # # #             continue

# # # # # #         first = trows[0]
# # # # # #         if first.get("PrePack Type") != "Multi":
# # # # # #             continue
# # # # # #         if first.get("Full Carton") != "Y":
# # # # # #             continue

# # # # # #         color   = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # # # # #         prepack = str(first.get("PrePack"))
# # # # # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # # # # #         row_no = ctn_counter[color]

# # # # # #         # ----- current units per size (session overrides JSON) -----
# # # # # #         edits = st.session_state.size_edits.get(color, {}).get(prepack, {})
# # # # # #         row_sizes = []                             # [(size, units), ...]
# # # # # #         for r in trows:
# # # # # #             size  = r["Size Desc"]
# # # # # #             units = int(edits.get(size, r.get("Units per PrePack") or 0))
# # # # # #             row_sizes.append((size, units))

# # # # # #         sizes_present = [s for s, _ in row_sizes]

# # # # # #         # ----- derived values from current size units -----
# # # # # #         sum_units   = sum(u for _, u in row_sizes)
# # # # # #         qty_per_ctn = sum_units                                # ← Σ units_per_size
# # # # # #         per_blst    = f"{sum_units} X {blst_c}"

# # # # # #         net_per_carton   = round(sum(u * nw.get(s, 0.0) for s, u in row_sizes), 2)
# # # # # #         empty_ctn_weight = _empty_ctn_weight_for(sizes_present, empty_weights)
# # # # # #         gross_per_carton = round(net_per_carton + empty_ctn_weight, 2)

# # # # # #         ctn_mes    = total.get("#PrePackets Ordered")
# # # # # #         total_qty  = total.get("Qty Ordered (eaches)") or sum(
# # # # # #             r.get("Qty Ordered (eaches)") or 0 for r in trows
# # # # # #         )

# # # # # #         total_net   = round(ctn_mes * net_per_carton,   2) if ctn_mes else None
# # # # # #         total_gross = round(ctn_mes * gross_per_carton, 2) if ctn_mes else None

# # # # # #         # ----- data row -----
# # # # # #         data_row = {
# # # # # #             "CTN NO":          row_no,
# # # # # #             "CTN MES:":        ctn_mes,
# # # # # #             "CTN QTY":         ctn_mes,
# # # # # #             "COLOR":           color,
# # # # # #             "PREPACK STECKER": prepack,
# # # # # #         }
# # # # # #         for s, u in row_sizes:
# # # # # #             data_row[s] = u
# # # # # #         data_row["PER BLST"]     = per_blst
# # # # # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # # # # #         data_row["TOTAL QTY"]    = total_qty
# # # # # #         data_row["GROSS WEIGHT"] = gross_per_carton
# # # # # #         data_row["NET WEIGHT"]   = net_per_carton

# # # # # #         # ----- total row -----
# # # # # #         tot = {
# # # # # #             "CTN NO":          "TOTAL",
# # # # # #             "CTN MES:":        None,
# # # # # #             "CTN QTY":         f"{ctn_mes} CTNS" if ctn_mes else None,
# # # # # #             "COLOR":           None,
# # # # # #             "PREPACK STECKER": None,
# # # # # #         }
# # # # # #         for s, u in row_sizes:
# # # # # #             tot[s] = (ctn_mes * u) if ctn_mes else None
# # # # # #         tot["PER BLST"]     = None
# # # # # #         tot["QTY PER CTN"]  = None
# # # # # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # # # # #         tot["GROSS WEIGHT"] = total_gross
# # # # # #         tot["NET WEIGHT"]   = total_net

# # # # # #         groups.setdefault(color, []).append(data_row)
# # # # # #         groups[color].append(tot)

# # # # # #     return groups


# # # # # # # ===========================================================================
# # # # # # # Detect size-cell edits and persist them
# # # # # # # ===========================================================================
# # # # # # def _persist_size_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
# # # # # #     """Return True if a rerun was triggered."""
# # # # # #     if not sizes:
# # # # # #         return False

# # # # # #     # only look at data rows (CTN NO != "TOTAL")
# # # # # #     mask = df["CTN NO"].astype(str) != "TOTAL"
# # # # # #     orig = df.loc[mask, sizes].fillna(-999)
# # # # # #     new  = edited.loc[mask, sizes].fillna(-999)

# # # # # #     if orig.equals(new):
# # # # # #         return False

# # # # # #     # rebuild the size→units map from the edited data rows
# # # # # #     new_units = {}
# # # # # #     for _, row in edited.loc[mask].iterrows():
# # # # # #         for s in sizes:
# # # # # #             v = row[s]
# # # # # #             if pd.notna(v):
# # # # # #                 new_units[s] = int(v)

# # # # # #     # one prepack per Multi group; grab its id from the first data row
# # # # # #     prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])

# # # # # #     st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
# # # # # #     return True


# # # # # # # ===========================================================================
# # # # # # # UI
# # # # # # # ===========================================================================
# # # # # # _init_state()

# # # # # # with st.sidebar:
# # # # # #     st.markdown("### ⚖️ Weight settings (kg)")
# # # # # #     st.caption("Edit any cell — values recalculate instantly.")

# # # # # #     edited_sidebar = st.data_editor(
# # # # # #         st.session_state.weights_df,
# # # # # #         use_container_width=True,
# # # # # #         num_rows="fixed",
# # # # # #         column_config={
# # # # # #             "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
# # # # # #             "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
# # # # # #             "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
# # # # # #         },
# # # # # #         key="weights_editor_sidebar",
# # # # # #     )
# # # # # #     if not edited_sidebar.equals(st.session_state.weights_df):
# # # # # #         st.session_state.weights_df = edited_sidebar
# # # # # #         st.rerun()

# # # # # #     if st.button("↺ Reset weights to defaults", use_container_width=True):
# # # # # #         st.session_state.weights_df = _default_weights_df()
# # # # # #         st.rerun()

# # # # # #     st.divider()

# # # # # #     st.markdown("### 📦 PER BLST")
# # # # # #     blst_c = st.number_input(
# # # # # #         "C  (multiplier)",
# # # # # #         min_value=1, max_value=8, value=1, step=1,
# # # # # #         help="PER BLST = \"Σ units_per_size X C\"",
# # # # # #     )
# # # # # #     st.caption(f"Formula: `PER BLST = \"A X {blst_c}\"`")

# # # # # #     st.divider()

# # # # # #     if st.button("↺ Reset size cells to PO defaults", use_container_width=True):
# # # # # #         st.session_state.size_edits = {}
# # # # # #         st.rerun()

# # # # # #     st.divider()
# # # # # #     json_path = st.text_input("JSON file path", DEFAULT_JSON)


# # # # # # if not Path(json_path).exists():
# # # # # #     st.error(f"File not found: `{json_path}`")
# # # # # #     st.stop()

# # # # # # weights = get_weights()
# # # # # # data = load_json(json_path)
# # # # # # groups = build_grouped(data, weights["NW"], weights["EMPTY"], blst_c)

# # # # # # if not groups:
# # # # # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # # # # #     st.stop()


# # # # # # # ===========================================================================
# # # # # # # Render one table per color
# # # # # # # ===========================================================================
# # # # # # all_frames: list = []

# # # # # # for color, rows in groups.items():
# # # # # #     sizes = present_sizes(rows)
# # # # # #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# # # # # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # # # # #     st.subheader(f"🎨 {color}")
# # # # # #     st.caption(
# # # # # #         f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s) · "
# # # # # #         "edit a size cell → QTY PER CTN, PER BLST, NET, GROSS refresh automatically"
# # # # # #     )

# # # # # #     # editable weight header (per color)
# # # # # #     render_size_weight_header(sizes, key_suffix=color)

# # # # # #     col_cfg = {
# # # # # #         "CTN NO":          st.column_config.TextColumn("CTN NO", width="small"),
# # # # # #         "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small"),
# # # # # #         "CTN QTY":         st.column_config.TextColumn("CTN QTY", width="small"),
# # # # # #         "COLOR":           st.column_config.TextColumn("COLOR", width="medium"),
# # # # # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium"),
# # # # # #         "PER BLST":        st.column_config.TextColumn("PER BLST", width="small"),
# # # # # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small"),
# # # # # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY", width="small"),
# # # # # #         "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f"),
# # # # # #         "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT", width="small", format="%.2f"),
# # # # # #     }
# # # # # #     for s in sizes:
# # # # # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small")

# # # # # #     try:
# # # # # #         edited = st.data_editor(
# # # # # #             data=df,
# # # # # #             use_container_width=True,
# # # # # #             hide_index=True,
# # # # # #             num_rows="fixed",
# # # # # #             column_config=col_cfg,
# # # # # #             key=f"multi_editor_{color}",
# # # # # #         )
# # # # # #     except TypeError:
# # # # # #         st.warning(
# # # # # #             "Your Streamlit version doesn't support data_editor with these options. "
# # # # # #             "Upgrade with: pip install -U streamlit"
# # # # # #         )
# # # # # #         st.dataframe(df, use_container_width=True, hide_index=True)
# # # # # #         edited = df

# # # # # #     # if the user touched a size cell → persist + rerun
# # # # # #     if _persist_size_edits(color, df, edited, sizes):
# # # # # #         st.rerun()

# # # # # #     all_frames.append((color, edited))
# # # # # #     st.divider()


# # # # # # # ===========================================================================
# # # # # # # Downloads
# # # # # # # ===========================================================================
# # # # # # st.markdown("### Download")

# # # # # # export_rows: list = []
# # # # # # for i, (_, frame) in enumerate(all_frames):
# # # # # #     if i > 0:
# # # # # #         export_rows.append({})
# # # # # #     export_rows.extend(frame.to_dict(orient="records"))

# # # # # # combined = pd.DataFrame(export_rows)

# # # # # # col1, col2 = st.columns(2)

# # # # # # with col1:
# # # # # #     st.download_button(
# # # # # #         "⬇ Download CSV (all colors)",
# # # # # #         data=combined.to_csv(index=False).encode("utf-8"),
# # # # # #         file_name="packing_list_multi.csv",
# # # # # #         mime="text/csv",
# # # # # #         use_container_width=True,
# # # # # #     )

# # # # # # with col2:
# # # # # #     try:
# # # # # #         buf = io.BytesIO()
# # # # # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # # # # #             st.session_state.weights_df.to_excel(writer, sheet_name="Weights")
# # # # # #             for color, frame in all_frames:
# # # # # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # # # # #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# # # # # #         st.download_button(
# # # # # #             "⬇ Download Excel (one sheet per color)",
# # # # # #             data=buf.getvalue(),
# # # # # #             file_name="packing_list_multi.xlsx",
# # # # # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # # # # #             use_container_width=True,
# # # # # #         )
# # # # # #     except ImportError:
# # # # # #         st.info("Install `openpyxl` to enable Excel export:  pip install openpyxl")


# # # # # # # ===========================================================================
# # # # # # # Sidebar info
# # # # # # # ===========================================================================
# # # # # # with st.sidebar:
# # # # # #     st.markdown("### Colors detected")
# # # # # #     for color, rows in groups.items():
# # # # # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # # # # #         st.write(f"- **{color}** — {n} group(s)")



# # # # # """
# # # # # multi_pack.py
# # # # # -------------
# # # # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.

# # # # # - Reference header (editable): N.W. / N.N.W. / EMPTY CTN WT.
# # # # # - Size cells are editable. Editing them recalculates:
# # # # #       A              = Σ units_per_size
# # # # #       QTY PER CTN    = A
# # # # #       PER BLST       = f"{A} X {C}"   (C default 1, adjust in sidebar)
# # # # #       NET WEIGHT     = Σ(units × N.W.)
# # # # #       GROSS WEIGHT   = NET + EMPTY_CTN_WEIGHT
# # # # #       TOTAL row      = recalculated

# # # # # Run:
# # # # #     streamlit run multi_pack.py
# # # # # """

# # # # # import io
# # # # # import json
# # # # # from pathlib import Path

# # # # # import pandas as pd
# # # # # import streamlit as st


# # # # # # ===========================================================================
# # # # # # Config
# # # # # # ===========================================================================
# # # # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # # # st.title("📦 Packing List — Multi Pack (Y)")

# # # # # DEFAULT_JSON = "61480360.json"

# # # # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # # # DEFAULT_NW    = {"XS": 0.510, "S": 0.520, "M": 0.550, "L": 0.560, "XL": 0.610, "XXL": 0.650, "XXL+": 0.690}
# # # # # DEFAULT_NNW   = {"XS": 0.49,  "S": 0.50,  "M": 0.53,  "L": 0.54,  "XL": 0.59,  "XXL": 0.63,  "XXL+": 0.67}
# # # # # DEFAULT_EMPTY = {"XS": 0.49,  "S": 1.00,  "M": 1.00,  "L": 1.00,  "XL": 1.00,  "XXL": 1.00,  "XXL+": 1.00}

# # # # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # # # ===========================================================================
# # # # # # Session state
# # # # # # ===========================================================================
# # # # # def _default_weights_df() -> pd.DataFrame:
# # # # #     return pd.DataFrame(
# # # # #         {
# # # # #             "SIZE":          SIZE_ORDER,
# # # # #             "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
# # # # #             "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
# # # # #             "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
# # # # #         }
# # # # #     ).set_index("SIZE")


# # # # # def _init_state():
# # # # #     if "weights_df" not in st.session_state:
# # # # #         st.session_state.weights_df = _default_weights_df()
# # # # #     if "size_edits" not in st.session_state:
# # # # #         # { color: { prepack: { size: units } } }
# # # # #         st.session_state.size_edits = {}


# # # # # def get_weights() -> dict:
# # # # #     df = st.session_state.weights_df
# # # # #     return {
# # # # #         "NW":    {s: float(df.loc[s, "N.W."])          for s in df.index},
# # # # #         "NNW":   {s: float(df.loc[s, "N.N.W."])        for s in df.index},
# # # # #         "EMPTY": {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index},
# # # # #     }


# # # # # # ===========================================================================
# # # # # # Helpers
# # # # # # ===========================================================================
# # # # # @st.cache_data(show_spinner=False)
# # # # # def load_json(path: str) -> dict:
# # # # #     with open(path, "r", encoding="utf-8") as f:
# # # # #         return json.load(f)


# # # # # def color_display(raw: str) -> str:
# # # # #     if not raw:
# # # # #         return ""
# # # # #     parts = raw.rsplit(" ", 1)
# # # # #     return parts[-1] if len(parts) > 1 else raw


# # # # # def present_sizes(rows: list) -> list:
# # # # #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # # # # def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
# # # # #     ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
# # # # #     return max(ws) if ws else 0.0


# # # # # def render_size_weight_header(sizes: list, key_suffix: str = "") -> None:
# # # # #     master = st.session_state.weights_df
# # # # #     view = master.loc[sizes].T.copy()
# # # # #     view.index.name = "SIZE"

# # # # #     edited = st.data_editor(
# # # # #         view,
# # # # #         use_container_width=False,
# # # # #         num_rows="fixed",
# # # # #         column_config={
# # # # #             s: st.column_config.NumberColumn(s, format="%.3f", step=0.001, width="small")
# # # # #             for s in view.columns
# # # # #         },
# # # # #         key=f"header_editor_{key_suffix}",
# # # # #     )
# # # # #     if not edited.equals(view):
# # # # #         for s in edited.columns:
# # # # #             st.session_state.weights_df.loc[s, "N.W."]          = float(edited.loc["N.W.", s])
# # # # #             st.session_state.weights_df.loc[s, "N.N.W."]        = float(edited.loc["N.N.W.", s])
# # # # #             st.session_state.weights_df.loc[s, "EMPTY CTN WT."] = float(edited.loc["EMPTY CTN WT.", s])
# # # # #         st.rerun()


# # # # # # ===========================================================================
# # # # # # Build packing list
# # # # # # ===========================================================================
# # # # # def build_grouped(data: dict, nw: dict, empty_weights: dict, blst_c: int) -> dict:
# # # # #     groups: dict = {}
# # # # #     ctn_counter: dict = {}

# # # # #     for _, table in data["tables"].items():
# # # # #         trows = table.get("rows") or []
# # # # #         total = table.get("total") or {}
# # # # #         if not trows:
# # # # #             continue

# # # # #         first = trows[0]
# # # # #         if first.get("PrePack Type") != "Multi" or first.get("Full Carton") != "Y":
# # # # #             continue

# # # # #         color   = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # # # #         prepack = str(first.get("PrePack"))
# # # # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # # # #         row_no = ctn_counter[color]

# # # # #         # current units per size (session overrides JSON)
# # # # #         edits = st.session_state.size_edits.get(color, {}).get(prepack, {})
# # # # #         row_sizes = []
# # # # #         for r in trows:
# # # # #             size  = r["Size Desc"]
# # # # #             units = int(edits.get(size, r.get("Units per PrePack") or 0))
# # # # #             row_sizes.append((size, units))

# # # # #         sizes_present = [s for s, _ in row_sizes]

# # # # #         # ---- A: Σ units_per_size -------------------------------------------
# # # # #         A = sum(u for _, u in row_sizes)

# # # # #         qty_per_ctn = A                          # QTY PER CTN = A
# # # # #         per_blst    = f"{A} X {blst_c}"          # PER BLST    = "A X C"

# # # # #         net_per_carton   = round(sum(u * nw.get(s, 0.0) for s, u in row_sizes), 2)
# # # # #         empty_ctn_weight = _empty_ctn_weight_for(sizes_present, empty_weights)
# # # # #         gross_per_carton = round(net_per_carton + empty_ctn_weight, 2)

# # # # #         ctn_mes   = total.get("#PrePackets Ordered")
# # # # #         total_qty = total.get("Qty Ordered (eaches)") or sum(
# # # # #             r.get("Qty Ordered (eaches)") or 0 for r in trows
# # # # #         )

# # # # #         total_net   = round(ctn_mes * net_per_carton,   2) if ctn_mes else None
# # # # #         total_gross = round(ctn_mes * gross_per_carton, 2) if ctn_mes else None

# # # # #         # ---- data row ----
# # # # #         data_row = {
# # # # #             "CTN NO":          row_no,
# # # # #             "CTN MES:":        ctn_mes,
# # # # #             "CTN QTY":         ctn_mes,
# # # # #             "COLOR":           color,
# # # # #             "PREPACK STECKER": prepack,
# # # # #         }
# # # # #         for s, u in row_sizes:
# # # # #             data_row[s] = u
# # # # #         data_row["PER BLST"]     = per_blst
# # # # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # # # #         data_row["TOTAL QTY"]    = total_qty
# # # # #         data_row["GROSS WEIGHT"] = gross_per_carton
# # # # #         data_row["NET WEIGHT"]   = net_per_carton

# # # # #         # ---- total row ----
# # # # #         tot = {
# # # # #             "CTN NO":          "TOTAL",
# # # # #             "CTN MES:":        None,
# # # # #             "CTN QTY":         f"{ctn_mes} CTNS" if ctn_mes else None,
# # # # #             "COLOR":           None,
# # # # #             "PREPACK STECKER": None,
# # # # #         }
# # # # #         for s, u in row_sizes:
# # # # #             tot[s] = (ctn_mes * u) if ctn_mes else None
# # # # #         tot["PER BLST"]     = None
# # # # #         tot["QTY PER CTN"]  = None
# # # # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # # # #         tot["GROSS WEIGHT"] = total_gross
# # # # #         tot["NET WEIGHT"]   = total_net

# # # # #         groups.setdefault(color, []).append(data_row)
# # # # #         groups[color].append(tot)

# # # # #     return groups


# # # # # # ===========================================================================
# # # # # # Detect size-cell edits
# # # # # # ===========================================================================
# # # # # def _persist_size_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
# # # # #     if not sizes:
# # # # #         return False
# # # # #     mask = df["CTN NO"].astype(str) != "TOTAL"
# # # # #     orig = df.loc[mask, sizes].fillna(-999)
# # # # #     new  = edited.loc[mask, sizes].fillna(-999)
# # # # #     if orig.equals(new):
# # # # #         return False

# # # # #     new_units = {}
# # # # #     for _, row in edited.loc[mask].iterrows():
# # # # #         for s in sizes:
# # # # #             v = row[s]
# # # # #             if pd.notna(v):
# # # # #                 new_units[s] = int(v)

# # # # #     prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])
# # # # #     st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
# # # # #     return True


# # # # # # ===========================================================================
# # # # # # UI
# # # # # # ===========================================================================
# # # # # _init_state()

# # # # # with st.sidebar:
# # # # #     st.markdown("### ⚖️ Weight settings (kg)")
# # # # #     st.caption("Edit any cell — values recalculate instantly.")

# # # # #     edited_sidebar = st.data_editor(
# # # # #         st.session_state.weights_df,
# # # # #         use_container_width=True,
# # # # #         num_rows="fixed",
# # # # #         column_config={
# # # # #             "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
# # # # #             "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
# # # # #             "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
# # # # #         },
# # # # #         key="weights_editor_sidebar",
# # # # #     )
# # # # #     if not edited_sidebar.equals(st.session_state.weights_df):
# # # # #         st.session_state.weights_df = edited_sidebar
# # # # #         st.rerun()

# # # # #     if st.button("↺ Reset weights", use_container_width=True):
# # # # #         st.session_state.weights_df = _default_weights_df()
# # # # #         st.rerun()

# # # # #     st.divider()
# # # # #     st.markdown("### 📦 PER BLST")
# # # # #     blst_c = st.number_input(
# # # # #         "C  (multiplier, default 1)",
# # # # #         min_value=1, max_value=8, value=1, step=1,
# # # # #         help="PER BLST = \"Σ units_per_size X C\"",
# # # # #     )
# # # # #     st.caption(f"Formula: `PER BLST = \"A X {blst_c}\"`  where A = QTY PER CTN")

# # # # #     st.divider()
# # # # #     if st.button("↺ Reset size cells to PO defaults", use_container_width=True):
# # # # #         st.session_state.size_edits = {}
# # # # #         st.rerun()

# # # # #     st.divider()
# # # # #     json_path = st.text_input("JSON file path", DEFAULT_JSON)


# # # # # if not Path(json_path).exists():
# # # # #     st.error(f"File not found: `{json_path}`")
# # # # #     st.stop()

# # # # # weights = get_weights()
# # # # # data = load_json(json_path)
# # # # # groups = build_grouped(data, weights["NW"], weights["EMPTY"], blst_c)

# # # # # if not groups:
# # # # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # # # #     st.stop()


# # # # # # ===========================================================================
# # # # # # Render
# # # # # # ===========================================================================
# # # # # all_frames: list = []

# # # # # for color, rows in groups.items():
# # # # #     sizes = present_sizes(rows)
# # # # #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# # # # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # # # #     st.subheader(f"🎨 {color}")
# # # # #     st.caption(
# # # # #         f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s) · "
# # # # #         "edit a size cell → QTY PER CTN and PER BLST update automatically"
# # # # #     )

# # # # #     render_size_weight_header(sizes, key_suffix=color)

# # # # #     col_cfg = {
# # # # #         "CTN NO":          st.column_config.TextColumn("CTN NO", width="small"),
# # # # #         "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small"),
# # # # #         "CTN QTY":         st.column_config.TextColumn("CTN QTY", width="small"),
# # # # #         "COLOR":           st.column_config.TextColumn("COLOR", width="medium"),
# # # # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium"),
# # # # #         # derived columns → read-only
# # # # #         "PER BLST":        st.column_config.TextColumn("PER BLST", width="small",   disabled=True),
# # # # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small", disabled=True),
# # # # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY", width="small",  disabled=True),
# # # # #         "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f", disabled=True),
# # # # #         "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT",   width="small", format="%.2f", disabled=True),
# # # # #     }
# # # # #     for s in sizes:
# # # # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small", min_value=0, step=1)

# # # # #     try:
# # # # #         edited = st.data_editor(
# # # # #             data=df,
# # # # #             use_container_width=True,
# # # # #             hide_index=True,
# # # # #             num_rows="fixed",
# # # # #             column_config=col_cfg,
# # # # #             key=f"multi_editor_{color}",
# # # # #         )
# # # # #     except TypeError:
# # # # #         st.warning("Upgrade Streamlit for data_editor: pip install -U streamlit")
# # # # #         st.dataframe(df, use_container_width=True, hide_index=True)
# # # # #         edited = df

# # # # #     if _persist_size_edits(color, df, edited, sizes):
# # # # #         st.rerun()

# # # # #     all_frames.append((color, edited))
# # # # #     st.divider()


# # # # # # ===========================================================================
# # # # # # Downloads
# # # # # # ===========================================================================
# # # # # st.markdown("### Download")

# # # # # export_rows: list = []
# # # # # for i, (_, frame) in enumerate(all_frames):
# # # # #     if i > 0:
# # # # #         export_rows.append({})
# # # # #     export_rows.extend(frame.to_dict(orient="records"))
# # # # # combined = pd.DataFrame(export_rows)

# # # # # col1, col2 = st.columns(2)
# # # # # with col1:
# # # # #     st.download_button(
# # # # #         "⬇ Download CSV (all colors)",
# # # # #         data=combined.to_csv(index=False).encode("utf-8"),
# # # # #         file_name="packing_list_multi.csv", mime="text/csv",
# # # # #         use_container_width=True,
# # # # #     )
# # # # # with col2:
# # # # #     try:
# # # # #         buf = io.BytesIO()
# # # # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # # # #             st.session_state.weights_df.to_excel(writer, sheet_name="Weights")
# # # # #             for color, frame in all_frames:
# # # # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # # # #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# # # # #         st.download_button(
# # # # #             "⬇ Download Excel (one sheet per color)",
# # # # #             data=buf.getvalue(), file_name="packing_list_multi.xlsx",
# # # # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # # # #             use_container_width=True,
# # # # #         )
# # # # #     except ImportError:
# # # # #         st.info("Install openpyxl for Excel export")


# # # # # # ===========================================================================
# # # # # # Sidebar info
# # # # # # ===========================================================================
# # # # # with st.sidebar:
# # # # #     st.markdown("### Colors detected")
# # # # #     for color, rows in groups.items():
# # # # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # # # #         st.write(f"- **{color}** — {n} group(s)")



# # # # """
# # # # multi_pack.py
# # # # -------------
# # # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.

# # # # Editable:
# # # #     - size cells (units per size)
# # # #     - CTN QTY (number of cartons)   ← this file
# # # #     - weight tables (sidebar + per-color header)

# # # # Derived:
# # # #     QTY PER CTN   = Σ units_per_size
# # # #     PER BLST      = f"{QTY PER CTN} X C"  (C default 1, sidebar)
# # # #     NET (per ctn) = Σ(units × N.W.)
# # # #     GROSS (per ctn) = NET + EMPTY_CTN_WEIGHT
# # # #     TOTAL QTY     = CTN QTY × QTY PER CTN
# # # #     Total row [s] = CTN QTY × units_per_size
# # # #     Total NET     = CTN QTY × NET (per ctn)
# # # #     Total GROSS   = CTN QTY × GROSS (per ctn)

# # # # Run:
# # # #     streamlit run multi_pack.py
# # # # """

# # # # import io
# # # # import json
# # # # from pathlib import Path

# # # # import pandas as pd
# # # # import streamlit as st


# # # # # ===========================================================================
# # # # # Config
# # # # # ===========================================================================
# # # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # # st.title("📦 Packing List — Multi Pack (Y)")

# # # # DEFAULT_JSON = "61480360.json"

# # # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # # DEFAULT_NW    = {"XS": 0.510, "S": 0.520, "M": 0.550, "L": 0.560, "XL": 0.610, "XXL": 0.650, "XXL+": 0.690}
# # # # DEFAULT_NNW   = {"XS": 0.49,  "S": 0.50,  "M": 0.53,  "L": 0.54,  "XL": 0.59,  "XXL": 0.63,  "XXL+": 0.67}
# # # # DEFAULT_EMPTY = {"XS": 0.49,  "S": 1.00,  "M": 1.00,  "L": 1.00,  "XL": 1.00,  "XXL": 1.00,  "XXL+": 1.00}

# # # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # # ===========================================================================
# # # # # Session state
# # # # # ===========================================================================
# # # # def _default_weights_df() -> pd.DataFrame:
# # # #     return pd.DataFrame(
# # # #         {
# # # #             "SIZE":          SIZE_ORDER,
# # # #             "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
# # # #             "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
# # # #             "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
# # # #         }
# # # #     ).set_index("SIZE")


# # # # def _init_state():
# # # #     if "weights_df" not in st.session_state:
# # # #         st.session_state.weights_df = _default_weights_df()
# # # #     if "size_edits" not in st.session_state:
# # # #         st.session_state.size_edits = {}   # { color: { prepack: { size: units } } }
# # # #     if "ctn_edits" not in st.session_state:
# # # #         st.session_state.ctn_edits = {}    # { color: { prepack: ctn_qty } }


# # # # def get_weights() -> dict:
# # # #     df = st.session_state.weights_df
# # # #     return {
# # # #         "NW":    {s: float(df.loc[s, "N.W."])          for s in df.index},
# # # #         "NNW":   {s: float(df.loc[s, "N.N.W."])        for s in df.index},
# # # #         "EMPTY": {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index},
# # # #     }


# # # # # ===========================================================================
# # # # # Helpers
# # # # # ===========================================================================
# # # # @st.cache_data(show_spinner=False)
# # # # def load_json(path: str) -> dict:
# # # #     with open(path, "r", encoding="utf-8") as f:
# # # #         return json.load(f)


# # # # def color_display(raw: str) -> str:
# # # #     if not raw:
# # # #         return ""
# # # #     parts = raw.rsplit(" ", 1)
# # # #     return parts[-1] if len(parts) > 1 else raw


# # # # def present_sizes(rows: list) -> list:
# # # #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # # # def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
# # # #     ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
# # # #     return max(ws) if ws else 0.0


# # # # def render_size_weight_header(sizes: list, key_suffix: str = "") -> None:
# # # #     master = st.session_state.weights_df
# # # #     view = master.loc[sizes].T.copy()
# # # #     view.index.name = "SIZE"

# # # #     edited = st.data_editor(
# # # #         view,
# # # #         use_container_width=False,
# # # #         num_rows="fixed",
# # # #         column_config={
# # # #             s: st.column_config.NumberColumn(s, format="%.3f", step=0.001, width="small")
# # # #             for s in view.columns
# # # #         },
# # # #         key=f"header_editor_{key_suffix}",
# # # #     )
# # # #     if not edited.equals(view):
# # # #         for s in edited.columns:
# # # #             st.session_state.weights_df.loc[s, "N.W."]          = float(edited.loc["N.W.", s])
# # # #             st.session_state.weights_df.loc[s, "N.N.W."]        = float(edited.loc["N.N.W.", s])
# # # #             st.session_state.weights_df.loc[s, "EMPTY CTN WT."] = float(edited.loc["EMPTY CTN WT.", s])
# # # #         st.rerun()


# # # # # ===========================================================================
# # # # # Build packing list
# # # # # ===========================================================================
# # # # def build_grouped(data: dict, nw: dict, empty_weights: dict, blst_c: int) -> dict:
# # # #     groups: dict = {}
# # # #     ctn_counter: dict = {}

# # # #     for _, table in data["tables"].items():
# # # #         trows = table.get("rows") or []
# # # #         total = table.get("total") or {}
# # # #         if not trows:
# # # #             continue

# # # #         first = trows[0]
# # # #         if first.get("PrePack Type") != "Multi" or first.get("Full Carton") != "Y":
# # # #             continue

# # # #         color   = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # # #         prepack = str(first.get("PrePack"))
# # # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # # #         row_no = ctn_counter[color]

# # # #         # --- session overrides -------------------------------------------------
# # # #         size_edits = st.session_state.size_edits.get(color, {}).get(prepack, {})
# # # #         ctn_edit   = st.session_state.ctn_edits.get(color, {}).get(prepack)

# # # #         row_sizes = []
# # # #         for r in trows:
# # # #             size  = r["Size Desc"]
# # # #             units = int(size_edits.get(size, r.get("Units per PrePack") or 0))
# # # #             row_sizes.append((size, units))

# # # #         sizes_present = [s for s, _ in row_sizes]

# # # #         # --- CTN QTY ----------------------------------------------------------
# # # #         json_ctn_mes = total.get("#PrePackets Ordered") or 0
# # # #         ctn_qty = int(ctn_edit) if ctn_edit is not None else json_ctn_mes

# # # #         # --- derived per-carton values ---------------------------------------
# # # #         A           = sum(u for _, u in row_sizes)
# # # #         qty_per_ctn = A
# # # #         per_blst    = f"{A} X {blst_c}"

# # # #         net_per_carton   = round(sum(u * nw.get(s, 0.0) for s, u in row_sizes), 2)
# # # #         empty_ctn_weight = _empty_ctn_weight_for(sizes_present, empty_weights)
# # # #         gross_per_carton = round(net_per_carton + empty_ctn_weight, 2)

# # # #         # --- totals depend on ctn_qty ----------------------------------------
# # # #         total_qty   = ctn_qty * qty_per_ctn
# # # #         total_net   = round(ctn_qty * net_per_carton,   2) if ctn_qty else None
# # # #         total_gross = round(ctn_qty * gross_per_carton, 2) if ctn_qty else None

# # # #         # ---- data row ----
# # # #         data_row = {
# # # #             "CTN NO":          row_no,
# # # #             "CTN MES:":        ctn_qty,
# # # #             "CTN QTY":         ctn_qty,     # editable
# # # #             "COLOR":           color,
# # # #             "PREPACK STECKER": prepack,
# # # #         }
# # # #         for s, u in row_sizes:
# # # #             data_row[s] = u
# # # #         data_row["PER BLST"]     = per_blst
# # # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # # #         data_row["TOTAL QTY"]    = total_qty
# # # #         data_row["GROSS WEIGHT"] = gross_per_carton
# # # #         data_row["NET WEIGHT"]   = net_per_carton

# # # #         # ---- total row ----
# # # #         tot = {
# # # #             "CTN NO":          "TOTAL",
# # # #             "CTN MES:":        None,
# # # #             "CTN QTY":         f"{ctn_qty} CTNS" if ctn_qty else None,
# # # #             "COLOR":           None,
# # # #             "PREPACK STECKER": None,
# # # #         }
# # # #         for s, u in row_sizes:
# # # #             tot[s] = (ctn_qty * u) if ctn_qty else None
# # # #         tot["PER BLST"]     = None
# # # #         tot["QTY PER CTN"]  = None
# # # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # # #         tot["GROSS WEIGHT"] = total_gross
# # # #         tot["NET WEIGHT"]   = total_net

# # # #         groups.setdefault(color, []).append(data_row)
# # # #         groups[color].append(tot)

# # # #     return groups


# # # # # ===========================================================================
# # # # # Detect edits (size cells + CTN QTY)
# # # # # ===========================================================================
# # # # def _to_int(v):
# # # #     """Parse int from anything: 89, '89', '89 CTNS', 89.0, None..."""
# # # #     if v is None:
# # # #         return None
# # # #     try:
# # # #         return int(float(str(v).strip().split()[0]))
# # # #     except (ValueError, TypeError, IndexError):
# # # #         return None


# # # # def _persist_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
# # # #     """Return True if any edit was saved (needs rerun)."""
# # # #     mask = df["CTN NO"].astype(str) != "TOTAL"
# # # #     if not mask.any():
# # # #         return False

# # # #     changed = False
# # # #     prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])

# # # #     # ---- size cell edits ----
# # # #     if sizes:
# # # #         orig_sizes = df.loc[mask, sizes].fillna(-999)
# # # #         new_sizes  = edited.loc[mask, sizes].fillna(-999)
# # # #         if not orig_sizes.equals(new_sizes):
# # # #             new_units = {}
# # # #             for _, row in edited.loc[mask].iterrows():
# # # #                 for s in sizes:
# # # #                     v = row[s]
# # # #                     if pd.notna(v):
# # # #                         new_units[s] = int(v)
# # # #             st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
# # # #             changed = True

# # # #     # ---- CTN QTY edits ----
# # # #     orig_ctn = _to_int(df.loc[mask, "CTN QTY"].iloc[0])
# # # #     new_ctn  = _to_int(edited.loc[mask, "CTN QTY"].iloc[0])

# # # #     if new_ctn is not None and new_ctn != orig_ctn:
# # # #         st.session_state.ctn_edits.setdefault(color, {})[prepack] = new_ctn
# # # #         changed = True

# # # #     return changed


# # # # # ===========================================================================
# # # # # UI
# # # # # ===========================================================================
# # # # _init_state()

# # # # with st.sidebar:
# # # #     st.markdown("### ⚖️ Weight settings (kg)")
# # # #     st.caption("Edit any cell — values recalculate instantly.")

# # # #     edited_sidebar = st.data_editor(
# # # #         st.session_state.weights_df,
# # # #         use_container_width=True,
# # # #         num_rows="fixed",
# # # #         column_config={
# # # #             "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
# # # #             "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
# # # #             "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
# # # #         },
# # # #         key="weights_editor_sidebar",
# # # #     )
# # # #     if not edited_sidebar.equals(st.session_state.weights_df):
# # # #         st.session_state.weights_df = edited_sidebar
# # # #         st.rerun()

# # # #     if st.button("↺ Reset weights", use_container_width=True):
# # # #         st.session_state.weights_df = _default_weights_df()
# # # #         st.rerun()

# # # #     st.divider()
# # # #     st.markdown("### 📦 PER BLST")
# # # #     blst_c = st.number_input(
# # # #         "C  (multiplier, default 1)",
# # # #         min_value=1, max_value=8, value=1, step=1,
# # # #         help="PER BLST = \"Σ units_per_size X C\"",
# # # #     )
# # # #     st.caption(f"Formula: `PER BLST = \"A X {blst_c}\"`")

# # # #     st.divider()
# # # #     if st.button("↺ Reset all cell edits", use_container_width=True):
# # # #         st.session_state.size_edits = {}
# # # #         st.session_state.ctn_edits  = {}
# # # #         st.rerun()

# # # #     st.divider()
# # # #     json_path = st.text_input("JSON file path", DEFAULT_JSON)


# # # # if not Path(json_path).exists():
# # # #     st.error(f"File not found: `{json_path}`")
# # # #     st.stop()

# # # # weights = get_weights()
# # # # data = load_json(json_path)
# # # # groups = build_grouped(data, weights["NW"], weights["EMPTY"], blst_c)

# # # # if not groups:
# # # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # # #     st.stop()


# # # # # ===========================================================================
# # # # # Render
# # # # # ===========================================================================
# # # # all_frames: list = []

# # # # for color, rows in groups.items():
# # # #     sizes = present_sizes(rows)
# # # #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# # # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # # #     st.subheader(f"🎨 {color}")
# # # #     st.caption(
# # # #         f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s) · "
# # # #         "edit size cells or CTN QTY → TOTAL row & TOTAL QTY update automatically"
# # # #     )

# # # #     render_size_weight_header(sizes, key_suffix=color)

# # # #     col_cfg = {
# # # #         "CTN NO":          st.column_config.TextColumn("CTN NO",  width="small", disabled=True),
# # # #         "CTN MES:":        st.column_config.NumberColumn("CTN MES:", width="small", disabled=True),
# # # #         # ---- editable carton count ----
# # # #         "CTN QTY":         st.column_config.NumberColumn(
# # # #             "CTN QTY", width="small",
# # # #             min_value=1, step=1, format="%d",
# # # #             help="Editable. Number of cartons. Drives TOTAL row, TOTAL QTY, NET, GROSS.",
# # # #         ),
# # # #         "COLOR":           st.column_config.TextColumn("COLOR",           width="medium", disabled=True),
# # # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium", disabled=True),
# # # #         # derived → read-only
# # # #         "PER BLST":        st.column_config.TextColumn("PER BLST",   width="small", disabled=True),
# # # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small", disabled=True),
# # # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY",  width="small", disabled=True),
# # # #         "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f", disabled=True),
# # # #         "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT",   width="small", format="%.2f", disabled=True),
# # # #     }
# # # #     for s in sizes:
# # # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small", min_value=0, step=1)

# # # #     try:
# # # #         edited = st.data_editor(
# # # #             data=df,
# # # #             use_container_width=True,
# # # #             hide_index=True,
# # # #             num_rows="fixed",
# # # #             column_config=col_cfg,
# # # #             key=f"multi_editor_{color}",
# # # #         )
# # # #     except TypeError:
# # # #         st.warning("Upgrade Streamlit: pip install -U streamlit")
# # # #         st.dataframe(df, use_container_width=True, hide_index=True)
# # # #         edited = df

# # # #     if _persist_edits(color, df, edited, sizes):
# # # #         st.rerun()

# # # #     all_frames.append((color, edited))
# # # #     st.divider()


# # # # # ===========================================================================
# # # # # Downloads
# # # # # ===========================================================================
# # # # st.markdown("### Download")

# # # # export_rows: list = []
# # # # for i, (_, frame) in enumerate(all_frames):
# # # #     if i > 0:
# # # #         export_rows.append({})
# # # #     export_rows.extend(frame.to_dict(orient="records"))
# # # # combined = pd.DataFrame(export_rows)

# # # # col1, col2 = st.columns(2)
# # # # with col1:
# # # #     st.download_button(
# # # #         "⬇ Download CSV (all colors)",
# # # #         data=combined.to_csv(index=False).encode("utf-8"),
# # # #         file_name="packing_list_multi.csv", mime="text/csv",
# # # #         use_container_width=True,
# # # #     )
# # # # with col2:
# # # #     try:
# # # #         buf = io.BytesIO()
# # # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # # #             st.session_state.weights_df.to_excel(writer, sheet_name="Weights")
# # # #             for color, frame in all_frames:
# # # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # # #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# # # #         st.download_button(
# # # #             "⬇ Download Excel (one sheet per color)",
# # # #             data=buf.getvalue(), file_name="packing_list_multi.xlsx",
# # # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # # #             use_container_width=True,
# # # #         )
# # # #     except ImportError:
# # # #         st.info("Install openpyxl for Excel export")


# # # # # ===========================================================================
# # # # # Sidebar info
# # # # # ===========================================================================
# # # # with st.sidebar:
# # # #     st.markdown("### Colors detected")
# # # #     for color, rows in groups.items():
# # # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # # #         st.write(f"- **{color}** — {n} group(s)")



# # # # """
# # # # multi_pack.py
# # # # -------------
# # # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.

# # # # Editable:
# # # #     - size cells (units per size)
# # # #     - CTN QTY (number of cartons)
# # # #     - weight tables (sidebar + per-color header)

# # # # Fixed:
# # # #     CTN MES: = "G81"

# # # # Derived:
# # # #     QTY PER CTN   = Σ units_per_size
# # # #     PER BLST      = f"{QTY PER CTN} X C"  (C default 1)
# # # #     NET (per ctn) = Σ(units × N.W.)
# # # #     GROSS (per ctn) = NET + EMPTY_CTN_WEIGHT
# # # #     TOTAL QTY     = CTN QTY × QTY PER CTN
# # # #     Total row [s] = CTN QTY × units_per_size

# # # # Run:
# # # #     streamlit run multi_pack.py
# # # # """

# # # # import io
# # # # import json
# # # # from pathlib import Path

# # # # import pandas as pd
# # # # import streamlit as st


# # # # # ===========================================================================
# # # # # Config
# # # # # ===========================================================================
# # # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # # st.title("📦 Packing List — Multi Pack (Y)")

# # # # DEFAULT_JSON = "61480360.json"

# # # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # # FIXED_CTN_MES = "G81"    # ← fixed carton name

# # # # DEFAULT_NW    = {"XS": 0.510, "S": 0.520, "M": 0.550, "L": 0.560, "XL": 0.610, "XXL": 0.650, "XXL+": 0.690}
# # # # DEFAULT_NNW   = {"XS": 0.49,  "S": 0.50,  "M": 0.53,  "L": 0.54,  "XL": 0.59,  "XXL": 0.63,  "XXL+": 0.67}
# # # # DEFAULT_EMPTY = {"XS": 0.49,  "S": 1.00,  "M": 1.00,  "L": 1.00,  "XL": 1.00,  "XXL": 1.00,  "XXL+": 1.00}

# # # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # # ===========================================================================
# # # # # Session state
# # # # # ===========================================================================
# # # # def _default_weights_df() -> pd.DataFrame:
# # # #     return pd.DataFrame(
# # # #         {
# # # #             "SIZE":          SIZE_ORDER,
# # # #             "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
# # # #             "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
# # # #             "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
# # # #         }
# # # #     ).set_index("SIZE")


# # # # def _init_state():
# # # #     if "weights_df" not in st.session_state:
# # # #         st.session_state.weights_df = _default_weights_df()
# # # #     if "size_edits" not in st.session_state:
# # # #         st.session_state.size_edits = {}   # { color: { prepack: { size: units } } }
# # # #     if "ctn_edits" not in st.session_state:
# # # #         st.session_state.ctn_edits = {}    # { color: { prepack: ctn_qty } }


# # # # def get_weights() -> dict:
# # # #     df = st.session_state.weights_df
# # # #     return {
# # # #         "NW":    {s: float(df.loc[s, "N.W."])          for s in df.index},
# # # #         "NNW":   {s: float(df.loc[s, "N.N.W."])        for s in df.index},
# # # #         "EMPTY": {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index},
# # # #     }


# # # # # ===========================================================================
# # # # # Helpers
# # # # # ===========================================================================
# # # # @st.cache_data(show_spinner=False)
# # # # def load_json(path: str) -> dict:
# # # #     with open(path, "r", encoding="utf-8") as f:
# # # #         return json.load(f)


# # # # def color_display(raw: str) -> str:
# # # #     if not raw:
# # # #         return ""
# # # #     parts = raw.rsplit(" ", 1)
# # # #     return parts[-1] if len(parts) > 1 else raw


# # # # def present_sizes(rows: list) -> list:
# # # #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # # # def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
# # # #     ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
# # # #     return max(ws) if ws else 0.0


# # # # def render_size_weight_header(sizes: list, key_suffix: str = "") -> None:
# # # #     master = st.session_state.weights_df
# # # #     view = master.loc[sizes].T.copy()
# # # #     view.index.name = "SIZE"

# # # #     edited = st.data_editor(
# # # #         view,
# # # #         use_container_width=False,
# # # #         num_rows="fixed",
# # # #         column_config={
# # # #             s: st.column_config.NumberColumn(s, format="%.3f", step=0.001, width="small")
# # # #             for s in view.columns
# # # #         },
# # # #         key=f"header_editor_{key_suffix}",
# # # #     )
# # # #     if not edited.equals(view):
# # # #         for s in edited.columns:
# # # #             st.session_state.weights_df.loc[s, "N.W."]          = float(edited.loc["N.W.", s])
# # # #             st.session_state.weights_df.loc[s, "N.N.W."]        = float(edited.loc["N.N.W.", s])
# # # #             st.session_state.weights_df.loc[s, "EMPTY CTN WT."] = float(edited.loc["EMPTY CTN WT.", s])
# # # #         st.rerun()


# # # # # ===========================================================================
# # # # # Build packing list
# # # # # ===========================================================================
# # # # def build_grouped(data: dict, nw: dict, empty_weights: dict, blst_c: int) -> dict:
# # # #     groups: dict = {}
# # # #     ctn_counter: dict = {}

# # # #     for _, table in data["tables"].items():
# # # #         trows = table.get("rows") or []
# # # #         total = table.get("total") or {}
# # # #         if not trows:
# # # #             continue

# # # #         first = trows[0]
# # # #         if first.get("PrePack Type") != "Multi" or first.get("Full Carton") != "Y":
# # # #             continue

# # # #         color   = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # # #         prepack = str(first.get("PrePack"))
# # # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # # #         row_no = ctn_counter[color]

# # # #         # --- session overrides -------------------------------------------------
# # # #         size_edits = st.session_state.size_edits.get(color, {}).get(prepack, {})
# # # #         ctn_edit   = st.session_state.ctn_edits.get(color, {}).get(prepack)

# # # #         row_sizes = []
# # # #         for r in trows:
# # # #             size  = r["Size Desc"]
# # # #             units = int(size_edits.get(size, r.get("Units per PrePack") or 0))
# # # #             row_sizes.append((size, units))

# # # #         sizes_present = [s for s, _ in row_sizes]

# # # #         # --- CTN QTY (cartons) -------------------------------------------------
# # # #         json_ctn_mes = total.get("#PrePackets Ordered") or 0
# # # #         ctn_qty = int(ctn_edit) if ctn_edit is not None else json_ctn_mes

# # # #         # --- derived per-carton values ---------------------------------------
# # # #         A           = sum(u for _, u in row_sizes)
# # # #         qty_per_ctn = A
# # # #         per_blst    = f"{A} X {blst_c}"

# # # #         net_per_carton   = round(sum(u * nw.get(s, 0.0) for s, u in row_sizes), 2)
# # # #         empty_ctn_weight = _empty_ctn_weight_for(sizes_present, empty_weights)
# # # #         gross_per_carton = round(net_per_carton + empty_ctn_weight, 2)

# # # #         # --- totals depend on ctn_qty ----------------------------------------
# # # #         total_qty   = ctn_qty * qty_per_ctn
# # # #         total_net   = round(ctn_qty * net_per_carton,   2) if ctn_qty else None
# # # #         total_gross = round(ctn_qty * gross_per_carton, 2) if ctn_qty else None

# # # #         # ---- data row ----
# # # #         data_row = {
# # # #             "CTN NO":          row_no,
# # # #             "CTN MES:":        FIXED_CTN_MES,   # ← fixed "G81"
# # # #             "CTN QTY":         ctn_qty,          # editable
# # # #             "COLOR":           color,
# # # #             "PREPACK STECKER": prepack,
# # # #         }
# # # #         for s, u in row_sizes:
# # # #             data_row[s] = u
# # # #         data_row["PER BLST"]     = per_blst
# # # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # # #         data_row["TOTAL QTY"]    = total_qty
# # # #         data_row["GROSS WEIGHT"] = gross_per_carton
# # # #         data_row["NET WEIGHT"]   = net_per_carton

# # # #         # ---- total row ----
# # # #         tot = {
# # # #             "CTN NO":          "TOTAL",
# # # #             "CTN MES:":        None,
# # # #             "CTN QTY":         f"{ctn_qty} CTNS" if ctn_qty else None,
# # # #             "COLOR":           None,
# # # #             "PREPACK STECKER": None,
# # # #         }
# # # #         for s, u in row_sizes:
# # # #             tot[s] = (ctn_qty * u) if ctn_qty else None
# # # #         tot["PER BLST"]     = None
# # # #         tot["QTY PER CTN"]  = None
# # # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # # #         tot["GROSS WEIGHT"] = total_gross
# # # #         tot["NET WEIGHT"]   = total_net

# # # #         groups.setdefault(color, []).append(data_row)
# # # #         groups[color].append(tot)

# # # #     return groups


# # # # # ===========================================================================
# # # # # Detect edits (size cells + CTN QTY)
# # # # # ===========================================================================
# # # # def _to_int(v):
# # # #     if v is None:
# # # #         return None
# # # #     try:
# # # #         return int(float(str(v).strip().split()[0]))
# # # #     except (ValueError, TypeError, IndexError):
# # # #         return None


# # # # def _persist_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
# # # #     """Return True if any edit was saved (needs rerun)."""
# # # #     mask = df["CTN NO"].astype(str) != "TOTAL"
# # # #     if not mask.any():
# # # #         return False

# # # #     changed = False
# # # #     prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])

# # # #     # ---- size cell edits ----
# # # #     if sizes:
# # # #         orig_sizes = df.loc[mask, sizes].fillna(-999)
# # # #         new_sizes  = edited.loc[mask, sizes].fillna(-999)
# # # #         if not orig_sizes.equals(new_sizes):
# # # #             new_units = {}
# # # #             for _, row in edited.loc[mask].iterrows():
# # # #                 for s in sizes:
# # # #                     v = row[s]
# # # #                     if pd.notna(v):
# # # #                         new_units[s] = int(v)
# # # #             st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
# # # #             changed = True

# # # #     # ---- CTN QTY edits ----
# # # #     orig_ctn = _to_int(df.loc[mask, "CTN QTY"].iloc[0])
# # # #     new_ctn  = _to_int(edited.loc[mask, "CTN QTY"].iloc[0])
# # # #     if new_ctn is not None and new_ctn != orig_ctn:
# # # #         st.session_state.ctn_edits.setdefault(color, {})[prepack] = new_ctn
# # # #         changed = True

# # # #     return changed


# # # # # ===========================================================================
# # # # # UI
# # # # # ===========================================================================
# # # # _init_state()

# # # # with st.sidebar:
# # # #     st.markdown("### ⚖️ Weight settings (kg)")
# # # #     st.caption("Edit any cell — values recalculate instantly.")

# # # #     edited_sidebar = st.data_editor(
# # # #         st.session_state.weights_df,
# # # #         use_container_width=True,
# # # #         num_rows="fixed",
# # # #         column_config={
# # # #             "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
# # # #             "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
# # # #             "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
# # # #         },
# # # #         key="weights_editor_sidebar",
# # # #     )
# # # #     if not edited_sidebar.equals(st.session_state.weights_df):
# # # #         st.session_state.weights_df = edited_sidebar
# # # #         st.rerun()

# # # #     if st.button("↺ Reset weights", use_container_width=True):
# # # #         st.session_state.weights_df = _default_weights_df()
# # # #         st.rerun()

# # # #     st.divider()
# # # #     st.markdown("### 📦 PER BLST")
# # # #     blst_c = st.number_input(
# # # #         "C  (multiplier, default 1)",
# # # #         min_value=1, max_value=8, value=1, step=1,
# # # #         help="PER BLST = \"Σ units_per_size X C\"",
# # # #     )
# # # #     st.caption(f"Formula: `PER BLST = \"A X {blst_c}\"`")

# # # #     st.divider()
# # # #     st.info(f"`CTN MES:` is fixed to **{FIXED_CTN_MES}**.")

# # # #     if st.button("↺ Reset all cell edits", use_container_width=True):
# # # #         st.session_state.size_edits = {}
# # # #         st.session_state.ctn_edits  = {}
# # # #         st.rerun()

# # # #     st.divider()
# # # #     json_path = st.text_input("JSON file path", DEFAULT_JSON)


# # # # if not Path(json_path).exists():
# # # #     st.error(f"File not found: `{json_path}`")
# # # #     st.stop()

# # # # weights = get_weights()
# # # # data = load_json(json_path)
# # # # groups = build_grouped(data, weights["NW"], weights["EMPTY"], blst_c)

# # # # if not groups:
# # # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # # #     st.stop()


# # # # # ===========================================================================
# # # # # Render
# # # # # ===========================================================================
# # # # all_frames: list = []

# # # # for color, rows in groups.items():
# # # #     sizes = present_sizes(rows)
# # # #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# # # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # # #     st.subheader(f"🎨 {color}")
# # # #     st.caption(
# # # #         f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s) · "
# # # #         "edit size cells or CTN QTY → totals update automatically"
# # # #     )

# # # #     render_size_weight_header(sizes, key_suffix=color)

# # # #     col_cfg = {
# # # #         "CTN NO":          st.column_config.TextColumn("CTN NO",  width="small", disabled=True),
# # # #         "CTN MES:":        st.column_config.TextColumn("CTN MES:", width="small", disabled=True),   # fixed
# # # #         "CTN QTY":         st.column_config.NumberColumn(
# # # #             "CTN QTY", width="small",
# # # #             min_value=1, step=1, format="%d",
# # # #             help="Editable. Number of cartons. Drives TOTAL row, TOTAL QTY, NET, GROSS.",
# # # #         ),
# # # #         "COLOR":           st.column_config.TextColumn("COLOR",           width="medium", disabled=True),
# # # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium", disabled=True),
# # # #         # derived → read-only
# # # #         "PER BLST":        st.column_config.TextColumn("PER BLST",   width="small", disabled=True),
# # # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small", disabled=True),
# # # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY",  width="small", disabled=True),
# # # #         "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f", disabled=True),
# # # #         "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT",   width="small", format="%.2f", disabled=True),
# # # #     }
# # # #     for s in sizes:
# # # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small", min_value=0, step=1)

# # # #     try:
# # # #         edited = st.data_editor(
# # # #             data=df,
# # # #             use_container_width=True,
# # # #             hide_index=True,
# # # #             num_rows="fixed",
# # # #             column_config=col_cfg,
# # # #             key=f"multi_editor_{color}",
# # # #         )
# # # #     except TypeError:
# # # #         st.warning("Upgrade Streamlit: pip install -U streamlit")
# # # #         st.dataframe(df, use_container_width=True, hide_index=True)
# # # #         edited = df

# # # #     if _persist_edits(color, df, edited, sizes):
# # # #         st.rerun()

# # # #     all_frames.append((color, edited))
# # # #     st.divider()


# # # # # ===========================================================================
# # # # # Downloads
# # # # # ===========================================================================
# # # # st.markdown("### Download")

# # # # export_rows: list = []
# # # # for i, (_, frame) in enumerate(all_frames):
# # # #     if i > 0:
# # # #         export_rows.append({})
# # # #     export_rows.extend(frame.to_dict(orient="records"))
# # # # combined = pd.DataFrame(export_rows)

# # # # col1, col2 = st.columns(2)
# # # # with col1:
# # # #     st.download_button(
# # # #         "⬇ Download CSV (all colors)",
# # # #         data=combined.to_csv(index=False).encode("utf-8"),
# # # #         file_name="packing_list_multi.csv", mime="text/csv",
# # # #         use_container_width=True,
# # # #     )
# # # # with col2:
# # # #     try:
# # # #         buf = io.BytesIO()
# # # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # # #             st.session_state.weights_df.to_excel(writer, sheet_name="Weights")
# # # #             for color, frame in all_frames:
# # # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # # #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# # # #         st.download_button(
# # # #             "⬇ Download Excel (one sheet per color)",
# # # #             data=buf.getvalue(), file_name="packing_list_multi.xlsx",
# # # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # # #             use_container_width=True,
# # # #         )
# # # #     except ImportError:
# # # #         st.info("Install openpyxl for Excel export")


# # # # # ===========================================================================
# # # # # Sidebar info
# # # # # ===========================================================================
# # # # with st.sidebar:
# # # #     st.markdown("### Colors detected")
# # # #     for color, rows in groups.items():
# # # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # # #         st.write(f"- **{color}** — {n} group(s)")



# # # """
# # # multi_pack.py
# # # -------------
# # # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.

# # # Layout per color group:
# # #     1. PO HEADER TABLE  (BUYER, STYLE, P.O.#, OIQTY, SHIP QTY, EX/SHORT,
# # #                          CTN QTY, CTN MEAS., PO#, SKU/Item, Unit/Prepack, CARTON)
# # #     2. MAIN PACKING TABLE  (CTN NO, CTN MES:, CTN QTY, COLOR, PREPACK STECKER,
# # #                             sizes..., PER BLST, QTY PER CTN, TOTAL QTY,
# # #                             GROSS WEIGHT, NET WEIGHT)

# # # Editable:
# # #     - size cells (units per size)
# # #     - CTN QTY (number of cartons)
# # #     - weight tables (sidebar)
# # #     - CTN MEAS. lines (sidebar)

# # # Fixed:
# # #     CTN MES: = "G82"

# # # Derived:
# # #     QTY PER CTN     = Σ units_per_size
# # #     PER BLST        = f"{QTY PER CTN} X C"  (C default 1)
# # #     NET (per ctn)   = Σ(units × N.W.)
# # #     GROSS (per ctn) = NET + EMPTY_CTN_WEIGHT
# # #     TOTAL QTY       = CTN QTY × QTY PER CTN
# # #     Total row [s]   = CTN QTY × units_per_size

# # # Header derived fields:
# # #     OIQTY     = Σ ORDER QTY of group rows
# # #     SHIP QTY  = Σ SHIP QTY of group rows
# # #     EX/SHORT  = OIQTY − SHIP QTY
# # #     CTN QTY   = group total "#PrePackets Ordered"
# # #     Unit/Prepk = f"{total_units_per_carton}/{ctn_qty}"
# # #     CARTON    = f"{color_index:02d} of {grand_total_ctn}"

# # # Run:
# # #     streamlit run multi_pack.py
# # # """

# # # import io
# # # import json
# # # from pathlib import Path

# # # import pandas as pd
# # # import streamlit as st


# # # # ===========================================================================
# # # # Config
# # # # ===========================================================================
# # # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # # st.title("📦 Packing List — Multi Pack (Y)")

# # # DEFAULT_JSON = "61480360.json"

# # # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # # FIXED_CTN_MES = "G82"    # ← fixed carton name (per your image)

# # # DEFAULT_NW    = {"XS": 0.510, "S": 0.520, "M": 0.550, "L": 0.560, "XL": 0.610, "XXL": 0.650, "XXL+": 0.690}
# # # DEFAULT_NNW   = {"XS": 0.49,  "S": 0.50,  "M": 0.53,  "L": 0.54,  "XL": 0.59,  "XXL": 0.63,  "XXL+": 0.67}
# # # DEFAULT_EMPTY = {"XS": 0.49,  "S": 1.00,  "M": 1.00,  "L": 1.00,  "XL": 1.00,  "XXL": 1.00,  "XXL+": 1.00}

# # # # Default CTN MEAS lines (editable in sidebar)
# # # DEFAULT_CTN_MEAS = [
# # #     "58.67 x 38.48 x 29.71 CM.G8. SL",
# # #     "58.67 x 38.48 x 14.86 CM.G8S. SL",
# # #     "38.48 x 29.33 x 14.86 CM.G8-M",
# # #     "29.33 x 19.25 x 14.86 CM.G-8XS",
# # #     "55.88 x 38.1  x 15.24 CM G13",
# # # ]

# # # # Default PO header fallback values (used if JSON has nulls)
# # # DEFAULT_BUYER   = "OLD NAVY"
# # # DEFAULT_STYLE   = "905518-00-1"
# # # DEFAULT_PO_NO   = "61480360"

# # # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # # ===========================================================================
# # # # Session state
# # # # ===========================================================================
# # # def _default_weights_df() -> pd.DataFrame:
# # #     return pd.DataFrame(
# # #         {
# # #             "SIZE":          SIZE_ORDER,
# # #             "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
# # #             "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
# # #             "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
# # #         }
# # #     ).set_index("SIZE")


# # # def _init_state():
# # #     if "weights_df" not in st.session_state:
# # #         st.session_state.weights_df = _default_weights_df()
# # #     if "size_edits" not in st.session_state:
# # #         st.session_state.size_edits = {}   # { color: { prepack: { size: units } } }
# # #     if "ctn_edits" not in st.session_state:
# # #         st.session_state.ctn_edits = {}    # { color: { prepack: ctn_qty } }
# # #     if "ctn_meas" not in st.session_state:
# # #         st.session_state.ctn_meas = list(DEFAULT_CTN_MEAS)


# # # def get_weights() -> dict:
# # #     df = st.session_state.weights_df
# # #     return {
# # #         "NW":    {s: float(df.loc[s, "N.W."])          for s in df.index},
# # #         "NNW":   {s: float(df.loc[s, "N.N.W."])        for s in df.index},
# # #         "EMPTY": {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index},
# # #     }


# # # # ===========================================================================
# # # # Helpers
# # # # ===========================================================================
# # # @st.cache_data(show_spinner=False)
# # # def load_json(path: str) -> dict:
# # #     with open(path, "r", encoding="utf-8") as f:
# # #         return json.load(f)


# # # def color_display(raw: str) -> str:
# # #     if not raw:
# # #         return ""
# # #     parts = raw.rsplit(" ", 1)
# # #     return parts[-1] if len(parts) > 1 else raw


# # # def color_code(raw: str) -> str:
# # #     """Extract '002' or '000' from '000905518-002 NAVY CAPTAIN'."""
# # #     if not raw:
# # #         return "000"
# # #     first = raw.split()[0] if raw.split() else ""
# # #     if "-" in first:
# # #         return first.split("-")[-1]
# # #     return "000"


# # # def present_sizes(rows: list) -> list:
# # #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # # def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
# # #     ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
# # #     return max(ws) if ws else 0.0


# # # def render_size_weight_header(sizes: list, key_suffix: str = "") -> None:
# # #     master = st.session_state.weights_df
# # #     view = master.loc[sizes].T.copy()
# # #     view.index.name = "SIZE"

# # #     edited = st.data_editor(
# # #         view,
# # #         use_container_width=False,
# # #         num_rows="fixed",
# # #         column_config={
# # #             s: st.column_config.NumberColumn(s, format="%.3f", step=0.001, width="small")
# # #             for s in view.columns
# # #         },
# # #         key=f"header_editor_{key_suffix}",
# # #     )
# # #     if not edited.equals(view):
# # #         for s in edited.columns:
# # #             st.session_state.weights_df.loc[s, "N.W."]          = float(edited.loc["N.W.", s])
# # #             st.session_state.weights_df.loc[s, "N.N.W."]        = float(edited.loc["N.N.W.", s])
# # #             st.session_state.weights_df.loc[s, "EMPTY CTN WT."] = float(edited.loc["EMPTY CTN WT.", s])
# # #         st.rerun()


# # # # ===========================================================================
# # # # PO HEADER TABLE — rendered above each color group's main table
# # # # ===========================================================================
# # # def render_po_header(
# # #     buyer: str,
# # #     style: str,
# # #     po_no: str,
# # #     oiqty: int,
# # #     ship_qty: int,
# # #     ex_short: int,
# # #     ctn_qty: int,
# # #     ctn_meas_list: list,
# # #     sku_item: str,
# # #     unit_prepack: str,
# # #     carton_label: str,
# # # ) -> None:
# # #     """
# # #     Render the boxed PO header block (BUYER, STYLE, P.O.#, OIQTY, SHIP QTY,
# # #     EX/SHORT, CTN QTY, CTN MEAS., PO#, SKU/Item, Unit/Prepack, CARTON).
# # #     """
# # #     meas_html = "".join(
# # #         f'<div class="po-line"><span class="po-label">CTN MEAS.</span>'
# # #         f'<span class="po-colon">:</span>'
# # #         f'<span class="po-value">{m}</span></div>'
# # #         for m in ctn_meas_list
# # #     )

# # #     html = f"""
# # #     <style>
# # #       .po-header {{
# # #         border: 2px solid #333;
# # #         border-radius: 6px;
# # #         padding: 10px 16px;
# # #         margin-bottom: 10px;
# # #         background: #fafafa;
# # #         font-family: 'Courier New', monospace;
# # #         font-size: 13px;
# # #         line-height: 1.55;
# # #       }}
# # #       .po-title {{
# # #         text-align: center;
# # #         font-weight: bold;
# # #         font-size: 16px;
# # #         letter-spacing: 2px;
# # #         margin-bottom: 8px;
# # #         border-bottom: 1px dashed #888;
# # #         padding-bottom: 6px;
# # #       }}
# # #       .po-grid {{
# # #         display: grid;
# # #         grid-template-columns: 1fr 1fr;
# # #         gap: 2px 30px;
# # #       }}
# # #       .po-col {{ }}
# # #       .po-line {{
# # #         display: flex;
# # #         align-items: baseline;
# # #       }}
# # #       .po-label {{
# # #         display: inline-block;
# # #         width: 90px;
# # #         font-weight: bold;
# # #       }}
# # #       .po-colon {{
# # #         width: 12px;
# # #         display: inline-block;
# # #         text-align: center;
# # #       }}
# # #       .po-value {{
# # #         display: inline-block;
# # #       }}
# # #     </style>
# # #     <div class="po-header">
# # #       <div class="po-title">MULTY PACK (Y)</div>
# # #       <div class="po-grid">
# # #         <div class="po-col">
# # #           <div class="po-line"><span class="po-label">BUYER</span><span class="po-colon">:</span><span class="po-value">{buyer}</span></div>
# # #           <div class="po-line"><span class="po-label">STYLE</span><span class="po-colon">:</span><span class="po-value">{style}</span></div>
# # #           <div class="po-line"><span class="po-label">P.O. #</span><span class="po-colon">:</span><span class="po-value">{po_no}</span></div>
# # #           <div class="po-line"><span class="po-label">OIQTY</span><span class="po-colon">:</span><span class="po-value">{oiqty} PCS</span></div>
# # #           <div class="po-line"><span class="po-label">SHIP QTY</span><span class="po-colon">:</span><span class="po-value">{ship_qty} PCS</span></div>
# # #           <div class="po-line"><span class="po-label">EX/SHORT</span><span class="po-colon">:</span><span class="po-value">{ex_short} PCS</span></div>
# # #           <div class="po-line"><span class="po-label">CTN QTY</span><span class="po-colon">:</span><span class="po-value">{ctn_qty} CTNS</span></div>
# # #           {meas_html}
# # #         </div>
# # #         <div class="po-col">
# # #           <div class="po-line"><span class="po-label">PO #</span><span class="po-colon">:</span><span class="po-value">{po_no}</span></div>
# # #           <div class="po-line"><span class="po-label">SKU / Item</span><span class="po-colon">:</span><span class="po-value">{sku_item}</span></div>
# # #           <div class="po-line"><span class="po-label">Unit / Prepack</span><span class="po-colon">:</span><span class="po-value">{unit_prepack}</span></div>
# # #           <div class="po-line"><span class="po-label">CARTON</span><span class="po-colon">:</span><span class="po-value">{carton_label}</span></div>
# # #         </div>
# # #       </div>
# # #     </div>
# # #     """
# # #     st.markdown(html, unsafe_allow_html=True)


# # # # ===========================================================================
# # # # Build packing list
# # # # ===========================================================================
# # # def build_grouped(data: dict, nw: dict, empty_weights: dict, blst_c: int) -> dict:
# # #     groups: dict = {}
# # #     ctn_counter: dict = {}

# # #     for _, table in data["tables"].items():
# # #         trows = table.get("rows") or []
# # #         total = table.get("total") or {}
# # #         if not trows:
# # #             continue

# # #         first = trows[0]
# # #         if first.get("PrePack Type") != "Multi" or first.get("Full Carton") != "Y":
# # #             continue

# # #         color   = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# # #         prepack = str(first.get("PrePack"))
# # #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# # #         row_no = ctn_counter[color]

# # #         # --- session overrides -------------------------------------------------
# # #         size_edits = st.session_state.size_edits.get(color, {}).get(prepack, {})
# # #         ctn_edit   = st.session_state.ctn_edits.get(color, {}).get(prepack)

# # #         row_sizes = []
# # #         for r in trows:
# # #             size  = r["Size Desc"]
# # #             units = int(size_edits.get(size, r.get("Units per PrePack") or 0))
# # #             row_sizes.append((size, units))

# # #         sizes_present = [s for s, _ in row_sizes]

# # #         # --- CTN QTY (cartons) -------------------------------------------------
# # #         json_ctn_mes = total.get("#PrePackets Ordered") or 0
# # #         ctn_qty = int(ctn_edit) if ctn_edit is not None else json_ctn_mes

# # #         # --- derived per-carton values ---------------------------------------
# # #         A           = sum(u for _, u in row_sizes)
# # #         qty_per_ctn = A
# # #         per_blst    = f"{A} X {blst_c}"

# # #         net_per_carton   = round(sum(u * nw.get(s, 0.0) for s, u in row_sizes), 2)
# # #         empty_ctn_weight = _empty_ctn_weight_for(sizes_present, empty_weights)
# # #         gross_per_carton = round(net_per_carton + empty_ctn_weight, 2)

# # #         # --- totals depend on ctn_qty ----------------------------------------
# # #         total_qty   = ctn_qty * qty_per_ctn
# # #         total_net   = round(ctn_qty * net_per_carton,   2) if ctn_qty else None
# # #         total_gross = round(ctn_qty * gross_per_carton, 2) if ctn_qty else None

# # #         # ---- header info (for PO header block) ----
# # #         header_info = {
# # #             "color":       color,
# # #             "color_code":  color_code(first.get("Universal CC #Color Desc", "")),
# # #             "prepack":     prepack,
# # #             "oiqty":       sum(int(r.get("ORDER QTY") or 0) for r in trows),
# # #             "ship_qty":    sum(int(r.get("SHIP QTY") or 0) for r in trows),
# # #             "ex_short":    max(
# # #                 sum(int(r.get("ORDER QTY") or 0) for r in trows)
# # #                 - sum(int(r.get("SHIP QTY") or 0) for r in trows),
# # #                 0,
# # #             ),
# # #             "ctn_qty":     ctn_qty,
# # #             "total_units_per_carton": qty_per_ctn,
# # #         }

# # #         # ---- data row ----
# # #         data_row = {
# # #             "CTN NO":          row_no,
# # #             "CTN MES:":        FIXED_CTN_MES,
# # #             "CTN QTY":         ctn_qty,
# # #             "COLOR":           color,
# # #             "PREPACK STECKER": prepack,
# # #         }
# # #         for s, u in row_sizes:
# # #             data_row[s] = u
# # #         data_row["PER BLST"]     = per_blst
# # #         data_row["QTY PER CTN"]  = qty_per_ctn
# # #         data_row["TOTAL QTY"]    = total_qty
# # #         data_row["GROSS WEIGHT"] = gross_per_carton
# # #         data_row["NET WEIGHT"]   = net_per_carton

# # #         # ---- total row ----
# # #         tot = {
# # #             "CTN NO":          "TOTAL",
# # #             "CTN MES:":        None,
# # #             "CTN QTY":         f"{ctn_qty} CTNS" if ctn_qty else None,
# # #             "COLOR":           None,
# # #             "PREPACK STECKER": None,
# # #         }
# # #         for s, u in row_sizes:
# # #             tot[s] = (ctn_qty * u) if ctn_qty else None
# # #         tot["PER BLST"]     = None
# # #         tot["QTY PER CTN"]  = None
# # #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# # #         tot["GROSS WEIGHT"] = total_gross
# # #         tot["NET WEIGHT"]   = total_net

# # #         groups.setdefault(color, []).append(data_row)
# # #         groups[color].append(tot)

# # #         # attach header info on first group only
# # #         if len(groups[color]) == 2:  # first data row + first total row
# # #             groups[color + "__header"] = header_info

# # #     return groups


# # # # ===========================================================================
# # # # Detect edits
# # # # ===========================================================================
# # # def _to_int(v):
# # #     if v is None:
# # #         return None
# # #     try:
# # #         return int(float(str(v).strip().split()[0]))
# # #     except (ValueError, TypeError, IndexError):
# # #         return None


# # # def _persist_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
# # #     mask = df["CTN NO"].astype(str) != "TOTAL"
# # #     if not mask.any():
# # #         return False

# # #     changed = False
# # #     prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])

# # #     if sizes:
# # #         orig_sizes = df.loc[mask, sizes].fillna(-999)
# # #         new_sizes  = edited.loc[mask, sizes].fillna(-999)
# # #         if not orig_sizes.equals(new_sizes):
# # #             new_units = {}
# # #             for _, row in edited.loc[mask].iterrows():
# # #                 for s in sizes:
# # #                     v = row[s]
# # #                     if pd.notna(v):
# # #                         new_units[s] = int(v)
# # #             st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
# # #             changed = True

# # #     orig_ctn = _to_int(df.loc[mask, "CTN QTY"].iloc[0])
# # #     new_ctn  = _to_int(edited.loc[mask, "CTN QTY"].iloc[0])
# # #     if new_ctn is not None and new_ctn != orig_ctn:
# # #         st.session_state.ctn_edits.setdefault(color, {})[prepack] = new_ctn
# # #         changed = True

# # #     return changed


# # # # ===========================================================================
# # # # UI
# # # # ===========================================================================
# # # _init_state()

# # # with st.sidebar:
# # #     st.markdown("### ⚖️ Weight settings (kg)")
# # #     st.caption("Edit any cell — values recalculate instantly.")

# # #     edited_sidebar = st.data_editor(
# # #         st.session_state.weights_df,
# # #         use_container_width=True,
# # #         num_rows="fixed",
# # #         column_config={
# # #             "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
# # #             "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
# # #             "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
# # #         },
# # #         key="weights_editor_sidebar",
# # #     )
# # #     if not edited_sidebar.equals(st.session_state.weights_df):
# # #         st.session_state.weights_df = edited_sidebar
# # #         st.rerun()

# # #     if st.button("↺ Reset weights", use_container_width=True):
# # #         st.session_state.weights_df = _default_weights_df()
# # #         st.rerun()

# # #     st.divider()
# # #     st.markdown("### 📦 CTN MEAS. (carton dimensions)")
# # #     st.caption("One line per carton type — appears in the PO header block.")
# # #     for i, m in enumerate(st.session_state.ctn_meas):
# # #         new_m = st.text_input(f"Line {i+1}", value=m, key=f"ctn_meas_{i}")
# # #         if new_m != m:
# # #             st.session_state.ctn_meas[i] = new_m

# # #     st.divider()
# # #     st.markdown("### 📦 PER BLST")
# # #     blst_c = st.number_input(
# # #         "C  (multiplier, default 1)",
# # #         min_value=1, max_value=8, value=1, step=1,
# # #         help='PER BLST = "Σ units_per_size X C"',
# # #     )
# # #     st.caption(f'Formula: `PER BLST = "A X {blst_c}"`')

# # #     st.divider()
# # #     st.info(f"`CTN MES:` is fixed to **{FIXED_CTN_MES}**.")

# # #     if st.button("↺ Reset all cell edits", use_container_width=True):
# # #         st.session_state.size_edits = {}
# # #         st.session_state.ctn_edits  = {}
# # #         st.rerun()

# # #     st.divider()
# # #     json_path = st.text_input("JSON file path", DEFAULT_JSON)


# # # if not Path(json_path).exists():
# # #     st.error(f"File not found: `{json_path}`")
# # #     st.stop()

# # # weights = get_weights()
# # # data = load_json(json_path)
# # # groups = build_grouped(data, weights["NW"], weights["EMPTY"], blst_c)

# # # # extract header info dict (stored under "<color>__header")
# # # header_map = {k.replace("__header", ""): v for k, v in groups.items() if k.endswith("__header")}
# # # # remove header keys from groups so they don't render as colors
# # # groups = {k: v for k, v in groups.items() if not k.endswith("__header")}

# # # if not groups:
# # #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# # #     st.stop()

# # # # PO-level fallbacks
# # # po_header = data.get("PO_HEADER", {}) or {}
# # # buyer_fixed = po_header.get("BUYER") or DEFAULT_BUYER
# # # po_no_fixed = po_header.get("P.O._#") or DEFAULT_PO_NO

# # # # Grand total cartons across all colors
# # # grand_total_ctn = sum(
# # #     (header_map[c]["ctn_qty"] or 0) for c in groups if c in header_map
# # # ) or 1


# # # # ===========================================================================
# # # # Render
# # # # ===========================================================================
# # # all_frames: list = []
# # # color_index = 0

# # # for color, rows in groups.items():
# # #     color_index += 1
# # #     sizes = present_sizes(rows)
# # #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# # #     df = pd.DataFrame(rows).reindex(columns=columns)

# # #     # ---- 1. PO HEADER BLOCK ----
# # #     hdr = header_map.get(color, {})
# # #     style_full = f"{DEFAULT_STYLE.rsplit('-', 2)[0]}-{hdr.get('color_code', '000')}-1"
# # #     sku_item   = style_full
# # #     unit_prepack = f"{hdr.get('total_units_per_carton', 0)}/{hdr.get('ctn_qty', 0)}"
# # #     carton_label = f"{color_index:02d} of {grand_total_ctn:03d}"

# # #     render_po_header(
# # #         buyer=buyer_fixed,
# # #         style=style_full,
# # #         po_no=po_no_fixed,
# # #         oiqty=hdr.get("oiqty", 0),
# # #         ship_qty=hdr.get("ship_qty", 0),
# # #         ex_short=hdr.get("ex_short", 0),
# # #         ctn_qty=hdr.get("ctn_qty", 0),
# # #         ctn_meas_list=st.session_state.ctn_meas,
# # #         sku_item=sku_item,
# # #         unit_prepack=unit_prepack,
# # #         carton_label=carton_label,
# # #     )

# # #     # ---- 2. MAIN PACKING TABLE ----
# # #     st.markdown(f"#### 🎨 {color}")
# # #     st.caption(
# # #         f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s) · "
# # #         "edit size cells or CTN QTY → totals update automatically"
# # #     )

# # #     render_size_weight_header(sizes, key_suffix=color)

# # #     col_cfg = {
# # #         "CTN NO":          st.column_config.TextColumn("CTN NO",  width="small", disabled=True),
# # #         "CTN MES:":        st.column_config.TextColumn("CTN MES:", width="small", disabled=True),
# # #         "CTN QTY":         st.column_config.NumberColumn(
# # #             "CTN QTY", width="small",
# # #             min_value=1, step=1, format="%d",
# # #             help="Editable. Number of cartons. Drives TOTAL row, TOTAL QTY, NET, GROSS.",
# # #         ),
# # #         "COLOR":           st.column_config.TextColumn("COLOR",           width="medium", disabled=True),
# # #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium", disabled=True),
# # #         "PER BLST":        st.column_config.TextColumn("PER BLST",   width="small", disabled=True),
# # #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small", disabled=True),
# # #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY",  width="small", disabled=True),
# # #         "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f", disabled=True),
# # #         "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT",   width="small", format="%.2f", disabled=True),
# # #     }
# # #     for s in sizes:
# # #         col_cfg[s] = st.column_config.NumberColumn(s, width="small", min_value=0, step=1)

# # #     try:
# # #         edited = st.data_editor(
# # #             data=df,
# # #             use_container_width=True,
# # #             hide_index=True,
# # #             num_rows="fixed",
# # #             column_config=col_cfg,
# # #             key=f"multi_editor_{color}",
# # #         )
# # #     except TypeError:
# # #         st.warning("Upgrade Streamlit: pip install -U streamlit")
# # #         st.dataframe(df, use_container_width=True, hide_index=True)
# # #         edited = df

# # #     if _persist_edits(color, df, edited, sizes):
# # #         st.rerun()

# # #     all_frames.append((color, edited))
# # #     st.divider()


# # # # ===========================================================================
# # # # Downloads
# # # # ===========================================================================
# # # st.markdown("### Download")

# # # export_rows: list = []
# # # for i, (_, frame) in enumerate(all_frames):
# # #     if i > 0:
# # #         export_rows.append({})
# # #     export_rows.extend(frame.to_dict(orient="records"))
# # # combined = pd.DataFrame(export_rows)

# # # col1, col2 = st.columns(2)
# # # with col1:
# # #     st.download_button(
# # #         "⬇ Download CSV (all colors)",
# # #         data=combined.to_csv(index=False).encode("utf-8"),
# # #         file_name="packing_list_multi.csv", mime="text/csv",
# # #         use_container_width=True,
# # #     )
# # # with col2:
# # #     try:
# # #         buf = io.BytesIO()
# # #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# # #             st.session_state.weights_df.to_excel(writer, sheet_name="Weights")
# # #             for color, frame in all_frames:
# # #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# # #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# # #         st.download_button(
# # #             "⬇ Download Excel (one sheet per color)",
# # #             data=buf.getvalue(), file_name="packing_list_multi.xlsx",
# # #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# # #             use_container_width=True,
# # #         )
# # #     except ImportError:
# # #         st.info("Install openpyxl for Excel export")


# # # # ===========================================================================
# # # # Sidebar info
# # # # ===========================================================================
# # # with st.sidebar:
# # #     st.markdown("### Colors detected")
# # #     for color, rows in groups.items():
# # #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# # #         st.write(f"- **{color}** — {n} group(s)")



# # """
# # multi_pack.py
# # -------------
# # Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.

# # Layout per color group:
# #     1. PO HEADER TABLE  (BUYER, STYLE, P.O.#, OIQTY, SHIP QTY, EX/SHORT,
# #                          CTN QTY, CTN MEAS., PO#, SKU/Item, Unit/Prepack, CARTON)
# #     2. MAIN PACKING TABLE  (CTN NO, CTN MES:, CTN QTY, COLOR, PREPACK STECKER,
# #                             sizes..., PER BLST, QTY PER CTN, TOTAL QTY,
# #                             GROSS WEIGHT, NET WEIGHT)

# # Editable:
# #     - size cells (units per size)
# #     - CTN QTY (number of cartons)
# #     - weight tables (sidebar)
# #     - CTN MEAS. lines (sidebar)

# # Fixed:
# #     CTN MES: = "G82"

# # Derived:
# #     QTY PER CTN     = Σ units_per_size
# #     PER BLST        = f"{QTY PER CTN} X C"  (C default 1)
# #     NET (per ctn)   = Σ(units × N.W.)
# #     GROSS (per ctn) = NET + EMPTY_CTN_WEIGHT
# #     TOTAL QTY       = CTN QTY × QTY PER CTN
# #     Total row [s]   = CTN QTY × units_per_size

# # Header derived fields:
# #     OIQTY     = total["ORDER QTY"]   (or Σ rows)
# #     SHIP QTY  = total["SHIP QTY"]    (or Σ rows)
# #     EX/SHORT  = total["EX-SHORT"]    (or OIQTY − SHIP QTY)
# #     CTN QTY   = group total "#PrePackets Ordered"
# #     Unit/Prepk = f"{total_units_per_carton}/{ctn_qty}"
# #     CARTON    = f"{color_index:02d} of {grand_total_ctn}"

# # Run:
# #     streamlit run multi_pack.py
# # """

# # import io
# # import json
# # from pathlib import Path

# # import pandas as pd
# # import streamlit as st


# # # ===========================================================================
# # # Config
# # # ===========================================================================
# # st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# # st.title("📦 Packing List — Multi Pack (Y)")

# # DEFAULT_JSON = "61480360.json"

# # SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# # FIXED_CTN_MES = "G82"    # ← fixed carton name (per your image)

# # DEFAULT_NW    = {"XS": 0.510, "S": 0.520, "M": 0.550, "L": 0.560, "XL": 0.610, "XXL": 0.650, "XXL+": 0.690}
# # DEFAULT_NNW   = {"XS": 0.49,  "S": 0.50,  "M": 0.53,  "L": 0.54,  "XL": 0.59,  "XXL": 0.63,  "XXL+": 0.67}
# # DEFAULT_EMPTY = {"XS": 0.49,  "S": 1.00,  "M": 1.00,  "L": 1.00,  "XL": 1.00,  "XXL": 1.00,  "XXL+": 1.00}

# # # Default CTN MEAS lines (editable in sidebar)
# # DEFAULT_CTN_MEAS = [
# #     "58.67 x 38.48 x 29.71 CM.G8. SL",
# #     "58.67 x 38.48 x 14.86 CM.G8S. SL",
# #     "38.48 x 29.33 x 14.86 CM.G8-M",
# #     "29.33 x 19.25 x 14.86 CM.G-8XS",
# #     "55.88 x 38.1  x 15.24 CM G13",
# # ]

# # # Default PO header fallback values (used if JSON has nulls)
# # DEFAULT_BUYER   = "OLD NAVY"
# # DEFAULT_STYLE   = "905518-00-1"
# # DEFAULT_PO_NO   = "61480360"

# # LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# # RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # # ===========================================================================
# # # Session state
# # # ===========================================================================
# # def _default_weights_df() -> pd.DataFrame:
# #     return pd.DataFrame(
# #         {
# #             "SIZE":          SIZE_ORDER,
# #             "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
# #             "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
# #             "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
# #         }
# #     ).set_index("SIZE")


# # def _init_state():
# #     if "weights_df" not in st.session_state:
# #         st.session_state.weights_df = _default_weights_df()
# #     if "size_edits" not in st.session_state:
# #         st.session_state.size_edits = {}   # { color: { prepack: { size: units } } }
# #     if "ctn_edits" not in st.session_state:
# #         st.session_state.ctn_edits = {}    # { color: { prepack: ctn_qty } }
# #     if "ctn_meas" not in st.session_state:
# #         st.session_state.ctn_meas = list(DEFAULT_CTN_MEAS)


# # def get_weights() -> dict:
# #     df = st.session_state.weights_df
# #     return {
# #         "NW":    {s: float(df.loc[s, "N.W."])          for s in df.index},
# #         "NNW":   {s: float(df.loc[s, "N.N.W."])        for s in df.index},
# #         "EMPTY": {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index},
# #     }


# # # ===========================================================================
# # # Helpers
# # # ===========================================================================
# # @st.cache_data(show_spinner=False)
# # def load_json(path: str) -> dict:
# #     with open(path, "r", encoding="utf-8") as f:
# #         return json.load(f)


# # def color_display(raw: str) -> str:
# #     if not raw:
# #         return ""
# #     parts = raw.rsplit(" ", 1)
# #     return parts[-1] if len(parts) > 1 else raw


# # def color_code(raw: str) -> str:
# #     """Extract '002' or '000' from '000905518-002 NAVY CAPTAIN'."""
# #     if not raw:
# #         return "000"
# #     first = raw.split()[0] if raw.split() else ""
# #     if "-" in first:
# #         return first.split("-")[-1]
# #     return "000"


# # def present_sizes(rows: list) -> list:
# #     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# # def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
# #     ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
# #     return max(ws) if ws else 0.0


# # def _int_or_none(v):
# #     """Safely convert a value to int, return None if impossible."""
# #     if v is None:
# #         return None
# #     try:
# #         return int(float(str(v).strip().split()[0]))
# #     except (TypeError, ValueError, IndexError):
# #         return None


# # def render_size_weight_header(sizes: list, key_suffix: str = "") -> None:
# #     master = st.session_state.weights_df
# #     view = master.loc[sizes].T.copy()
# #     view.index.name = "SIZE"

# #     edited = st.data_editor(
# #         view,
# #         use_container_width=False,
# #         num_rows="fixed",
# #         column_config={
# #             s: st.column_config.NumberColumn(s, format="%.3f", step=0.001, width="small")
# #             for s in view.columns
# #         },
# #         key=f"header_editor_{key_suffix}",
# #     )
# #     if not edited.equals(view):
# #         for s in edited.columns:
# #             st.session_state.weights_df.loc[s, "N.W."]          = float(edited.loc["N.W.", s])
# #             st.session_state.weights_df.loc[s, "N.N.W."]        = float(edited.loc["N.N.W.", s])
# #             st.session_state.weights_df.loc[s, "EMPTY CTN WT."] = float(edited.loc["EMPTY CTN WT.", s])
# #         st.rerun()


# # # ===========================================================================
# # # PO HEADER TABLE — rendered above each color group's main table
# # # ===========================================================================
# # def render_po_header(
# #     buyer: str,
# #     style: str,
# #     po_no: str,
# #     oiqty: int,
# #     ship_qty: int,
# #     ex_short: int,
# #     ctn_qty: int,
# #     ctn_meas_list: list,
# #     sku_item: str,
# #     unit_prepack: str,
# #     carton_label: str,
# # ) -> None:
# #     """
# #     Render the boxed PO header block (BUYER, STYLE, P.O.#, OIQTY, SHIP QTY,
# #     EX/SHORT, CTN QTY, CTN MEAS., PO#, SKU/Item, Unit/Prepack, CARTON).
# #     """
# #     meas_html = "".join(
# #         f'<div class="po-line"><span class="po-label">CTN MEAS.</span>'
# #         f'<span class="po-colon">:</span>'
# #         f'<span class="po-value">{m}</span></div>'
# #         for m in ctn_meas_list
# #     )

# #     html = f"""
# #     <style>
# #       .po-header {{
# #         border: 2px solid #333;
# #         border-radius: 6px;
# #         padding: 10px 16px;
# #         margin-bottom: 10px;
# #         background: #fafafa;
# #         font-family: 'Courier New', monospace;
# #         font-size: 13px;
# #         line-height: 1.55;
# #       }}
# #       .po-title {{
# #         text-align: center;
# #         font-weight: bold;
# #         font-size: 16px;
# #         letter-spacing: 2px;
# #         margin-bottom: 8px;
# #         border-bottom: 1px dashed #888;
# #         padding-bottom: 6px;
# #       }}
# #       .po-grid {{
# #         display: grid;
# #         grid-template-columns: 1fr 1fr;
# #         gap: 2px 30px;
# #       }}
# #       .po-col {{ }}
# #       .po-line {{
# #         display: flex;
# #         align-items: baseline;
# #       }}
# #       .po-label {{
# #         display: inline-block;
# #         width: 110px;
# #         font-weight: bold;
# #       }}
# #       .po-colon {{
# #         width: 12px;
# #         display: inline-block;
# #         text-align: center;
# #       }}
# #       .po-value {{
# #         display: inline-block;
# #       }}
# #     </style>
# #     <div class="po-header">
# #       <div class="po-title">MULTY PACK (Y)</div>
# #       <div class="po-grid">
# #         <div class="po-col">
# #           <div class="po-line"><span class="po-label">BUYER</span><span class="po-colon">:</span><span class="po-value">{buyer}</span></div>
# #           <div class="po-line"><span class="po-label">STYLE</span><span class="po-colon">:</span><span class="po-value">{style}</span></div>
# #           <div class="po-line"><span class="po-label">P.O. #</span><span class="po-colon">:</span><span class="po-value">{po_no}</span></div>
# #           <div class="po-line"><span class="po-label">OIQTY</span><span class="po-colon">:</span><span class="po-value">{oiqty} PCS</span></div>
# #           <div class="po-line"><span class="po-label">SHIP QTY</span><span class="po-colon">:</span><span class="po-value">{ship_qty} PCS</span></div>
# #           <div class="po-line"><span class="po-label">EX/SHORT</span><span class="po-colon">:</span><span class="po-value">{ex_short} PCS</span></div>
# #           <div class="po-line"><span class="po-label">CTN QTY</span><span class="po-colon">:</span><span class="po-value">{ctn_qty} CTNS</span></div>
# #           {meas_html}
# #         </div>
# #         <div class="po-col">
# #           <div class="po-line"><span class="po-label">PO #</span><span class="po-colon">:</span><span class="po-value">{po_no}</span></div>
# #           <div class="po-line"><span class="po-label">SKU / Item</span><span class="po-colon">:</span><span class="po-value">{sku_item}</span></div>
# #           <div class="po-line"><span class="po-label">Unit / Prepack</span><span class="po-colon">:</span><span class="po-value">{unit_prepack}</span></div>
# #           <div class="po-line"><span class="po-label">CARTON</span><span class="po-colon">:</span><span class="po-value">{carton_label}</span></div>
# #         </div>
# #       </div>
# #     </div>
# #     """
# #     st.markdown(html, unsafe_allow_html=True)


# # # ===========================================================================
# # # Build packing list
# # # ===========================================================================
# # def build_grouped(data: dict, nw: dict, empty_weights: dict, blst_c: int) -> dict:
# #     groups: dict = {}
# #     ctn_counter: dict = {}

# #     for _, table in data["tables"].items():
# #         trows = table.get("rows") or []
# #         total = table.get("total") or {}
# #         if not trows:
# #             continue

# #         first = trows[0]
# #         if first.get("PrePack Type") != "Multi" or first.get("Full Carton") != "Y":
# #             continue

# #         color   = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
# #         prepack = str(first.get("PrePack"))
# #         ctn_counter[color] = ctn_counter.get(color, 0) + 1
# #         row_no = ctn_counter[color]

# #         # --- session overrides ---
# #         size_edits = st.session_state.size_edits.get(color, {}).get(prepack, {})
# #         ctn_edit   = st.session_state.ctn_edits.get(color, {}).get(prepack)

# #         row_sizes = []
# #         for r in trows:
# #             size  = r["Size Desc"]
# #             units = int(size_edits.get(size, r.get("Units per PrePack") or 0))
# #             row_sizes.append((size, units))

# #         sizes_present = [s for s, _ in row_sizes]

# #         # --- CTN QTY (cartons) ---
# #         json_ctn_mes = _int_or_none(total.get("#PrePackets Ordered")) or 0
# #         ctn_qty = int(ctn_edit) if ctn_edit is not None else int(json_ctn_mes)

# #         # --- derived per-carton values ---
# #         A           = sum(u for _, u in row_sizes)
# #         qty_per_ctn = A
# #         per_blst    = f"{A} X {blst_c}"

# #         net_per_carton   = round(sum(u * nw.get(s, 0.0) for s, u in row_sizes), 2)
# #         empty_ctn_weight = _empty_ctn_weight_for(sizes_present, empty_weights)
# #         gross_per_carton = round(net_per_carton + empty_ctn_weight, 2)

# #         # --- totals depend on ctn_qty ---
# #         total_qty   = ctn_qty * qty_per_ctn
# #         total_net   = round(ctn_qty * net_per_carton,   2) if ctn_qty else None
# #         total_gross = round(ctn_qty * gross_per_carton, 2) if ctn_qty else None

# #         # ---- header info (FIXED: read total first, then rows) ----
# #         oiqty_total    = _int_or_none(total.get("ORDER QTY"))
# #         ship_qty_total = _int_or_none(total.get("SHIP QTY"))
# #         ex_short_total = _int_or_none(total.get("EX-SHORT"))

# #         if oiqty_total is None:
# #             oiqty_total = sum(_int_or_none(r.get("ORDER QTY")) or 0 for r in trows)
# #         if ship_qty_total is None:
# #             ship_qty_total = sum(_int_or_none(r.get("SHIP QTY")) or 0 for r in trows)
# #         if ex_short_total is None:
# #             ex_short_total = max(oiqty_total - ship_qty_total, 0)

# #         header_info = {
# #             "color":       color,
# #             "color_code":  color_code(first.get("Universal CC #Color Desc", "")),
# #             "prepack":     prepack,
# #             "oiqty":       oiqty_total,
# #             "ship_qty":    ship_qty_total,
# #             "ex_short":    ex_short_total,
# #             "ctn_qty":     ctn_qty,
# #             "total_units_per_carton": qty_per_ctn,
# #         }

# #         # ---- data row ----
# #         data_row = {
# #             "CTN NO":          row_no,
# #             "CTN MES:":        FIXED_CTN_MES,
# #             "CTN QTY":         ctn_qty,
# #             "COLOR":           color,
# #             "PREPACK STECKER": prepack,
# #         }
# #         for s, u in row_sizes:
# #             data_row[s] = u
# #         data_row["PER BLST"]     = per_blst
# #         data_row["QTY PER CTN"]  = qty_per_ctn
# #         data_row["TOTAL QTY"]    = total_qty
# #         data_row["GROSS WEIGHT"] = gross_per_carton
# #         data_row["NET WEIGHT"]   = net_per_carton

# #         # ---- total row ----
# #         tot = {
# #             "CTN NO":          "TOTAL",
# #             "CTN MES:":        None,
# #             "CTN QTY":         f"{ctn_qty} CTNS" if ctn_qty else None,
# #             "COLOR":           None,
# #             "PREPACK STECKER": None,
# #         }
# #         for s, u in row_sizes:
# #             tot[s] = (ctn_qty * u) if ctn_qty else None
# #         tot["PER BLST"]     = None
# #         tot["QTY PER CTN"]  = None
# #         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
# #         tot["GROSS WEIGHT"] = total_gross
# #         tot["NET WEIGHT"]   = total_net

# #         groups.setdefault(color, []).append(data_row)
# #         groups[color].append(tot)

# #         # attach header info on first group only
# #         if len(groups[color]) == 2:
# #             groups[color + "__header"] = header_info

# #     return groups


# # # ===========================================================================
# # # Detect edits
# # # ===========================================================================
# # def _persist_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
# #     mask = df["CTN NO"].astype(str) != "TOTAL"
# #     if not mask.any():
# #         return False

# #     changed = False
# #     prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])

# #     if sizes:
# #         orig_sizes = df.loc[mask, sizes].fillna(-999)
# #         new_sizes  = edited.loc[mask, sizes].fillna(-999)
# #         if not orig_sizes.equals(new_sizes):
# #             new_units = {}
# #             for _, row in edited.loc[mask].iterrows():
# #                 for s in sizes:
# #                     v = row[s]
# #                     if pd.notna(v):
# #                         new_units[s] = int(v)
# #             st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
# #             changed = True

# #     orig_ctn = _to_int(df.loc[mask, "CTN QTY"].iloc[0])
# #     new_ctn  = _to_int(edited.loc[mask, "CTN QTY"].iloc[0])
# #     if new_ctn is not None and new_ctn != orig_ctn:
# #         st.session_state.ctn_edits.setdefault(color, {})[prepack] = new_ctn
# #         changed = True

# #     return changed


# # # ===========================================================================
# # # UI
# # # ===========================================================================
# # _init_state()

# # with st.sidebar:
# #     st.markdown("### ⚖️ Weight settings (kg)")
# #     st.caption("Edit any cell — values recalculate instantly.")

# #     edited_sidebar = st.data_editor(
# #         st.session_state.weights_df,
# #         use_container_width=True,
# #         num_rows="fixed",
# #         column_config={
# #             "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
# #             "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
# #             "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
# #         },
# #         key="weights_editor_sidebar",
# #     )
# #     if not edited_sidebar.equals(st.session_state.weights_df):
# #         st.session_state.weights_df = edited_sidebar
# #         st.rerun()

# #     if st.button("↺ Reset weights", use_container_width=True):
# #         st.session_state.weights_df = _default_weights_df()
# #         st.rerun()

# #     st.divider()
# #     st.markdown("### 📦 CTN MEAS. (carton dimensions)")
# #     st.caption("One line per carton type — appears in the PO header block.")
# #     for i, m in enumerate(st.session_state.ctn_meas):
# #         new_m = st.text_input(f"Line {i+1}", value=m, key=f"ctn_meas_{i}")
# #         if new_m != m:
# #             st.session_state.ctn_meas[i] = new_m

# #     st.divider()
# #     st.markdown("### 📦 PER BLST")
# #     blst_c = st.number_input(
# #         "C  (multiplier, default 1)",
# #         min_value=1, max_value=8, value=1, step=1,
# #         help='PER BLST = "Σ units_per_size X C"',
# #     )
# #     st.caption(f'Formula: `PER BLST = "A X {blst_c}"`')

# #     st.divider()
# #     st.info(f"`CTN MES:` is fixed to **{FIXED_CTN_MES}**.")

# #     if st.button("↺ Reset all cell edits", use_container_width=True):
# #         st.session_state.size_edits = {}
# #         st.session_state.ctn_edits  = {}
# #         st.rerun()

# #     st.divider()
# #     json_path = st.text_input("JSON file path", DEFAULT_JSON)


# # if not Path(json_path).exists():
# #     st.error(f"File not found: `{json_path}`")
# #     st.stop()

# # weights = get_weights()
# # data = load_json(json_path)
# # groups = build_grouped(data, weights["NW"], weights["EMPTY"], blst_c)

# # # extract header info dict (stored under "<color>__header")
# # header_map = {k.replace("__header", ""): v for k, v in groups.items() if k.endswith("__header")}
# # # remove header keys from groups so they don't render as colors
# # groups = {k: v for k, v in groups.items() if not k.endswith("__header")}

# # if not groups:
# #     st.warning("No Multi Pack (Y) tables found in the JSON.")
# #     st.stop()

# # # PO-level fallbacks
# # po_header = data.get("PO_HEADER", {}) or {}
# # buyer_fixed = po_header.get("BUYER") or DEFAULT_BUYER
# # po_no_fixed = po_header.get("P.O._#") or DEFAULT_PO_NO

# # # Grand total cartons across all colors
# # grand_total_ctn = sum(
# #     (header_map[c]["ctn_qty"] or 0) for c in groups if c in header_map
# # ) or 1


# # # ===========================================================================
# # # Render
# # # ===========================================================================
# # all_frames: list = []
# # color_index = 0

# # for color, rows in groups.items():
# #     color_index += 1
# #     sizes = present_sizes(rows)
# #     columns = LEFT_STATIC + sizes + RIGHT_STATIC
# #     df = pd.DataFrame(rows).reindex(columns=columns)

# #     # ---- 1. PO HEADER BLOCK ----
# #     hdr = header_map.get(color, {})
# #     style_full = f"{DEFAULT_STYLE.rsplit('-', 2)[0]}-{hdr.get('color_code', '000')}-1"
# #     sku_item   = style_full
# #     unit_prepack = f"{hdr.get('total_units_per_carton', 0)}/{hdr.get('ctn_qty', 0)}"
# #     carton_label = f"{color_index:02d} of {grand_total_ctn:03d}"

# #     render_po_header(
# #         buyer=buyer_fixed,
# #         style=style_full,
# #         po_no=po_no_fixed,
# #         oiqty=hdr.get("oiqty", 0),
# #         ship_qty=hdr.get("ship_qty", 0),
# #         ex_short=hdr.get("ex_short", 0),
# #         ctn_qty=hdr.get("ctn_qty", 0),
# #         ctn_meas_list=st.session_state.ctn_meas,
# #         sku_item=sku_item,
# #         unit_prepack=unit_prepack,
# #         carton_label=carton_label,
# #     )

# #     # ---- 2. MAIN PACKING TABLE ----
# #     st.markdown(f"#### 🎨 {color}")
# #     st.caption(
# #         f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s) · "
# #         "edit size cells or CTN QTY → totals update automatically"
# #     )

# #     render_size_weight_header(sizes, key_suffix=color)

# #     col_cfg = {
# #         "CTN NO":          st.column_config.TextColumn("CTN NO",  width="small", disabled=True),
# #         "CTN MES:":        st.column_config.TextColumn("CTN MES:", width="small", disabled=True),
# #         "CTN QTY":         st.column_config.NumberColumn(
# #             "CTN QTY", width="small",
# #             min_value=1, step=1, format="%d",
# #             help="Editable. Number of cartons. Drives TOTAL row, TOTAL QTY, NET, GROSS.",
# #         ),
# #         "COLOR":           st.column_config.TextColumn("COLOR",           width="medium", disabled=True),
# #         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium", disabled=True),
# #         "PER BLST":        st.column_config.TextColumn("PER BLST",   width="small", disabled=True),
# #         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small", disabled=True),
# #         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY",  width="small", disabled=True),
# #         "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f", disabled=True),
# #         "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT",   width="small", format="%.2f", disabled=True),
# #     }
# #     for s in sizes:
# #         col_cfg[s] = st.column_config.NumberColumn(s, width="small", min_value=0, step=1)

# #     try:
# #         edited = st.data_editor(
# #             data=df,
# #             use_container_width=True,
# #             hide_index=True,
# #             num_rows="fixed",
# #             column_config=col_cfg,
# #             key=f"multi_editor_{color}",
# #         )
# #     except TypeError:
# #         st.warning("Upgrade Streamlit: pip install -U streamlit")
# #         st.dataframe(df, use_container_width=True, hide_index=True)
# #         edited = df

# # # ===========================================================================
# # # Detect edits
# # # ===========================================================================
# # def _persist_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
# #     mask = df["CTN NO"].astype(str) != "TOTAL"
# #     if not mask.any():
# #         return False

# #     changed = False
# #     prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])

# #     if sizes:
# #         orig_sizes = df.loc[mask, sizes].fillna(-999)
# #         new_sizes  = edited.loc[mask, sizes].fillna(-999)
# #         if not orig_sizes.equals(new_sizes):
# #             new_units = {}
# #             for _, row in edited.loc[mask].iterrows():
# #                 for s in sizes:
# #                     v = row[s]
# #                     if pd.notna(v):
# #                         new_units[s] = int(v)
# #             st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
# #             changed = True

# #     orig_ctn = _int_or_none(df.loc[mask, "CTN QTY"].iloc[0])
# #     new_ctn  = _int_or_none(edited.loc[mask, "CTN QTY"].iloc[0])
# #     if new_ctn is not None and new_ctn != orig_ctn:
# #         st.session_state.ctn_edits.setdefault(color, {})[prepack] = new_ctn
# #         changed = True

# #     return changed

# #     all_frames.append((color, edited))
# #     st.divider()


# # # ===========================================================================
# # # Downloads
# # # ===========================================================================
# # st.markdown("### Download")

# # export_rows: list = []
# # for i, (_, frame) in enumerate(all_frames):
# #     if i > 0:
# #         export_rows.append({})
# #     export_rows.extend(frame.to_dict(orient="records"))
# # combined = pd.DataFrame(export_rows)

# # col1, col2 = st.columns(2)
# # with col1:
# #     st.download_button(
# #         "⬇ Download CSV (all colors)",
# #         data=combined.to_csv(index=False).encode("utf-8"),
# #         file_name="packing_list_multi.csv", mime="text/csv",
# #         use_container_width=True,
# #     )
# # with col2:
# #     try:
# #         buf = io.BytesIO()
# #         with pd.ExcelWriter(buf, engine="openpyxl") as writer:
# #             st.session_state.weights_df.to_excel(writer, sheet_name="Weights")
# #             for color, frame in all_frames:
# #                 sheet = color[:31].replace("/", "-").replace("\\", "-")
# #                 frame.to_excel(writer, index=False, sheet_name=sheet)
# #         st.download_button(
# #             "⬇ Download Excel (one sheet per color)",
# #             data=buf.getvalue(), file_name="packing_list_multi.xlsx",
# #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# #             use_container_width=True,
# #         )
# #     except ImportError:
# #         st.info("Install openpyxl for Excel export")


# # # ===========================================================================
# # # Sidebar info
# # # ===========================================================================
# # with st.sidebar:
# #     st.markdown("### Colors detected")
# #     for color, rows in groups.items():
# #         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
# #         st.write(f"- **{color}** — {n} group(s)")



# """
# multi_y_packing.py
# ------------------
# Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.

# Layout per color group:
#     1. COMPACT PO HEADER  (5 rows: title + 3 grid rows + CTN MEAS)
#     2. MAIN PACKING TABLE (CTN NO, CTN MES:, CTN QTY, COLOR, PREPACK STECKER,
#                            sizes..., PER BLST, QTY PER CTN, TOTAL QTY,
#                            GROSS WEIGHT, NET WEIGHT)

# Excel export mirrors: Style - 905518 PO - 61480360 - Qty - 4598 Pcs Multi Y OK.xlsx
#     Sheet 'PKL' : company header + weights + per-color PO blocks + summary
#     Sheet 'sum' : packing list summary table (DC, PO NO, SEASON, COLOR/CODE, ...)

# Run:
#     streamlit run multi_y_packing.py
# """

# import io
# import json
# from pathlib import Path

# import pandas as pd
# import streamlit as st

# # ===========================================================================
# # Config
# # ===========================================================================
# st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
# st.title("📦 Packing List — Multi Pack (Y)")

# DEFAULT_JSON = "61480360.json"

# SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

# FIXED_CTN_MES = "G82"

# DEFAULT_NW    = {"XS": 0.510, "S": 0.520, "M": 0.550, "L": 0.560, "XL": 0.610, "XXL": 0.650, "XXL+": 0.690}
# DEFAULT_NNW   = {"XS": 0.490, "S": 0.500, "M": 0.530, "L": 0.540, "XL": 0.590, "XXL": 0.630, "XXL+": 0.670}
# DEFAULT_EMPTY = {"XS": 0.490, "S": 1.000, "M": 1.000, "L": 1.000, "XL": 1.000, "XXL": 1.000, "XXL+": 1.000}

# DEFAULT_CTN_MEAS = [
#     "58.67 X 38.48 X 29.71 CM.G8_SL",
#     "58.67 X 38.48 X 14.86 CM.G8S_SL",
#     "38.48 X 29.33 X 14.86 CM.G-8M",
#     "29.33 X 19.25 X 14.86 CM.G-8XS",
#     "55.88 X 38.1 X 15.24 CM G13",
# ]

# DEFAULT_BUYER = "OLD NAVY"
# DEFAULT_STYLE = "905518-00-1"
# DEFAULT_PO_NO = "61480360"

# LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
# RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# # ===========================================================================
# # Session state
# # ===========================================================================
# def _default_weights_df() -> pd.DataFrame:
#     return pd.DataFrame(
#         {
#             "SIZE":          SIZE_ORDER,
#             "N.W.":          [DEFAULT_NW[s]    for s in SIZE_ORDER],
#             "N.N.W.":        [DEFAULT_NNW[s]   for s in SIZE_ORDER],
#             "EMPTY CTN WT.": [DEFAULT_EMPTY[s] for s in SIZE_ORDER],
#         }
#     ).set_index("SIZE")


# def _init_state():
#     if "weights_df" not in st.session_state:
#         st.session_state.weights_df = _default_weights_df()
#     if "size_edits" not in st.session_state:
#         st.session_state.size_edits = {}
#     if "ctn_edits" not in st.session_state:
#         st.session_state.ctn_edits = {}
#     if "ctn_meas" not in st.session_state:
#         st.session_state.ctn_meas = list(DEFAULT_CTN_MEAS)


# def get_weights() -> dict:
#     df = st.session_state.weights_df
#     return {
#         "NW":    {s: float(df.loc[s, "N.W."])          for s in df.index},
#         "NNW":   {s: float(df.loc[s, "N.N.W."])        for s in df.index},
#         "EMPTY": {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index},
#     }


# # ===========================================================================
# # Helpers
# # ===========================================================================
# @st.cache_data(show_spinner=False)
# def load_json(path: str) -> dict:
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def color_display(raw: str) -> str:
#     if not raw:
#         return ""
#     parts = raw.rsplit(" ", 1)
#     return parts[-1] if len(parts) > 1 else raw


# def color_code(raw: str) -> str:
#     if not raw:
#         return "000"
#     first = raw.split()[0] if raw.split() else ""
#     if "-" in first:
#         return first.split("-")[-1]
#     return "000"


# def present_sizes(rows: list) -> list:
#     return [s for s in SIZE_ORDER if any(s in r for r in rows)]


# def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
#     ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
#     return max(ws) if ws else 0.0


# def _int_or_none(v):
#     if v is None:
#         return None
#     try:
#         return int(float(str(v).strip().split()[0]))
#     except (TypeError, ValueError, IndexError):
#         return None


# def render_size_weight_header(sizes: list, key_suffix: str = "") -> None:
#     master = st.session_state.weights_df
#     view = master.loc[sizes].T.copy()
#     view.index.name = "SIZE"

#     edited = st.data_editor(
#         view,
#         use_container_width=False,
#         num_rows="fixed",
#         column_config={
#             s: st.column_config.NumberColumn(s, format="%.3f", step=0.001, width="small")
#             for s in view.columns
#         },
#         key=f"header_editor_{key_suffix}",
#     )
#     if not edited.equals(view):
#         for s in edited.columns:
#             st.session_state.weights_df.loc[s, "N.W."]          = float(edited.loc["N.W.", s])
#             st.session_state.weights_df.loc[s, "N.N.W."]        = float(edited.loc["N.N.W.", s])
#             st.session_state.weights_df.loc[s, "EMPTY CTN WT."] = float(edited.loc["EMPTY CTN WT.", s])
#         st.rerun()


# # ===========================================================================
# # COMPACT PO HEADER (5 rows: title + 3 grid rows + CTN MEAS line)
# # ===========================================================================
# def render_po_header(
#     buyer: str, style: str, po_no: str,
#     oiqty: int, ship_qty: int, ex_short: int, ctn_qty: int,
#     ctn_meas_list: list, sku_item: str,
#     unit_prepack: str, carton_label: str,
# ) -> None:
#     meas_compact = " · ".join(ctn_meas_list)

#     html = f"""
#     <style>
#       .po-header-compact {{
#         border: 2px solid #333; border-radius: 6px;
#         padding: 8px 12px; margin-bottom: 10px; background: #fafafa;
#         font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.55;
#       }}
#       .po-title-compact {{
#         text-align: center; font-weight: bold; font-size: 15px;
#         letter-spacing: 2px; margin-bottom: 6px;
#         border-bottom: 1px dashed #888; padding-bottom: 4px;
#       }}
#       .po-grid-compact {{
#         display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px 16px;
#       }}
#       .po-cell {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
#       .po-cell b {{ display: inline-block; min-width: 90px; }}
#       .po-meas-row {{
#         margin-top: 6px; border-top: 1px dashed #bbb; padding-top: 4px;
#         font-size: 12px; color: #222; grid-column: 1 / -1;
#         white-space: normal; line-height: 1.5;
#       }}
#       .po-meas-row b {{ margin-right: 6px; }}
#     </style>
#     <div class="po-header-compact">
#       <div class="po-title-compact">MULTY PACK (Y)</div>
#       <div class="po-grid-compact">
#         <div class="po-cell"><b>BUYER</b>: {buyer}</div>
#         <div class="po-cell"><b>STYLE</b>: {style}</div>
#         <div class="po-cell"><b>P.O. #</b>: {po_no}</div>
#         <div class="po-cell"><b>OIQTY</b>: {oiqty} PCS</div>
#         <div class="po-cell"><b>SHIP QTY</b>: {ship_qty} PCS</div>
#         <div class="po-cell"><b>EX/SHORT</b>: {ex_short} PCS</div>
#         <div class="po-cell"><b>CTN QTY</b>: {ctn_qty} CTNS</div>
#         <div class="po-cell"><b>CARTON</b>: {carton_label}</div>
#         <div class="po-cell"><b>PO #</b>: {po_no}</div>
#         <div class="po-cell"><b>SKU / Item</b>: {sku_item}</div>
#         <div class="po-cell"><b>Unit/Prepack</b>: {unit_prepack}</div>
#         <div class="po-cell"></div>
#         <div class="po-meas-row"><b>CTN MEAS:</b> {meas_compact}</div>
#       </div>
#     </div>
#     """
#     st.markdown(html, unsafe_allow_html=True)


# # ===========================================================================
# # Build packing list
# # ===========================================================================
# def build_grouped(data: dict, nw: dict, empty_weights: dict, blst_c: int) -> dict:
#     groups: dict = {}
#     ctn_counter: dict = {}

#     for _, table in data["tables"].items():
#         trows = table.get("rows") or []
#         total = table.get("total") or {}
#         if not trows:
#             continue

#         first = trows[0]
#         if first.get("PrePack Type") != "Multi" or first.get("Full Carton") != "Y":
#             continue

#         color   = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
#         prepack = str(first.get("PrePack"))
#         ctn_counter[color] = ctn_counter.get(color, 0) + 1
#         row_no = ctn_counter[color]

#         size_edits = st.session_state.size_edits.get(color, {}).get(prepack, {})
#         ctn_edit   = st.session_state.ctn_edits.get(color, {}).get(prepack)

#         row_sizes = []
#         for r in trows:
#             size  = r["Size Desc"]
#             units = int(size_edits.get(size, r.get("Units per PrePack") or 0))
#             row_sizes.append((size, units))

#         sizes_present = [s for s, _ in row_sizes]

#         json_ctn_mes = _int_or_none(total.get("#PrePackets Ordered")) or 0
#         ctn_qty = int(ctn_edit) if ctn_edit is not None else int(json_ctn_mes)

#         A           = sum(u for _, u in row_sizes)
#         qty_per_ctn = A
#         per_blst    = f"{A} X {blst_c}"

#         net_per_carton   = round(sum(u * nw.get(s, 0.0) for s, u in row_sizes), 2)
#         empty_ctn_weight = _empty_ctn_weight_for(sizes_present, empty_weights)
#         gross_per_carton = round(net_per_carton + empty_ctn_weight, 2)

#         total_qty   = ctn_qty * qty_per_ctn
#         total_net   = round(ctn_qty * net_per_carton,   2) if ctn_qty else None
#         total_gross = round(ctn_qty * gross_per_carton, 2) if ctn_qty else None

#         oiqty_total    = _int_or_none(total.get("ORDER QTY"))
#         ship_qty_total = _int_or_none(total.get("SHIP QTY"))
#         ex_short_total = _int_or_none(total.get("EX-SHORT"))

#         if oiqty_total is None:
#             oiqty_total = sum(_int_or_none(r.get("ORDER QTY")) or 0 for r in trows)
#         if ship_qty_total is None:
#             ship_qty_total = sum(_int_or_none(r.get("SHIP QTY")) or 0 for r in trows)
#         if ex_short_total is None:
#             ex_short_total = max(oiqty_total - ship_qty_total, 0)

#         header_info = {
#             "color": color,
#             "color_code": color_code(first.get("Universal CC #Color Desc", "")),
#             "prepack": prepack,
#             "oiqty": oiqty_total,
#             "ship_qty": ship_qty_total,
#             "ex_short": ex_short_total,
#             "ctn_qty": ctn_qty,
#             "total_units_per_carton": qty_per_ctn,
#         }

#         data_row = {
#             "CTN NO": row_no, "CTN MES:": FIXED_CTN_MES,
#             "CTN QTY": ctn_qty, "COLOR": color,
#             "PREPACK STECKER": prepack,
#         }
#         for s, u in row_sizes:
#             data_row[s] = u
#         data_row["PER BLST"]     = per_blst
#         data_row["QTY PER CTN"]  = qty_per_ctn
#         data_row["TOTAL QTY"]    = total_qty
#         data_row["GROSS WEIGHT"] = gross_per_carton
#         data_row["NET WEIGHT"]   = net_per_carton

#         tot = {
#             "CTN NO": "TOTAL", "CTN MES:": None,
#             "CTN QTY": f"{ctn_qty} CTNS" if ctn_qty else None,
#             "COLOR": None, "PREPACK STECKER": None,
#         }
#         for s, u in row_sizes:
#             tot[s] = (ctn_qty * u) if ctn_qty else None
#         tot["PER BLST"]     = None
#         tot["QTY PER CTN"]  = None
#         tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
#         tot["GROSS WEIGHT"] = total_gross
#         tot["NET WEIGHT"]   = total_net

#         groups.setdefault(color, []).append(data_row)
#         groups[color].append(tot)

#         if len(groups[color]) == 2:
#             groups[color + "__header"] = header_info

#     return groups


# # ===========================================================================
# # Detect edits
# # ===========================================================================
# def _persist_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
#     mask = df["CTN NO"].astype(str) != "TOTAL"
#     if not mask.any():
#         return False

#     changed = False
#     prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])

#     if sizes:
#         orig_sizes = df.loc[mask, sizes].fillna(-999)
#         new_sizes  = edited.loc[mask, sizes].fillna(-999)
#         if not orig_sizes.equals(new_sizes):
#             new_units = {}
#             for _, row in edited.loc[mask].iterrows():
#                 for s in sizes:
#                     v = row[s]
#                     if pd.notna(v):
#                         new_units[s] = int(v)
#             st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
#             changed = True

#     orig_ctn = _int_or_none(df.loc[mask, "CTN QTY"].iloc[0])
#     new_ctn  = _int_or_none(edited.loc[mask, "CTN QTY"].iloc[0])
#     if new_ctn is not None and new_ctn != orig_ctn:
#         st.session_state.ctn_edits.setdefault(color, {})[prepack] = new_ctn
#         changed = True

#     return changed


# # ===========================================================================
# # EXCEL EXPORT — mirrors 'Style - 905518 PO - 61480360 ... Multi Y OK.xlsx'
# # ===========================================================================
# def export_excel_template(
#     all_frames: list,
#     header_map: dict,
#     groups: dict,
#     weights_df: pd.DataFrame,
#     ctn_meas: list,
#     buyer: str, style: str, po_no: str,
#     grand_total_ctn: int,
# ) -> bytes:
#     """
#     Build an Excel workbook with two sheets:
#       - 'PKL' : full packing list (company header + weights + per-color blocks + summary)
#       - 'sum' : packing list summary
#     Uses formulas, merges, borders, fonts to match the reference template.
#     """
#     from openpyxl import Workbook
#     from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
#     from openpyxl.utils import get_column_letter

#     wb = Workbook()

#     # ================================================================
#     # Styles
#     # ================================================================
#     thin = Side(style="thin", color="000000")
#     med  = Side(style="medium", color="000000")
#     border_all   = Border(left=thin, right=thin, top=thin, bottom=thin)
#     border_title = Border(left=med, right=med, top=med, bottom=med)

#     font_title   = Font(name="Calibri", size=14, bold=True)
#     font_section = Font(name="Calibri", size=12, bold=True)
#     font_bold    = Font(name="Calibri", size=11, bold=True)
#     font_normal  = Font(name="Calibri", size=11)
#     font_small   = Font(name="Calibri", size=10)

#     align_center = Alignment(horizontal="center", vertical="center")
#     align_left   = Alignment(horizontal="left",   vertical="center")
#     align_right  = Alignment(horizontal="right",  vertical="center")

#     fill_header = PatternFill("solid", fgColor="D9E1F2")
#     fill_total  = PatternFill("solid", fgColor="FFF2CC")

#     # ================================================================
#     # SHEET 1: PKL
#     # ================================================================
#     ws = wb.active
#     ws.title = "PKL"

#     # ---- Column widths ----
#     widths = {
#         "A": 8,  "B": 6,  "C": 10, "D": 10, "E": 20, "F": 16,
#         "G": 6,  "H": 6,  "I": 6,  "J": 6,  "K": 6,  "L": 6,  "M": 6,
#         "N": 10, "O": 4,  "P": 12, "Q": 12, "R": 14, "S": 12,
#     }
#     for col, w in widths.items():
#         ws.column_dimensions[col].width = w

#     # ---- Row 1-2: Company header ----
#     ws.merge_cells("A1:S1")
#     ws["A1"] = "CREATIVE COLLECTIONS LTD-1A."
#     ws["A1"].font = font_title
#     ws["A1"].alignment = align_left

#     ws.merge_cells("A2:S2")
#     ws["A2"] = "Nishat Nagar , Tongi , Gazipur ."
#     ws["A2"].font = font_normal
#     ws["A2"].alignment = align_left

#     # ---- Row 4-6: Weight reference ----
#     ws["D4"] = "SIZE";         ws["D4"].font = font_bold
#     ws["F4"] = "SIZE";         ws["F4"].font = font_bold
#     for i, s in enumerate(SIZE_ORDER):
#         cell = ws.cell(row=4, column=7 + i, value=s)
#         cell.font = font_bold; cell.alignment = align_center

#     ws["D5"] = "N.W";          ws["D5"].font = font_bold
#     ws["F5"] = "N.WT";         ws["F5"].font = font_bold
#     for i, s in enumerate(SIZE_ORDER):
#         v = float(weights_df.loc[s, "N.W."])
#         cell = ws.cell(row=5, column=7 + i, value=v)
#         cell.number_format = "0.00"; cell.alignment = align_center

#     ws["D6"] = "N.N.W";        ws["D6"].font = font_bold
#     ws["F6"] = "N.N. WT";      ws["F6"].font = font_bold
#     for i, s in enumerate(SIZE_ORDER):
#         v = float(weights_df.loc[s, "N.N.W."])
#         col = get_column_letter(7 + i)
#         cell = ws.cell(row=6, column=7 + i, value=f"=+{col}5-0.02")
#         cell.number_format = "0.00"; cell.alignment = align_center

#     ws["D7"] = "EMPTY CTN WET"; ws["D7"].font = font_bold

#     # ---- Section renderer ----
#     current_row = [9]  # mutable container for current row index

#     def write_section(color_name, rows, hdr, ctn_start, ctn_total_global):
#         r = current_row[0]

#         # Section title (MULTY PACK Y)
#         ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=19)
#         c = ws.cell(row=r, column=1, value="MULTY PACK ( Y )")
#         c.font = font_section; c.alignment = align_center
#         r += 1

#         # PO header — compact 3-row grid
#         # Row A: BUYER | STYLE | P.O. # | OIQTY
#         ws.cell(row=r, column=1, value="BUYER").font = font_bold
#         ws.cell(row=r, column=2, value=":").alignment = align_center
#         ws.cell(row=r, column=3, value=buyer).font = font_normal
#         ws.cell(row=r, column=5, value="STYLE").font = font_bold
#         ws.cell(row=r, column=6, value=":").alignment = align_center
#         ws.cell(row=r, column=7, value=hdr.get("style_full", style)).font = font_normal
#         ws.cell(row=r, column=10, value="P.O. #").font = font_bold
#         ws.cell(row=r, column=11, value=":").alignment = align_center
#         ws.cell(row=r, column=12, value=po_no).font = font_normal
#         ws.cell(row=r, column=15, value="OIQTY").font = font_bold
#         ws.cell(row=r, column=16, value=":").alignment = align_center
#         ws.cell(row=r, column=17, value=hdr["oiqty"]).font = font_normal
#         ws.cell(row=r, column=18, value="PCS").font = font_small
#         r += 1

#         # Row B: SHIP QTY | EX/SHORT | CTN QTY | CARTON
#         ws.cell(row=r, column=1, value="SHIP QTY").font = font_bold
#         ws.cell(row=r, column=2, value=":").alignment = align_center
#         ws.cell(row=r, column=3, value=hdr["ship_qty"]).font = font_normal
#         ws.cell(row=r, column=4, value="PCS").font = font_small
#         ws.cell(row=r, column=5, value="EX/SHORT").font = font_bold
#         ws.cell(row=r, column=6, value=":").alignment = align_center
#         ws.cell(row=r, column=7, value=hdr["ex_short"]).font = font_normal
#         ws.cell(row=r, column=8, value="PCS").font = font_small
#         ws.cell(row=r, column=10, value="CTN QTY").font = font_bold
#         ws.cell(row=r, column=11, value=":").alignment = align_center
#         ws.cell(row=r, column=12, value=hdr["ctn_qty"]).font = font_normal
#         ws.cell(row=r, column=13, value="CTNS").font = font_small
#         ws.cell(row=r, column=15, value="CARTON").font = font_bold
#         ws.cell(row=r, column=16, value=":").alignment = align_center
#         ws.cell(row=r, column=17, value=f"{ctn_start:02d} of {ctn_total_global:03d}").font = font_normal
#         r += 1

#         # Row C: PO # | SKU/Item | Unit/Prepack
#         ws.cell(row=r, column=1, value="PO #").font = font_bold
#         ws.cell(row=r, column=2, value=":").alignment = align_center
#         ws.cell(row=r, column=3, value=po_no).font = font_normal
#         ws.cell(row=r, column=5, value="SKU / Item").font = font_bold
#         ws.cell(row=r, column=6, value=":").alignment = align_center
#         ws.cell(row=r, column=7, value=hdr.get("style_full", style)).font = font_normal
#         ws.cell(row=r, column=10, value="Unit / Prepack").font = font_bold
#         ws.cell(row=r, column=11, value=":").alignment = align_center
#         ws.cell(row=r, column=12, value=f"{hdr['total_units_per_carton']}/{hdr['ctn_qty']}").font = font_normal
#         r += 1

#         # CTN MEAS lines
#         for m in ctn_meas:
#             ws.cell(row=r, column=1, value="CTN MEAS.").font = font_bold
#             ws.cell(row=r, column=2, value=":").alignment = align_center
#             ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=19)
#             ws.cell(row=r, column=3, value=m).font = font_normal
#             r += 1

#         # ---- Main packing table ----
#         sizes = present_sizes(rows)
#         # Header row 1
#         left_hdr = ["CTN", "", "CTN", "CTN QTY", "COLOR", "PREPACK STECKER"]
#         for i, h in enumerate(left_hdr):
#             ws.cell(row=r, column=1 + i, value=h).font = font_bold
#             ws.cell(row=r, column=1 + i).alignment = align_center
#             ws.cell(row=r, column=1 + i).fill = fill_header
#             ws.cell(row=r, column=1 + i).border = border_all
#         # SIZE merged across size columns
#         if sizes:
#             c_start = 7
#             c_end = 7 + len(sizes) - 1
#             ws.merge_cells(start_row=r, start_column=c_start, end_row=r, end_column=c_end)
#             cc = ws.cell(row=r, column=c_start, value="SIZE")
#             cc.font = font_bold; cc.alignment = align_center; cc.fill = fill_header
#             for cc_i in range(c_start, c_end + 1):
#                 ws.cell(row=r, column=cc_i).border = border_all
#         # Right headers
#         right_hdr = ["PER BLST", "", "", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]
#         for i, h in enumerate(right_hdr):
#             c_idx = 7 + len(sizes) + i
#             ws.cell(row=r, column=c_idx, value=h).font = font_bold
#             ws.cell(row=r, column=c_idx).alignment = align_center
#             ws.cell(row=r, column=c_idx).fill = fill_header
#             ws.cell(row=r, column=c_idx).border = border_all
#         r += 1

#         # Header row 2 (size labels)
#         ws.cell(row=r, column=1, value="NO").font = font_bold
#         ws.cell(row=r, column=3, value="MES:").font = font_bold
#         for i, s in enumerate(sizes):
#             cc = ws.cell(row=r, column=7 + i, value=s)
#             cc.font = font_bold; cc.alignment = align_center; cc.fill = fill_header
#             cc.border = border_all
#         for i in range(6):
#             ws.cell(row=r, column=1 + i).border = border_all
#             ws.cell(row=r, column=1 + i).fill = fill_header
#         for i in range(len(right_hdr)):
#             c_idx = 7 + len(sizes) + i
#             ws.cell(row=r, column=c_idx).border = border_all
#             ws.cell(row=r, column=c_idx).fill = fill_header
#         r += 1

#         # Data rows
#         data_row_obj = rows[0] if rows else {}
#         total_row_obj = rows[-1] if len(rows) > 1 else {}

#         # Row values
#         ctn_no = data_row_obj.get("CTN NO", 1)
#         ctn_qty_val = data_row_obj.get("CTN QTY", 0)
#         color_val = data_row_obj.get("COLOR", "")
#         prepack_val = data_row_obj.get("PREPACK STECKER", "")
#         size_units = [data_row_obj.get(s, "") for s in sizes]

#         ws.cell(row=r, column=1, value=ctn_no).alignment = align_center
#         ws.cell(row=r, column=3, value=FIXED_CTN_MES).alignment = align_center
#         ws.cell(row=r, column=4, value=ctn_qty_val).alignment = align_center
#         ws.cell(row=r, column=5, value=color_val).alignment = align_center
#         ws.cell(row=r, column=6, value=prepack_val).alignment = align_center

#         for i, u in enumerate(size_units):
#             cc = ws.cell(row=r, column=7 + i, value=u)
#             cc.alignment = align_center

#         # PER BLST / QTY PER CTN / TOTAL QTY / GROSS / NET
#         size_range_start = get_column_letter(7)
#         size_range_end = get_column_letter(7 + len(sizes) - 1)
#         sum_range = f"{size_range_start}{r}:{size_range_end}{r}"

#         base_col = 7 + len(sizes)
#         ws.cell(row=r, column=base_col + 0, value=f"=SUM({sum_range})").alignment = align_center
#         ws.cell(row=r, column=base_col + 1, value="X").alignment = align_center
#         ws.cell(row=r, column=base_col + 2, value=1).alignment = align_center
#         ws.cell(row=r, column=base_col + 3, value=f"=+{get_column_letter(base_col+3)}{r}*{get_column_letter(base_col+0)}{r}").alignment = align_center
#         # QTY PER CTN references SUM of sizes
#         ws.cell(row=r, column=base_col + 3, value=f"={get_column_letter(base_col+0)}{r}")
#         ws.cell(row=r, column=base_col + 4, value=f"={get_column_letter(base_col+3)}{r}*{get_column_letter(4)}{r}").alignment = align_center
#         ws.cell(row=r, column=base_col + 5, value=f"={get_column_letter(base_col+3)}{r}*{get_column_letter(4)}{r}").alignment = align_center
#         ws.cell(row=r, column=base_col + 5).number_format = "0.00"
#         ws.cell(row=r, column=base_col + 6, value=f"={get_column_letter(base_col+5)}{r}-0.42").alignment = align_center
#         ws.cell(row=r, column=base_col + 6).number_format = "0.00"

#         for c_idx in range(1, base_col + 7):
#             ws.cell(row=r, column=c_idx).border = border_all
#         r += 1

#         # TOTAL row
#         ws.cell(row=r, column=1, value="TOTAL").font = font_bold
#         ws.cell(row=r, column=1).alignment = align_center
#         ws.cell(row=r, column=1).fill = fill_total
#         ws.cell(row=r, column=4, value=f"=SUM(D{r-1}:D{r-1})").alignment = align_center
#         ws.cell(row=r, column=4).fill = fill_total
#         ws.cell(row=r, column=5, value="CTNS").alignment = align_center
#         ws.cell(row=r, column=5).fill = fill_total
#         for i, s in enumerate(sizes):
#             col_letter = get_column_letter(7 + i)
#             ws.cell(row=r, column=7 + i, value=f"={col_letter}{r-1}*$D${r}").alignment = align_center
#             ws.cell(row=r, column=7 + i).fill = fill_total
#         # QTY total
#         ws.cell(row=r, column=base_col + 4, value=f"=SUM({get_column_letter(base_col+4)}{r-1}:{get_column_letter(base_col+4)}{r-1})").alignment = align_center
#         ws.cell(row=r, column=base_col + 4).fill = fill_total
#         ws.cell(row=r, column=base_col + 5, value="PCS").alignment = align_center
#         ws.cell(row=r, column=base_col + 5).fill = fill_total

#         for c_idx in range(1, base_col + 7):
#             ws.cell(row=r, column=c_idx).border = border_all
#         r += 2  # blank row between sections

#         current_row[0] = r
#         return r

#     # ---- Iterate color groups ----
#     ctn_cursor = 1
#     for color, rows in groups.items():
#         hdr = header_map.get(color, {})
#         style_code = hdr.get("color_code", "000")
#         hdr["style_full"] = f"{DEFAULT_STYLE.rsplit('-', 2)[0]}-{style_code}-1"

#         write_section(color, rows, hdr, ctn_cursor, grand_total_ctn)
#         ctn_cursor += int(hdr.get("ctn_qty", 0))

#     # ================================================================
#     # SHEET 2: sum
#     # ================================================================
#     ws2 = wb.create_sheet("sum")
#     ws2.column_dimensions["A"].width = 14
#     ws2.column_dimensions["B"].width = 14
#     ws2.column_dimensions["C"].width = 12
#     ws2.column_dimensions["D"].width = 20
#     ws2.column_dimensions["E"].width = 12
#     ws2.column_dimensions["F"].width = 12
#     ws2.column_dimensions["G"].width = 10
#     ws2.column_dimensions["H"].width = 10
#     ws2.column_dimensions["I"].width = 10
#     ws2.column_dimensions["J"].width = 10

#     ws2.merge_cells("A3:J3")
#     ws2["A3"] = "CREATIVE COLLECTIONS LIMITED (UNIT-1A)"
#     ws2["A3"].font = font_title
#     ws2["A3"].alignment = align_left

#     ws2.merge_cells("A4:J4")
#     ws2["A4"] = "Nishatnagar,Tongi,Gazipur"
#     ws2["A4"].font = font_normal
#     ws2["A4"].alignment = align_left

#     ws2.merge_cells("A5:J5")
#     ws2["A5"] = "PACKING LIST SUMMARY"
#     ws2["A5"].font = font_section
#     ws2["A5"].alignment = align_center

#     ws2["A7"] = "BUYER"; ws2["A7"].font = font_bold
#     ws2["B7"] = buyer;   ws2["B7"].font = font_normal
#     ws2["H7"] = "DATE";  ws2["H7"].font = font_bold
#     ws2["I7"] = "01/02/2026"; ws2["I7"].font = font_normal

#     ws2["A8"] = "STYLE"; ws2["A8"].font = font_bold
#     ws2["B8"] = style;   ws2["B8"].font = font_normal

#     # Summary table header
#     hdrs = ["DC", "PO NO", "SEASON", "COLOR/CODE", "ORD/QTY", "SHIP/QTY",
#             "EXCES", "SHORT", "PER (%)", "CTNS"]
#     for i, h in enumerate(hdrs):
#         c = ws2.cell(row=10, column=1 + i, value=h)
#         c.font = font_bold; c.alignment = align_center; c.fill = fill_header
#         c.border = border_all

#     # Data rows: one per color group
#     r2 = 11
#     for color, rows in groups.items():
#         hdr = header_map.get(color, {})
#         ws2.cell(row=r2, column=1, value="BDC").alignment = align_center
#         ws2.cell(row=r2, column=2, value=po_no).alignment = align_center
#         ws2.cell(row=r2, column=3, value="Sum'26").alignment = align_center
#         ws2.cell(row=r2, column=4, value=color).alignment = align_center
#         ws2.cell(row=r2, column=5, value=hdr.get("oiqty", 0)).alignment = align_center
#         ws2.cell(row=r2, column=6, value=hdr.get("ship_qty", 0)).alignment = align_center
#         ws2.cell(row=r2, column=7, value=f"=F{r2}-E{r2}").alignment = align_center
#         ws2.cell(row=r2, column=8, value=hdr.get("ex_short", 0)).alignment = align_center
#         ws2.cell(row=r2, column=9, value=f"=G{r2}/E{r2}").alignment = align_center
#         ws2.cell(row=r2, column=10, value=hdr.get("ctn_qty", 0)).alignment = align_center
#         for c_idx in range(1, 11):
#             ws2.cell(row=r2, column=c_idx).border = border_all
#         r2 += 1

#     # TOTAL row
#     ws2.cell(row=r2, column=4, value="TOTAL").font = font_bold
#     ws2.cell(row=r2, column=4).alignment = align_center
#     ws2.cell(row=r2, column=5, value=f"=SUM(E11:E{r2-1})").alignment = align_center
#     ws2.cell(row=r2, column=6, value=f"=SUM(F11:F{r2-1})").alignment = align_center
#     ws2.cell(row=r2, column=7, value=f"=SUM(G11:G{r2-1})").alignment = align_center
#     ws2.cell(row=r2, column=8, value=f"=SUM(H11:H{r2-1})").alignment = align_center
#     ws2.cell(row=r2, column=9, value=f"=H{r2}/E{r2}").alignment = align_center
#     ws2.cell(row=r2, column=10, value=f"=SUM(J11:J{r2-1})").alignment = align_center
#     for c_idx in range(1, 11):
#         ws2.cell(row=r2, column=c_idx).fill = fill_total
#         ws2.cell(row=r2, column=c_idx).border = border_all

#     # ---- Save to bytes ----
#     buf = io.BytesIO()
#     wb.save(buf)
#     return buf.getvalue()


# # ===========================================================================
# # UI
# # ===========================================================================
# _init_state()

# with st.sidebar:
#     st.markdown("### ⚖️ Weight settings (kg)")
#     st.caption("Edit any cell — values recalculate instantly.")

#     edited_sidebar = st.data_editor(
#         st.session_state.weights_df,
#         use_container_width=True,
#         num_rows="fixed",
#         column_config={
#             "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
#             "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
#             "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
#         },
#         key="weights_editor_sidebar",
#     )
#     if not edited_sidebar.equals(st.session_state.weights_df):
#         st.session_state.weights_df = edited_sidebar
#         st.rerun()

#     if st.button("↺ Reset weights", use_container_width=True):
#         st.session_state.weights_df = _default_weights_df()
#         st.rerun()

#     st.divider()
#     st.markdown("### 📦 CTN MEAS. (carton dimensions)")
#     st.caption("One line per carton type — appears in the PO header block.")
#     for i, m in enumerate(st.session_state.ctn_meas):
#         new_m = st.text_input(f"Line {i+1}", value=m, key=f"ctn_meas_{i}")
#         if new_m != m:
#             st.session_state.ctn_meas[i] = new_m

#     st.divider()
#     st.markdown("### 📦 PER BLST")
#     blst_c = st.number_input(
#         "C  (multiplier, default 1)",
#         min_value=1, max_value=8, value=1, step=1,
#         help='PER BLST = "Σ units_per_size X C"',
#     )
#     st.caption(f'Formula: `PER BLST = "A X {blst_c}"`')

#     st.divider()
#     st.info(f"`CTN MES:` is fixed to **{FIXED_CTN_MES}**.")

#     if st.button("↺ Reset all cell edits", use_container_width=True):
#         st.session_state.size_edits = {}
#         st.session_state.ctn_edits  = {}
#         st.rerun()

#     st.divider()
#     json_path = st.text_input("JSON file path", DEFAULT_JSON)


# if not Path(json_path).exists():
#     st.error(f"File not found: `{json_path}`")
#     st.stop()

# weights = get_weights()
# data = load_json(json_path)
# groups = build_grouped(data, weights["NW"], weights["EMPTY"], blst_c)

# header_map = {k.replace("__header", ""): v for k, v in groups.items() if k.endswith("__header")}
# groups = {k: v for k, v in groups.items() if not k.endswith("__header")}

# if not groups:
#     st.warning("No Multi Pack (Y) tables found in the JSON.")
#     st.stop()

# po_header = data.get("PO_HEADER", {}) or {}
# buyer_fixed = po_header.get("BUYER") or DEFAULT_BUYER
# po_no_fixed = po_header.get("P.O._#") or DEFAULT_PO_NO

# grand_total_ctn = sum(
#     (header_map[c]["ctn_qty"] or 0) for c in groups if c in header_map
# ) or 1


# # ===========================================================================
# # Render
# # ===========================================================================
# all_frames: list = []
# color_index = 0

# for color, rows in groups.items():
#     color_index += 1
#     sizes = present_sizes(rows)
#     columns = LEFT_STATIC + sizes + RIGHT_STATIC
#     df = pd.DataFrame(rows).reindex(columns=columns)

#     hdr = header_map.get(color, {})
#     style_full = f"{DEFAULT_STYLE.rsplit('-', 2)[0]}-{hdr.get('color_code', '000')}-1"
#     sku_item   = style_full
#     unit_prepack = f"{hdr.get('total_units_per_carton', 0)}/{hdr.get('ctn_qty', 0)}"
#     carton_label = f"{color_index:02d} of {grand_total_ctn:03d}"

#     render_po_header(
#         buyer=buyer_fixed,
#         style=style_full,
#         po_no=po_no_fixed,
#         oiqty=hdr.get("oiqty", 0),
#         ship_qty=hdr.get("ship_qty", 0),
#         ex_short=hdr.get("ex_short", 0),
#         ctn_qty=hdr.get("ctn_qty", 0),
#         ctn_meas_list=st.session_state.ctn_meas,
#         sku_item=sku_item,
#         unit_prepack=unit_prepack,
#         carton_label=carton_label,
#     )

#     st.markdown(f"#### 🎨 {color}")
#     st.caption(
#         f"{sum(1 for r in rows if r.get('CTN NO') != 'TOTAL')} group(s) · "
#         "edit size cells or CTN QTY → totals update automatically"
#     )

#     render_size_weight_header(sizes, key_suffix=color)

#     col_cfg = {
#         "CTN NO":          st.column_config.TextColumn("CTN NO",  width="small", disabled=True),
#         "CTN MES:":        st.column_config.TextColumn("CTN MES:", width="small", disabled=True),
#         "CTN QTY":         st.column_config.NumberColumn(
#             "CTN QTY", width="small", min_value=1, step=1, format="%d",
#             help="Editable. Number of cartons.",
#         ),
#         "COLOR":           st.column_config.TextColumn("COLOR",           width="medium", disabled=True),
#         "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium", disabled=True),
#         "PER BLST":        st.column_config.TextColumn("PER BLST",   width="small", disabled=True),
#         "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small", disabled=True),
#         "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY",  width="small", disabled=True),
#         "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f", disabled=True),
#         "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT",   width="small", format="%.2f", disabled=True),
#     }
#     for s in sizes:
#         col_cfg[s] = st.column_config.NumberColumn(s, width="small", min_value=0, step=1)

#     try:
#         edited = st.data_editor(
#             data=df, use_container_width=True, hide_index=True,
#             num_rows="fixed", column_config=col_cfg,
#             key=f"multi_editor_{color}",
#         )
#     except TypeError:
#         st.warning("Upgrade Streamlit: pip install -U streamlit")
#         st.dataframe(df, use_container_width=True, hide_index=True)
#         edited = df

#     if _persist_edits(color, df, edited, sizes):
#         st.rerun()

#     all_frames.append((color, edited))
#     st.divider()


# # ===========================================================================
# # Downloads
# # ===========================================================================
# st.markdown("### Download")

# col1, col2 = st.columns(2)
# with col1:
#     export_rows: list = []
#     for i, (_, frame) in enumerate(all_frames):
#         if i > 0:
#             export_rows.append({})
#         export_rows.extend(frame.to_dict(orient="records"))
#     combined = pd.DataFrame(export_rows)
#     st.download_button(
#         "⬇ Download CSV (all colors)",
#         data=combined.to_csv(index=False).encode("utf-8"),
#         file_name="packing_list_multi.csv", mime="text/csv",
#         use_container_width=True,
#     )

# with col2:
#     try:
#         xlsx_bytes = export_excel_template(
#             all_frames=all_frames,
#             header_map=header_map,
#             groups=groups,
#             weights_df=st.session_state.weights_df,
#             ctn_meas=st.session_state.ctn_meas,
#             buyer=buyer_fixed,
#             style=DEFAULT_STYLE,
#             po_no=po_no_fixed,
#             grand_total_ctn=grand_total_ctn,
#         )
#         st.download_button(
#             "⬇ Download Excel (template format)",
#             data=xlsx_bytes,
#             file_name="packing_list_multi.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             use_container_width=True,
#         )
#     except Exception as e:
#         st.error(f"Excel export failed: {e}")


# # ===========================================================================
# # Sidebar info
# # ===========================================================================
# with st.sidebar:
#     st.markdown("### Colors detected")
#     for color, rows in groups.items():
#         n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
#         st.write(f"- **{color}** — {n} group(s)")





"""
multi_y_packing.py
------------------
Streamlit app: read parsed PO JSON → build Multi Pack (Y) packing list.

Design mirrors the reference image:
    - Centered title + address
    - Bordered weight reference table (SIZE / N.W / N.N.W / EMPTY CTN WET)
    - Section strip: MULTY PACK ( Y )
    - Left-side PO header (13 lines) + right-side block (4 lines)
    - Main table with merged SIZE header across size columns
    - Total row with borders

Excel export mirrors: Style - 905518 PO - 61480360 - Qty - 4598 Pcs Multi Y OK.xlsx
    Sheet 'PKL' : full packing list matching the design
    Sheet 'sum' : packing list summary

Run:
    streamlit run multi_y_packing.py
"""

import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ===========================================================================
# Config
# ===========================================================================
st.set_page_config(page_title="Packing List — Multi Pack (Y)", layout="wide")
st.title("📦 Packing List — Multi Pack (Y)")

DEFAULT_JSON = "61480360.json"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXL+"]

FIXED_CTN_MES = "G82"

DEFAULT_NW    = {"XS": 0.510, "S": 0.520, "M": 0.550, "L": 0.560, "XL": 0.610, "XXL": 0.650, "XXL+": 0.690}
DEFAULT_NNW   = {"XS": 0.490, "S": 0.500, "M": 0.530, "L": 0.540, "XL": 0.590, "XXL": 0.630, "XXL+": 0.670}
DEFAULT_EMPTY = {"XS": 0.490, "S": 1.000, "M": 1.000, "L": 1.000, "XL": 1.000, "XXL": 1.000, "XXL+": 1.000}

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

LEFT_STATIC  = ["CTN NO", "CTN MES:", "CTN QTY", "COLOR", "PREPACK STECKER"]
RIGHT_STATIC = ["PER BLST", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]


# ===========================================================================
# Session state
# ===========================================================================
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
    if "weights_df" not in st.session_state:
        st.session_state.weights_df = _default_weights_df()
    if "size_edits" not in st.session_state:
        st.session_state.size_edits = {}
    if "ctn_edits" not in st.session_state:
        st.session_state.ctn_edits = {}
    if "ctn_meas" not in st.session_state:
        st.session_state.ctn_meas = list(DEFAULT_CTN_MEAS)


def get_weights() -> dict:
    df = st.session_state.weights_df
    return {
        "NW":    {s: float(df.loc[s, "N.W."])          for s in df.index},
        "NNW":   {s: float(df.loc[s, "N.N.W."])        for s in df.index},
        "EMPTY": {s: float(df.loc[s, "EMPTY CTN WT."]) for s in df.index},
    }


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


def present_sizes(rows: list) -> list:
    return [s for s in SIZE_ORDER if any(s in r for r in rows)]


def _empty_ctn_weight_for(sizes: list, empty_weights: dict) -> float:
    ws = [empty_weights.get(s) for s in sizes if s in empty_weights]
    return max(ws) if ws else 0.0


def _int_or_none(v):
    if v is None:
        return None
    try:
        return int(float(str(v).strip().split()[0]))
    except (TypeError, ValueError, IndexError):
        return None


def render_size_weight_header(sizes: list, key_suffix: str = "") -> None:
    master = st.session_state.weights_df
    view = master.loc[sizes].T.copy()
    view.index.name = "SIZE"

    edited = st.data_editor(
        view,
        use_container_width=False,
        num_rows="fixed",
        column_config={
            s: st.column_config.NumberColumn(s, format="%.3f", step=0.001, width="small")
            for s in view.columns
        },
        key=f"header_editor_{key_suffix}",
    )
    if not edited.equals(view):
        for s in edited.columns:
            st.session_state.weights_df.loc[s, "N.W."]          = float(edited.loc["N.W.", s])
            st.session_state.weights_df.loc[s, "N.N.W."]        = float(edited.loc["N.N.W.", s])
            st.session_state.weights_df.loc[s, "EMPTY CTN WT."] = float(edited.loc["EMPTY CTN WT.", s])
        st.rerun()


# ===========================================================================
# TOP BLOCK: Company title + address + weight reference table
# ===========================================================================
def render_company_header(weights_df: pd.DataFrame) -> None:
    sizes = list(weights_df.index)
    nw_vals    = [f"{float(weights_df.loc[s,'N.W.']):.3f}"    for s in sizes]
    nnw_vals   = [f"{float(weights_df.loc[s,'N.N.W.']):.3f}"  for s in sizes]

    size_cells = "".join(f"<th>{s}</th>" for s in sizes)
    nw_cells   = "".join(f"<td>{v}</td>" for v in nw_vals)
    nnw_cells  = "".join(f"<td>{v}</td>" for v in nnw_vals)

    html = f"""
    <style>
      .cc-title {{
        text-align: center;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        font-size: 20px;
        text-decoration: underline;
        margin-bottom: 2px;
      }}
      .cc-addr {{
        text-align: center;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        font-size: 15px;
        margin-bottom: 12px;
      }}
      .cc-weight-wrap {{
        display: flex;
        justify-content: center;
        margin-bottom: 14px;
      }}
      .cc-weight {{
        border-collapse: collapse;
        font-family: 'Courier New', monospace;
        font-size: 13px;
      }}
      .cc-weight th, .cc-weight td {{
        border: 1px solid #000;
        padding: 2px 10px;
        text-align: center;
        min-width: 48px;
      }}
      .cc-weight th.label {{
        text-align: left;
        background: #fff;
        font-weight: bold;
        min-width: 90px;
      }}
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
# SECTION STRIP:  MULTY PACK ( Y )
# ===========================================================================
def render_section_strip(title: str) -> None:
    html = f"""
    <style>
      .cc-strip {{
        text-align: center;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        font-size: 16px;
        letter-spacing: 2px;
        border-top: 2px solid #000;
        border-bottom: 2px solid #000;
        padding: 4px 0;
        margin: 16px 0 10px 0;
      }}
    </style>
    <div class="cc-strip">{title}</div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ===========================================================================
# PO HEADER: left block (13 lines) + right block (4 lines)
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
        display: grid;
        grid-template-columns: 1.4fr 1fr;
        gap: 20px;
        font-family: 'Courier New', monospace;
        font-size: 13.5px;
        line-height: 1.5;
        margin-bottom: 10px;
      }}
      .po-line {{ display: flex; align-items: baseline; }}
      .po-label {{ display: inline-block; width: 110px; font-weight: bold; }}
      .po-colon {{ width: 14px; display: inline-block; text-align: center; }}
      .po-value {{ display: inline-block; }}
      .po-right {{ margin-top: 60px; }}
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
# Build packing list
# ===========================================================================
def build_grouped(data: dict, nw: dict, empty_weights: dict, blst_c: int) -> dict:
    groups: dict = {}
    ctn_counter: dict = {}

    for _, table in data["tables"].items():
        trows = table.get("rows") or []
        total = table.get("total") or {}
        if not trows:
            continue

        first = trows[0]
        if first.get("PrePack Type") != "Multi" or first.get("Full Carton") != "Y":
            continue

        color   = color_display(first.get("Universal CC #Color Desc", "")) or "UNKNOWN"
        prepack = str(first.get("PrePack"))
        ctn_counter[color] = ctn_counter.get(color, 0) + 1
        row_no = ctn_counter[color]

        size_edits = st.session_state.size_edits.get(color, {}).get(prepack, {})
        ctn_edit   = st.session_state.ctn_edits.get(color, {}).get(prepack)

        row_sizes = []
        for r in trows:
            size  = r["Size Desc"]
            units = int(size_edits.get(size, r.get("Units per PrePack") or 0))
            row_sizes.append((size, units))

        sizes_present = [s for s, _ in row_sizes]

        json_ctn_mes = _int_or_none(total.get("#PrePackets Ordered")) or 0
        ctn_qty = int(ctn_edit) if ctn_edit is not None else int(json_ctn_mes)

        A           = sum(u for _, u in row_sizes)
        qty_per_ctn = A
        per_blst    = f"{A} X {blst_c}"

        net_per_carton   = round(sum(u * nw.get(s, 0.0) for s, u in row_sizes), 2)
        empty_ctn_weight = _empty_ctn_weight_for(sizes_present, empty_weights)
        gross_per_carton = round(net_per_carton + empty_ctn_weight, 2)

        total_qty   = ctn_qty * qty_per_ctn
        total_net   = round(ctn_qty * net_per_carton,   2) if ctn_qty else None
        total_gross = round(ctn_qty * gross_per_carton, 2) if ctn_qty else None

        oiqty_total    = _int_or_none(total.get("ORDER QTY"))
        ship_qty_total = _int_or_none(total.get("SHIP QTY"))
        ex_short_total = _int_or_none(total.get("EX-SHORT"))

        if oiqty_total is None:
            oiqty_total = sum(_int_or_none(r.get("ORDER QTY")) or 0 for r in trows)
        if ship_qty_total is None:
            ship_qty_total = sum(_int_or_none(r.get("SHIP QTY")) or 0 for r in trows)
        if ex_short_total is None:
            ex_short_total = max(oiqty_total - ship_qty_total, 0)

        header_info = {
            "color": color,
            "color_code": color_code(first.get("Universal CC #Color Desc", "")),
            "prepack": prepack,
            "oiqty": oiqty_total,
            "ship_qty": ship_qty_total,
            "ex_short": ex_short_total,
            "ctn_qty": ctn_qty,
            "total_units_per_carton": qty_per_ctn,
        }

        data_row = {
            "CTN NO": row_no, "CTN MES:": FIXED_CTN_MES,
            "CTN QTY": ctn_qty, "COLOR": color,
            "PREPACK STECKER": prepack,
        }
        for s, u in row_sizes:
            data_row[s] = u
        data_row["PER BLST"]     = per_blst
        data_row["QTY PER CTN"]  = qty_per_ctn
        data_row["TOTAL QTY"]    = total_qty
        data_row["GROSS WEIGHT"] = gross_per_carton
        data_row["NET WEIGHT"]   = net_per_carton

        tot = {
            "CTN NO": "TOTAL", "CTN MES:": None,
            "CTN QTY": f"{ctn_qty} CTNS" if ctn_qty else None,
            "COLOR": None, "PREPACK STECKER": None,
        }
        for s, u in row_sizes:
            tot[s] = (ctn_qty * u) if ctn_qty else None
        tot["PER BLST"]     = None
        tot["QTY PER CTN"]  = None
        tot["TOTAL QTY"]    = f"{total_qty} PCS" if total_qty else None
        tot["GROSS WEIGHT"] = total_gross
        tot["NET WEIGHT"]   = total_net

        groups.setdefault(color, []).append(data_row)
        groups[color].append(tot)

        if len(groups[color]) == 2:
            groups[color + "__header"] = header_info

    return groups


# ===========================================================================
# Detect edits
# ===========================================================================
def _persist_edits(color: str, df: pd.DataFrame, edited: pd.DataFrame, sizes: list) -> bool:
    mask = df["CTN NO"].astype(str) != "TOTAL"
    if not mask.any():
        return False

    changed = False
    prepack = str(df.loc[mask, "PREPACK STECKER"].iloc[0])

    if sizes:
        orig_sizes = df.loc[mask, sizes].fillna(-999)
        new_sizes  = edited.loc[mask, sizes].fillna(-999)
        if not orig_sizes.equals(new_sizes):
            new_units = {}
            for _, row in edited.loc[mask].iterrows():
                for s in sizes:
                    v = row[s]
                    if pd.notna(v):
                        new_units[s] = int(v)
            st.session_state.size_edits.setdefault(color, {})[prepack] = new_units
            changed = True

    orig_ctn = _int_or_none(df.loc[mask, "CTN QTY"].iloc[0])
    new_ctn  = _int_or_none(edited.loc[mask, "CTN QTY"].iloc[0])
    if new_ctn is not None and new_ctn != orig_ctn:
        st.session_state.ctn_edits.setdefault(color, {})[prepack] = new_ctn
        changed = True

    return changed


# ===========================================================================
# EXCEL EXPORT — mirrors reference template
# ===========================================================================
def export_excel_template(
    all_frames: list,
    header_map: dict,
    groups: dict,
    weights_df: pd.DataFrame,
    ctn_meas: list,
    buyer: str, style: str, po_no: str,
    grand_total_ctn: int,
) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()

    thin = Side(style="thin", color="000000")
    med  = Side(style="medium", color="000000")
    border_all   = Border(left=thin, right=thin, top=thin, bottom=thin)
    border_title = Border(left=med, right=med, top=med, bottom=med)

    font_title   = Font(name="Courier New", size=18, bold=True, underline="single")
    font_addr    = Font(name="Courier New", size=13, bold=True)
    font_section = Font(name="Courier New", size=13, bold=True)
    font_bold    = Font(name="Courier New", size=11, bold=True)
    font_normal  = Font(name="Courier New", size=11)
    font_small   = Font(name="Courier New", size=10)

    align_center = Alignment(horizontal="center", vertical="center")
    align_left   = Alignment(horizontal="left",   vertical="center")

    fill_header = PatternFill("solid", fgColor="D9D9D9")
    fill_total  = PatternFill("solid", fgColor="F2F2F2")

    ws = wb.active
    ws.title = "PKL"

    # Column widths
    widths = {
        "A": 8,  "B": 6,  "C": 10, "D": 10, "E": 20, "F": 16,
        "G": 7,  "H": 7,  "I": 7,  "J": 7,  "K": 7,  "L": 7,  "M": 8,
        "N": 12, "O": 5,  "P": 12, "Q": 12, "R": 14, "S": 12,
    }
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    # Row 1-2: Title + Address
    ws.merge_cells("A1:S1")
    ws["A1"] = "CREATIVE COLLECTIONS LTD-1A."
    ws["A1"].font = font_title
    ws["A1"].alignment = align_center

    ws.merge_cells("A2:S2")
    ws["A2"] = "Nishat Nagar , Tongi , Gazipur ."
    ws["A2"].font = font_addr
    ws["A2"].alignment = align_center

    # Row 4-7: Weight reference table
    ws["D4"] = "SIZE";  ws["D4"].font = font_bold;  ws["D4"].border = border_all
    ws["F4"] = "SIZE";  ws["F4"].font = font_bold;  ws["F4"].border = border_all
    for i, s in enumerate(SIZE_ORDER):
        c = ws.cell(row=4, column=7 + i, value=s)
        c.font = font_bold; c.alignment = align_center; c.border = border_all

    ws["D5"] = "N.W";   ws["D5"].font = font_bold;  ws["D5"].border = border_all
    ws["F5"] = "N.WT";  ws["F5"].font = font_bold;  ws["F5"].border = border_all
    for i, s in enumerate(SIZE_ORDER):
        c = ws.cell(row=5, column=7 + i, value=float(weights_df.loc[s, "N.W."]))
        c.number_format = "0.000"; c.alignment = align_center; c.border = border_all

    ws["D6"] = "N.N.W"; ws["D6"].font = font_bold;  ws["D6"].border = border_all
    ws["F6"] = "N.N.WT";ws["F6"].font = font_bold;  ws["F6"].border = border_all
    for i, s in enumerate(SIZE_ORDER):
        c = ws.cell(row=6, column=7 + i, value=float(weights_df.loc[s, "N.N.W."]))
        c.number_format = "0.000"; c.alignment = align_center; c.border = border_all

    ws["D7"] = "EMPTY CTN WET"; ws["D7"].font = font_bold; ws["D7"].border = border_all
    ws["F7"] = ""; ws["F7"].border = border_all
    for i in range(len(SIZE_ORDER)):
        ws.cell(row=7, column=7 + i).border = border_all

    r = 9

    # ---- Sections ----
    for color, rows in groups.items():
        hdr = header_map.get(color, {})
        style_code = hdr.get("color_code", "000")
        style_full = f"{DEFAULT_STYLE.rsplit('-', 2)[0]}-{style_code}-1"

        # Section strip
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=19)
        c = ws.cell(row=r, column=1, value="MULTY PACK ( Y )")
        c.font = font_section; c.alignment = align_center
        c.border = Border(top=med, bottom=med)
        r += 1

        # ---- PO Header (left block) ----
        po_left = [
            ("BUYER",      buyer),
            ("STYLE",      style_full),
            ("P. O. #",    po_no),
            ("O/QTY",      f"{hdr.get('oiqty', 0)} PCS"),
            ("SHIP QTY",   f"{hdr.get('ship_qty', 0)} PCS"),
            ("EX/SHORT",   f"{hdr.get('ex_short', 0)} PCS"),
            ("CTN QTY",    f"{hdr.get('ctn_qty', 0)} CTNS"),
        ]
        for label, value in po_left:
            ws.cell(row=r, column=1, value=label).font = font_bold
            ws.cell(row=r, column=2, value=":").alignment = align_center
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=8)
            ws.cell(row=r, column=3, value=value).font = font_normal
            r += 1

        # CTN MEAS lines
        for m in ctn_meas:
            ws.cell(row=r, column=1, value="CTN MEAS.").font = font_bold
            ws.cell(row=r, column=2, value=":").alignment = align_center
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=8)
            ws.cell(row=r, column=3, value=m).font = font_normal
            r += 1

        # Right block — starts at same row as BUYER line
        right_start = r - len(po_left) - len(ctn_meas)
        po_right = [
            ("PO #",           po_no),
            ("SKU / Item",     style_full),
            ("Unit / Prepack", f"{hdr.get('total_units_per_carton', 0)}/{hdr.get('ctn_qty', 0)}"),
            ("CARTON",         f"{list(groups.keys()).index(color)+1:02d} of {grand_total_ctn:03d}"),
        ]
        rr = right_start + 6
        for label, value in po_right:
            ws.cell(row=rr, column=12, value=label).font = font_bold
            ws.cell(row=rr, column=13, value=":").alignment = align_center
            ws.merge_cells(start_row=rr, start_column=14, end_row=rr, end_column=17)
            ws.cell(row=rr, column=14, value=value).font = font_normal
            rr += 1

        r += 0

        # ---- Main table ----
        sizes = present_sizes(rows)
        size_cols = len(sizes)
        base_right = 7 + size_cols

        # Header row 1
        left_hdr = ["CTN", "", "CTN", "CTN QTY", "COLOR", "PREPACK STECKER"]
        for i, h in enumerate(left_hdr):
            c = ws.cell(row=r, column=1 + i, value=h)
            c.font = font_bold; c.alignment = align_center
            c.border = border_all; c.fill = fill_header

        ws.merge_cells(start_row=r, start_column=7, end_row=r, end_column=7 + size_cols - 1)
        c = ws.cell(row=r, column=7, value="SIZE")
        c.font = font_bold; c.alignment = align_center
        c.border = border_all; c.fill = fill_header
        for i in range(1, size_cols):
            ws.cell(row=r, column=7 + i).border = border_all
            ws.cell(row=r, column=7 + i).fill = fill_header

        right_hdr = ["PER BLST", "", "QTY PER CTN", "TOTAL QTY", "GROSS WEIGHT", "NET WEIGHT"]
        for i, h in enumerate(right_hdr):
            c = ws.cell(row=r, column=base_right + i, value=h)
            c.font = font_bold; c.alignment = align_center
            c.border = border_all; c.fill = fill_header
        r += 1

        # Header row 2 (size labels)
        ws.cell(row=r, column=1, value="NO").font = font_bold
        ws.cell(row=r, column=3, value="MES:").font = font_bold
        ws.cell(row=r, column=5, value="COLOR").font = font_bold
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

        # Data row
        data_row_obj = rows[0]
        ctn_no = data_row_obj.get("CTN NO", 1)
        ctn_qty_val = data_row_obj.get("CTN QTY", 0)
        color_val = data_row_obj.get("COLOR", "")
        prepack_val = data_row_obj.get("PREPACK STECKER", "")

        ws.cell(row=r, column=1, value=ctn_no).alignment = align_center
        ws.cell(row=r, column=3, value=FIXED_CTN_MES).alignment = align_center
        ws.cell(row=r, column=4, value=ctn_qty_val).alignment = align_center
        ws.cell(row=r, column=5, value=color_val).alignment = align_center
        ws.cell(row=r, column=6, value=prepack_val).alignment = align_center

        for i, s in enumerate(sizes):
            cc = ws.cell(row=r, column=7 + i, value=data_row_obj.get(s, ""))
            cc.alignment = align_center

        sum_range = f"{get_column_letter(7)}{r}:{get_column_letter(7+size_cols-1)}{r}"
        ws.cell(row=r, column=base_right + 0, value=f"=SUM({sum_range})").alignment = align_center
        ws.cell(row=r, column=base_right + 1, value="X").alignment = align_center
        ws.cell(row=r, column=base_right + 2, value=1).alignment = align_center
        ws.cell(row=r, column=base_right + 3, value=f"={get_column_letter(base_right+0)}{r}").alignment = align_center
        ws.cell(row=r, column=base_right + 4, value=f"={get_column_letter(base_right+3)}{r}*{get_column_letter(4)}{r}").alignment = align_center
        ws.cell(row=r, column=base_right + 5, value=f"={get_column_letter(base_right+3)}{r}*{get_column_letter(4)}{r}").alignment = align_center
        ws.cell(row=r, column=base_right + 5).number_format = "0.00"

        for c_idx in range(1, base_right + 6):
            ws.cell(row=r, column=c_idx).border = border_all
        r += 1

        # TOTAL row
        ws.cell(row=r, column=1, value="TOTAL").font = font_bold
        ws.cell(row=r, column=1).alignment = align_center
        ws.cell(row=r, column=1).fill = fill_total
        ws.cell(row=r, column=4, value=f"=SUM(D{r-1}:D{r-1})").alignment = align_center
        ws.cell(row=r, column=4).fill = fill_total
        ws.cell(row=r, column=5, value="CTNS").alignment = align_center
        ws.cell(row=r, column=5).fill = fill_total
        for i, s in enumerate(sizes):
            c = ws.cell(row=r, column=7 + i, value=f"={get_column_letter(7+i)}{r-1}*$D${r}")
            c.alignment = align_center; c.fill = fill_total
        ws.cell(row=r, column=base_right + 3, value=f"=SUM({get_column_letter(base_right+3)}{r-1}:{get_column_letter(base_right+3)}{r-1})").alignment = align_center
        ws.cell(row=r, column=base_right + 3).fill = fill_total
        ws.cell(row=r, column=base_right + 4, value="PCS").alignment = align_center
        ws.cell(row=r, column=base_right + 4).fill = fill_total

        for c_idx in range(1, base_right + 6):
            ws.cell(row=r, column=c_idx).border = border_all
        r += 2

    # ================================================================
    # SHEET 2: sum
    # ================================================================
    ws2 = wb.create_sheet("sum")
    ws2.column_dimensions["A"].width = 14
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 12
    ws2.column_dimensions["D"].width = 20
    for col in "EFGHIJ":
        ws2.column_dimensions[col].width = 12

    ws2.merge_cells("A3:J3")
    ws2["A3"] = "CREATIVE COLLECTIONS LIMITED (UNIT-1A)"
    ws2["A3"].font = font_title
    ws2["A3"].alignment = align_center

    ws2.merge_cells("A4:J4")
    ws2["A4"] = "Nishatnagar,Tongi,Gazipur"
    ws2["A4"].font = font_addr
    ws2["A4"].alignment = align_center

    ws2.merge_cells("A5:J5")
    ws2["A5"] = "PACKING LIST SUMMARY"
    ws2["A5"].font = font_section
    ws2["A5"].alignment = align_center

    ws2["A7"] = "BUYER"; ws2["A7"].font = font_bold
    ws2["B7"] = buyer;   ws2["B7"].font = font_normal
    ws2["H7"] = "DATE";  ws2["H7"].font = font_bold
    ws2["I7"] = "01/02/2026"; ws2["I7"].font = font_normal

    ws2["A8"] = "STYLE"; ws2["A8"].font = font_bold
    ws2["B8"] = style;   ws2["B8"].font = font_normal

    hdrs = ["DC", "PO NO", "SEASON", "COLOR/CODE", "ORD/QTY", "SHIP/QTY",
            "EXCES", "SHORT", "PER (%)", "CTNS"]
    for i, h in enumerate(hdrs):
        c = ws2.cell(row=10, column=1 + i, value=h)
        c.font = font_bold; c.alignment = align_center
        c.fill = fill_header; c.border = border_all

    r2 = 11
    for color, rows in groups.items():
        hdr = header_map.get(color, {})
        ws2.cell(row=r2, column=1, value="BDC").alignment = align_center
        ws2.cell(row=r2, column=2, value=po_no).alignment = align_center
        ws2.cell(row=r2, column=3, value="Sum'26").alignment = align_center
        ws2.cell(row=r2, column=4, value=color).alignment = align_center
        ws2.cell(row=r2, column=5, value=hdr.get("oiqty", 0)).alignment = align_center
        ws2.cell(row=r2, column=6, value=hdr.get("ship_qty", 0)).alignment = align_center
        ws2.cell(row=r2, column=7, value=f"=F{r2}-E{r2}").alignment = align_center
        ws2.cell(row=r2, column=8, value=hdr.get("ex_short", 0)).alignment = align_center
        ws2.cell(row=r2, column=9, value=f"=G{r2}/E{r2}").alignment = align_center
        ws2.cell(row=r2, column=10, value=hdr.get("ctn_qty", 0)).alignment = align_center
        for c_idx in range(1, 11):
            ws2.cell(row=r2, column=c_idx).border = border_all
        r2 += 1

    ws2.cell(row=r2, column=4, value="TOTAL").font = font_bold
    ws2.cell(row=r2, column=4).alignment = align_center
    ws2.cell(row=r2, column=5, value=f"=SUM(E11:E{r2-1})").alignment = align_center
    ws2.cell(row=r2, column=6, value=f"=SUM(F11:F{r2-1})").alignment = align_center
    ws2.cell(row=r2, column=7, value=f"=SUM(G11:G{r2-1})").alignment = align_center
    ws2.cell(row=r2, column=8, value=f"=SUM(H11:H{r2-1})").alignment = align_center
    ws2.cell(row=r2, column=9, value=f"=H{r2}/E{r2}").alignment = align_center
    ws2.cell(row=r2, column=10, value=f"=SUM(J11:J{r2-1})").alignment = align_center
    for c_idx in range(1, 11):
        ws2.cell(row=r2, column=c_idx).fill = fill_total
        ws2.cell(row=r2, column=c_idx).border = border_all

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ===========================================================================
# UI
# ===========================================================================
_init_state()

with st.sidebar:
    st.markdown("### ⚖️ Weight settings (kg)")
    edited_sidebar = st.data_editor(
        st.session_state.weights_df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "N.W.":          st.column_config.NumberColumn("N.W.",          format="%.3f", step=0.001),
            "N.N.W.":        st.column_config.NumberColumn("N.N.W.",        format="%.3f", step=0.001),
            "EMPTY CTN WT.": st.column_config.NumberColumn("EMPTY CTN WT.", format="%.3f", step=0.001),
        },
        key="weights_editor_sidebar",
    )
    if not edited_sidebar.equals(st.session_state.weights_df):
        st.session_state.weights_df = edited_sidebar
        st.rerun()

    if st.button("↺ Reset weights", use_container_width=True):
        st.session_state.weights_df = _default_weights_df()
        st.rerun()

    st.divider()
    st.markdown("### 📦 CTN MEAS. (carton dimensions)")
    for i, m in enumerate(st.session_state.ctn_meas):
        new_m = st.text_input(f"Line {i+1}", value=m, key=f"ctn_meas_{i}")
        if new_m != m:
            st.session_state.ctn_meas[i] = new_m

    st.divider()
    blst_c = st.number_input("PER BLST multiplier C", min_value=1, max_value=8, value=1, step=1)
    st.info(f"`CTN MES:` is fixed to **{FIXED_CTN_MES}**.")

    if st.button("↺ Reset all cell edits", use_container_width=True):
        st.session_state.size_edits = {}
        st.session_state.ctn_edits  = {}
        st.rerun()

    st.divider()
    json_path = st.text_input("JSON file path", DEFAULT_JSON)


if not Path(json_path).exists():
    st.error(f"File not found: `{json_path}`")
    st.stop()

weights = get_weights()
data = load_json(json_path)
groups = build_grouped(data, weights["NW"], weights["EMPTY"], blst_c)

header_map = {k.replace("__header", ""): v for k, v in groups.items() if k.endswith("__header")}
groups = {k: v for k, v in groups.items() if not k.endswith("__header")}

if not groups:
    st.warning("No Multi Pack (Y) tables found in the JSON.")
    st.stop()

po_header = data.get("PO_HEADER", {}) or {}
buyer_fixed = po_header.get("BUYER") or DEFAULT_BUYER
po_no_fixed = po_header.get("P.O._#") or DEFAULT_PO_NO

grand_total_ctn = sum(
    (header_map[c]["ctn_qty"] or 0) for c in groups if c in header_map
) or 1


# ===========================================================================
# Render
# ===========================================================================
# Top block
render_company_header(st.session_state.weights_df)

all_frames: list = []
color_index = 0

for color, rows in groups.items():
    color_index += 1
    sizes = present_sizes(rows)
    columns = LEFT_STATIC + sizes + RIGHT_STATIC
    df = pd.DataFrame(rows).reindex(columns=columns)

    hdr = header_map.get(color, {})
    style_full = f"{DEFAULT_STYLE.rsplit('-', 2)[0]}-{hdr.get('color_code', '000')}-1"
    unit_prepack = f"{hdr.get('total_units_per_carton', 0)}/{hdr.get('ctn_qty', 0)}"
    carton_label = f"{color_index:02d} of {grand_total_ctn:03d}"

    render_section_strip("MULTY PACK ( Y )")
    render_po_header(
        buyer=buyer_fixed, style=style_full, po_no=po_no_fixed,
        oiqty=hdr.get("oiqty", 0), ship_qty=hdr.get("ship_qty", 0),
        ex_short=hdr.get("ex_short", 0), ctn_qty=hdr.get("ctn_qty", 0),
        ctn_meas_list=st.session_state.ctn_meas,
        sku_item=style_full, unit_prepack=unit_prepack, carton_label=carton_label,
    )

    render_size_weight_header(sizes, key_suffix=color)

    col_cfg = {
        "CTN NO":          st.column_config.TextColumn("CTN NO",  width="small", disabled=True),
        "CTN MES:":        st.column_config.TextColumn("CTN MES:", width="small", disabled=True),
        "CTN QTY":         st.column_config.NumberColumn("CTN QTY", width="small", min_value=1, step=1, format="%d"),
        "COLOR":           st.column_config.TextColumn("COLOR",           width="medium", disabled=True),
        "PREPACK STECKER": st.column_config.TextColumn("PREPACK STECKER", width="medium", disabled=True),
        "PER BLST":        st.column_config.TextColumn("PER BLST",   width="small", disabled=True),
        "QTY PER CTN":     st.column_config.NumberColumn("QTY PER CTN", width="small", disabled=True),
        "TOTAL QTY":       st.column_config.TextColumn("TOTAL QTY",  width="small", disabled=True),
        "GROSS WEIGHT":    st.column_config.NumberColumn("GROSS WEIGHT", width="small", format="%.2f", disabled=True),
        "NET WEIGHT":      st.column_config.NumberColumn("NET WEIGHT",   width="small", format="%.2f", disabled=True),
    }
    for s in sizes:
        col_cfg[s] = st.column_config.NumberColumn(s, width="small", min_value=0, step=1)

    try:
        edited = st.data_editor(
            data=df, use_container_width=True, hide_index=True,
            num_rows="fixed", column_config=col_cfg,
            key=f"multi_editor_{color}",
        )
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True)
        edited = df

    if _persist_edits(color, df, edited, sizes):
        st.rerun()

    all_frames.append((color, edited))


# ===========================================================================
# Downloads
# ===========================================================================
st.markdown("### Download")
col1, col2 = st.columns(2)

with col1:
    export_rows: list = []
    for i, (_, frame) in enumerate(all_frames):
        if i > 0:
            export_rows.append({})
        export_rows.extend(frame.to_dict(orient="records"))
    combined = pd.DataFrame(export_rows)
    st.download_button(
        "⬇ Download CSV (all colors)",
        data=combined.to_csv(index=False).encode("utf-8"),
        file_name="packing_list_multi.csv", mime="text/csv",
        use_container_width=True,
    )

with col2:
    try:
        xlsx_bytes = export_excel_template(
            all_frames=all_frames, header_map=header_map, groups=groups,
            weights_df=st.session_state.weights_df, ctn_meas=st.session_state.ctn_meas,
            buyer=buyer_fixed, style=DEFAULT_STYLE, po_no=po_no_fixed,
            grand_total_ctn=grand_total_ctn,
        )
        st.download_button(
            "⬇ Download Excel (template format)",
            data=xlsx_bytes,
            file_name="packing_list_multi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Excel export failed: {e}")


with st.sidebar:
    st.markdown("### Colors detected")
    for color, rows in groups.items():
        n = sum(1 for r in rows if r.get("CTN NO") != "TOTAL")
        st.write(f"- **{color}** — {n} group(s)")