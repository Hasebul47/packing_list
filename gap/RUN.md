# GAP / OLD NAVY – PO sheet to packing list

## Unified app (recommended)

```bash
streamlit run unified_packing.py
```

**Flow:** Upload PDF → extract data → auto-detect packing type(s) → packing list tables + Excel download.

Supported types (auto-detected from each table):

| Type    | Rule                                              |
|---------|---------------------------------------------------|
| Bulk    | `PrePack Type == Bulk`                            |
| Single  | `PrePack Type == Single`                          |
| Multi Y | `PrePack Type == Multi` and `Full Carton == Y`    |
| Multi N | `PrePack Type == Multi` and `Full Carton == N`    |

Outputs:
- Extracted JSON
- Interactive packing-list tables per type
- Unified Excel (all types)
- Full-template Multi N Excel (when Multi N is present)

---

## Legacy separate apps

```bash
streamlit run app.py              # PO PDF -> JSON only
streamlit run bulk_pack.py        # BULK PACK
streamlit run single_pack.py      # SINGLE PACK
streamlit run multi_y_packing.py  # MULTY PACK ( Y )   Full Carton = Y
streamlit run multi_n_packing.py  # MULTY PACK ( N )   Full Carton = N
```

Multi N modules: `multi_n_core.py` (logic) + `multi_n_export.py` (Excel) + `multi_n_packing.py` (page)

Test POs:
- `61429740.pdf` → Bulk + Single + Multi N
- `61480360.pdf` → Bulk + Single + Multi Y

---

## Packing rules (verified against the reference sheets)

- **Bulk**: ship qty = order + excess, excess = floor(3% of that size's total order over all pack types), shipped inside Bulk. Cartons = full cartons of the per-size cap (XS-L 20, XL/XXL 18, XXL+ 15, 2T/3T 50, 4T/5T 44, 18-24M 60) + one remainder carton. Toddler excess is trimmed when it would only spill a tiny carton.
- **Single**: cap per size (pcs cap / units per prepack); a lone leftover prepack rides in the last full carton.
- **Multi Y**: gross = sum(units x N.W) + 0.71, net = gross - 0.42.
- Carton code (G81/G82/G84/G85) is picked from how full the carton is. Weights use tare G81/G82 = 0.71, G84/G85 = 0.24; the reference weights are hand-entered and cannot be matched exactly.
- Sidebar lets you change excess %, carton caps and the Single prepack limit.

## Tests

```bash
python -m pytest tests -q
```
Compares against `61429740` / `61480360` reference sheets. Known, documented differences: Navy Captain bulk has 53 cartons in the reference (hand-split remainders) vs 50 here; Teakwood single 30 vs 29; In The Navy ships 1471 in the reference vs 1477 here.
