"""
Regression tests: packing logic vs the hand-made reference packing lists
  Style - 905518 PO - 61480360 ... Multi Y OK (2).xlsx
  Style - 908546 PO - 61429740 ... Multi.xlsx

Run:  python -m pytest tests -q        (from the project folder)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import parser_lib as parser  # noqa: E402
from color_builders import (  # noqa: E402
    build_bulk_by_color, build_multi_y_by_color, build_single_by_color,
)
from multi_n_core import DEFAULT_TARE, build_multi_n  # noqa: E402
from color_builders import DEFAULT_NW  # noqa: E402


def load(po):
    return json.loads((ROOT / f"{po}.json").read_text(encoding="utf-8"))


def by_color(secs):
    return {s["color"]: s for s in secs}


def size_totals(sec):
    out = {}
    for r in sec["rows"]:
        out[r["size"]] = out.get(r["size"], 0) + r["total_qty"]
    return out


def test_pdf_parses_to_saved_json():
    for po in ("61480360", "61429740"):
        data = parser.parse_text(parser.extract_text(str(ROOT / f"{po}.pdf")))
        assert data == load(po)


# ---------------------------------------------------------------- Bulk
def test_bulk_61480360_matches_reference():
    b = by_color(build_bulk_by_color(load("61480360")))
    nc, tw = b["NAVY CAPTAIN"], b["TEAKWOOD"]
    # ship qty and per-size quantities are exact
    assert (nc["qty_ordered"], nc["ship_qty"]) == (878, 935)
    assert (tw["qty_ordered"], tw["ship_qty"]) == (1430, 1505)
    assert size_totals(nc) == {"XS": 32, "S": 216, "M": 256, "L": 239, "XL": 146, "XXL": 31, "XXL+": 15}
    assert size_totals(tw) == {"XS": 58, "S": 311, "M": 449, "L": 402, "XL": 239, "XXL": 31, "XXL+": 15}
    # carton count: Teakwood exact; Navy Captain reference hand-splits 3
    # remainders into extra small cartons (53), we pack minimal (50)
    assert tw["ctn_total"] == 80
    assert nc["ctn_total"] == 50


def test_bulk_61429740_matches_reference():
    b = by_color(build_bulk_by_color(load("61429740")))
    es, nv = b["ESPRESSO BARK"], b["IN THE NAVY"]
    assert es["ctn_total"] == 15 and nv["ctn_total"] == 34       # exact
    assert size_totals(nv) == {"12-18M": 13, "18-24M": 81, "2T": 298, "3T": 343, "4T": 424, "5T": 318}
    # Espresso: excess trimmed so 4T/5T end on a full carton -> 622, exact.
    # In The Navy: reference ships 1471 (4T trimmed by 6 more); we ship 1477.
    assert es["ship_qty"] == 622 and nv["ship_qty"] == 1477


# -------------------------------------------------------------- Single
def test_single_matches_reference():
    s = by_color(build_single_by_color(load("61480360")))
    assert s["NAVY CAPTAIN"]["ctn_total"] == 27 and s["NAVY CAPTAIN"]["ship_qty"] == 510
    assert s["TEAKWOOD"]["ship_qty"] == 534
    assert s["TEAKWOOD"]["ctn_total"] == 29          # reference: 30 (hand split 10+5+3)
    t = build_single_by_color(load("61429740"))
    assert len(t) == 1 and t[0]["ctn_total"] == 4 and t[0]["ship_qty"] == 66


# -------------------------------------------------------------- Multi Y
def test_multi_y_matches_reference():
    secs = build_multi_y_by_color(load("61480360"))
    assert [s["ctn_total"] for s in secs] == [89, 89]
    for s in secs:
        r = s["rows"][0]
        assert (r["gross"], r["net"]) == (4.8, 4.38)
        assert r["total_qty"] == 623


# -------------------------------------------------------------- Multi N
def test_multi_n_matches_reference_quantities():
    secs = build_multi_n(load("61429740"), DEFAULT_NW, DEFAULT_TARE)
    assert [s["ctn_total"] for s in secs] == [62, 62]
    assert [s["ship_qty"] for s in secs] == [2223, 2223]


# -------------------------------------------------------------- totals
def test_carton_numbers_are_continuous_and_totals_reconcile():
    for po, expect_ctn in (("61429740", 177), ("61480360", 364)):
        d = load(po)
        n = 1
        allrows = []
        for fn in (build_bulk_by_color, build_single_by_color, build_multi_y_by_color):
            secs = fn(d, n)
            for s in secs:
                allrows += s["rows"]
                n += s["ctn_total"]
        for s in build_multi_n(d, DEFAULT_NW, DEFAULT_TARE, start_ctn_no=n):
            allrows += s["rows"]
            n += s["ctn_total"]
        prev_end = 0
        for r in allrows:
            assert r["ctn_from"] == prev_end + 1
            prev_end = r["ctn_to"]
        assert n - 1 == expect_ctn      # ref: 177 / 368 (4 hand-split cartons)
