"""Build a structural steel bill of materials (Excel) from a member list (CSV).

    python bom_builder.py members.csv -o Steel_BoM.xlsx --project "Shed 01" --waste 5

Input CSV columns (header row required):
    category, mark, section, description, qty, length_m, sheet, notes
Optional column kg_per_m overrides the calculated mass for that line.

The workbook keeps live formulas (total length = qty x length, total kg = length x kg/m,
subtotals, waste allowance), so the numbers can be checked and edited in Excel.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import OrderedDict

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from steel_sections import kg_per_m

NAVY = "1F3A5F"
LIGHT = "E8EEF5"
GROUP = "D6E2EF"
INPUT = "FFF4CC"
thin = Side(style="thin", color="B7C3D0")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

COLUMNS = [  # header, width, number format
    ("Mark", 12, None), ("Section", 20, None), ("Description", 30, None), ("Qty", 6, "0"),
    ("Length each (m)", 10, "0.00"), ("Total length (m)", 11, "0.00"), ("kg/m", 8, "0.00"),
    ("Total kg", 11, '#,##0.0;-#,##0.0;"-"'), ("Sheet", 9, None), ("Notes", 34, None),
    ("kg/m source", 32, None), ("Category", 18, None),
]


def read_members(path: str) -> "OrderedDict[str, list[dict]]":
    groups: "OrderedDict[str, list[dict]]" = OrderedDict()
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            if not row.get("section"):
                continue
            groups.setdefault(row.get("category") or "Other", []).append(row)
    return groups


def build(groups, out_path: str, project: str, drawings: str, prepared: str, waste: float,
          notes: list[str]) -> dict:
    wb = Workbook()
    ws = wb.active
    ws.title = "BoM"
    bold = Font(bold=True)
    white = Font(bold=True, color="FFFFFF")

    # title block
    ws["A1"] = "STRUCTURAL STEEL BILL OF MATERIALS"
    ws["A1"].font = Font(bold=True, size=14, color=NAVY)
    info = [("Project", project), ("Drawings", drawings), ("Prepared by", prepared),
            ("Date", dt.date.today().strftime("%d %b %Y"))]
    for i, (k, v) in enumerate(info, start=2):
        ws.cell(i, 1, k).font = bold
        ws.cell(i, 2, v)
    ws["H2"] = "Waste allowance"
    ws["H2"].font = bold
    ws.merge_cells("H2:I2")
    ws["J2"] = waste / 100
    ws["J2"].number_format = "0%"
    ws["J2"].fill = PatternFill("solid", fgColor=INPUT)
    ws["H3"] = "Yellow cell = input, change it and totals update."

    hdr = 7
    for c, (name, width, _) in enumerate(COLUMNS, start=1):
        cell = ws.cell(hdr, c, name)
        cell.font = white
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(c)].width = width
    ws.row_dimensions[hdr].height = 30

    r = hdr + 1
    first_data = r
    unknown = []
    stats = {"lines": 0}
    for cat, rows in groups.items():
        ws.cell(r, 1, cat.upper()).font = bold
        for c in range(1, len(COLUMNS) + 1):
            ws.cell(r, c).fill = PatternFill("solid", fgColor=GROUP)
            ws.cell(r, c).border = BORDER
        r += 1
        g0 = r
        for m in rows:
            kg_override = m.get("kg_per_m")
            if kg_override:
                kg, src = float(kg_override), "given in member list"
            else:
                kg, src = kg_per_m(m["section"])
            if kg is None:
                unknown.append(m["section"])
            vals = [m.get("mark"), m["section"], m.get("description"),
                    float(m.get("qty") or 0), float(m.get("length_m") or 0),
                    f"=D{r}*E{r}", kg if kg is not None else None,
                    f'=IF(G{r}="","",F{r}*G{r})', m.get("sheet"), m.get("notes"), src, cat]
            for c, v in enumerate(vals, start=1):
                cell = ws.cell(r, c, v)
                cell.border = BORDER
                fmt = COLUMNS[c - 1][2]
                if fmt:
                    cell.number_format = fmt
                if c == 7 and kg is None:
                    cell.fill = PatternFill("solid", fgColor=INPUT)
            stats["lines"] += 1
            r += 1
        ws.cell(r, 3, f"Subtotal - {cat}").font = bold
        ws.cell(r, 6, f"=SUBTOTAL(9,F{g0}:F{r-1})")
        ws.cell(r, 8, f"=SUBTOTAL(9,H{g0}:H{r-1})")
        for c in range(1, len(COLUMNS) + 1):
            cell = ws.cell(r, c)
            cell.fill = PatternFill("solid", fgColor=LIGHT)
            cell.border = BORDER
            cell.font = bold
            if COLUMNS[c - 1][2]:
                cell.number_format = COLUMNS[c - 1][2]
        r += 2
    last_data = r - 1

    def total_row(row, label, f_len, f_kg):
        ws.cell(row, 3, label).font = bold
        if f_len:
            ws.cell(row, 6, f_len).number_format = "#,##0.00"
        ws.cell(row, 8, f_kg).number_format = '#,##0.0;-#,##0.0;"-"' 
        for c in (3, 6, 8):
            ws.cell(row, c).font = bold
        for c in range(1, len(COLUMNS) + 1):
            ws.cell(row, c).border = BORDER

    total_row(r, "TOTAL (net)", f"=SUBTOTAL(9,F{first_data}:F{last_data})",
              f"=SUBTOTAL(9,H{first_data}:H{last_data})")
    total_row(r + 1, "Waste / offcut allowance", None, f"=H{r}*$J$2")
    total_row(r + 2, "TOTAL incl. allowance (kg)", None, f"=H{r}+H{r+1}")
    total_row(r + 3, "TOTAL incl. allowance (tonnes)", None, f"=H{r+2}/1000")
    ws.cell(r + 3, 8).number_format = "0.000"
    for rr in range(r, r + 4):
        for c in range(1, len(COLUMNS) + 1):
            ws.cell(rr, c).fill = PatternFill("solid", fgColor=LIGHT)
    ws.column_dimensions["L"].hidden = True
    ws.freeze_panes = ws.cell(hdr + 1, 1)
    ws.print_title_rows = f"{hdr}:{hdr}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:K{r+3}"

    # summary by section and by category
    sm = wb.create_sheet("Summary")
    sm["A1"] = "SUMMARY"
    sm["A1"].font = Font(bold=True, size=14, color=NAVY)
    heads = ["Section", "Total length (m)", "kg/m", "Total kg"]
    for c, h in enumerate(heads, start=1):
        cell = sm.cell(3, c, h)
        cell.font = white
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.border = BORDER
    sections = list(OrderedDict.fromkeys(m["section"] for rows in groups.values() for m in rows))
    rr = 4
    for s in sections:
        sm.cell(rr, 1, s)
        sm.cell(rr, 2, f'=SUMIF(BoM!$B${first_data}:$B${last_data},A{rr},BoM!$F${first_data}:$F${last_data})').number_format = "0.00"
        sm.cell(rr, 3, f'=IFERROR(IF(INDEX(BoM!$G${first_data}:$G${last_data},MATCH(A{rr},BoM!$B${first_data}:$B${last_data},0))="","",INDEX(BoM!$G${first_data}:$G${last_data},MATCH(A{rr},BoM!$B${first_data}:$B${last_data},0))),"")').number_format = "0.00"
        sm.cell(rr, 4, f'=SUMIF(BoM!$B${first_data}:$B${last_data},A{rr},BoM!$H${first_data}:$H${last_data})').number_format = '#,##0.0;-#,##0.0;"-"'
        for c in range(1, 5):
            sm.cell(rr, c).border = BORDER
        rr += 1
    sm.cell(rr, 1, "TOTAL (net)").font = bold
    sm.cell(rr, 2, f"=SUM(B4:B{rr-1})").number_format = "#,##0.00"
    sm.cell(rr, 4, f"=SUM(D4:D{rr-1})").number_format = "#,##0.0"
    rr += 2
    for c, h in enumerate(["Category", "Total length (m)", "", "Total kg"], start=1):
        cell = sm.cell(rr, c, h)
        cell.font = white
        cell.fill = PatternFill("solid", fgColor=NAVY)
    rr += 1
    c0 = rr
    for cat in groups:
        sm.cell(rr, 1, cat)
        sm.cell(rr, 2, f'=SUMIF(BoM!$L${first_data}:$L${last_data},A{rr},BoM!$F${first_data}:$F${last_data})').number_format = "0.00"
        sm.cell(rr, 4, f'=SUMIF(BoM!$L${first_data}:$L${last_data},A{rr},BoM!$H${first_data}:$H${last_data})').number_format = '#,##0.0;-#,##0.0;"-"'
        rr += 1
    sm.cell(rr, 1, "TOTAL (net)").font = bold
    sm.cell(rr, 4, f"=SUM(D{c0}:D{rr-1})").number_format = "#,##0.0"
    for col, w in zip("ABCD", (24, 16, 10, 14)):
        sm.column_dimensions[col].width = w

    nt = wb.create_sheet("Notes")
    nt["A1"] = "NOTES, ASSUMPTIONS AND EXCLUSIONS"
    nt["A1"].font = Font(bold=True, size=14, color=NAVY)
    base = ["Lengths are measured centre-line / grid to grid unless noted; laps added where shown.",
            "kg/m: hot-rolled from designation or AS/NZS 3679.1 tables; hollow sections and angles "
            "calculated (density 7850 kg/m3). Verify against the supplier catalogue before ordering.",
            "Yellow kg/m cells: section not recognised - enter the supplier value."]
    for i, line in enumerate(base + notes, start=3):
        nt.cell(i, 1, f"{i-2}. {line}").alignment = Alignment(wrap_text=True, vertical="top")
    nt.column_dimensions["A"].width = 120
    if unknown:
        nt.cell(len(base + notes) + 4, 1, "Sections without kg/m: " + ", ".join(sorted(set(unknown)))).font = Font(bold=True, color="C00000")

    wb.save(out_path)
    stats["unknown"] = sorted(set(unknown))
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("members")
    ap.add_argument("-o", "--out", default="Steel_BoM.xlsx")
    ap.add_argument("--project", default="")
    ap.add_argument("--drawings", default="")
    ap.add_argument("--prepared", default="")
    ap.add_argument("--waste", type=float, default=5.0, help="waste / offcut allowance, percent")
    ap.add_argument("--note", action="append", default=[], help="extra note line (repeat)")
    a = ap.parse_args()
    stats = build(read_members(a.members), a.out, a.project, a.drawings, a.prepared, a.waste, a.note)
    print(f"{a.out}: {stats['lines']} lines")
    if stats["unknown"]:
        print("kg/m missing for:", ", ".join(stats["unknown"]))


if __name__ == "__main__":
    main()
