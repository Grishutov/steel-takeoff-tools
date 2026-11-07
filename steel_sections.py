"""Mass per metre (kg/m) of common structural steel sections from their designation.

Supported designations (spaces and case are ignored):
  Australian hot-rolled      310UB40.4, 150UC30.0, 700WB115, 125TFB  -> mass is in the name
  Australian channels        100PFC, 250PFC                          -> catalogue table below
  US wide flange / channels  W12x26, C10x15.3, MC8x20, S6x12.5        -> lb/ft in the name
  Square / rectangular HSS   150x150x6.0 SHS, 150x50x3RHS, 89x3.5SHS -> calculated (AS/NZS 1163 corner radii)
  Circular hollow sections   88.9x3.2 CHS, 114.3x4.8CHS              -> calculated
  Angles                     150x90x10UA, 75x75x6EA, 65x8EA          -> calculated, root radius ignored (approx.)
  Round bar / rod bracing    M20 ROD, RB16, 20 DIA, 20 ROD            -> calculated from diameter

Cold-formed purlins and girts (C15024, Z20019 ...) vary by manufacturer, so they are not
calculated: put the supplier's kg/m in sections_custom.csv and it will be used first.

Steel density 7850 kg/m3.
"""
from __future__ import annotations

import csv
import math
import os
import re

DENSITY = 7850.0  # kg/m3
LB_FT_TO_KG_M = 1.48816394

# Australian parallel flange channels (AS/NZS 3679.1), kg/m
PFC_AU = {75: 5.92, 100: 8.33, 125: 11.9, 150: 17.7, 180: 20.9, 200: 22.9,
          230: 25.1, 250: 35.5, 300: 40.1, 380: 55.2}

_custom: dict[str, tuple[float, str]] | None = None


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s.upper().replace("×", "X"))


def load_custom(path: str | None = None) -> dict[str, tuple[float, str]]:
    """Read sections_custom.csv (designation, kg_per_m, source). Missing file -> empty."""
    global _custom
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sections_custom.csv")
    table: dict[str, tuple[float, str]] = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                name = (row.get("designation") or "").strip()
                kg = (row.get("kg_per_m") or "").strip()
                if not name or name.startswith("#") or not kg:
                    continue
                try:
                    table[_norm(name)] = (float(kg), (row.get("source") or "custom table").strip())
                except ValueError:
                    continue
    _custom = table
    return table


def _hollow_rect(b: float, d: float, t: float) -> float:
    """Cross-section area (mm2) of a cold-formed SHS/RHS with AS/NZS 1163 corner radii."""
    ro = 2.0 * t if t <= 3.0 else 2.5 * t
    ri = ro - t
    return 2 * t * (b + d - 2 * t) - (4 - math.pi) * (ro ** 2 - ri ** 2)


def kg_per_m(designation: str) -> tuple[float | None, str]:
    """Return (kg/m, method). kg/m is None when the section is not recognised."""
    if _custom is None:
        load_custom()
    s = _norm(designation)
    if s in _custom:
        return _custom[s]

    # Australian UB / UC / WB / WC / TFB with mass in the name: 310UB40.4
    m = re.fullmatch(r"(\d+)(UB|UC|WB|WC|UBP)(\d+(?:\.\d+)?)", s)
    if m:
        return float(m.group(3)), "mass in designation"
    m = re.fullmatch(r"(\d+)PFC", s)
    if m and int(m.group(1)) in PFC_AU:
        return PFC_AU[int(m.group(1))], "AS/NZS 3679.1 PFC table"

    # US shapes with lb/ft in the name: W12X26, C10X15.3, MC8X20, S6X12.5, HP10X42
    m = re.fullmatch(r"(W|C|MC|S|HP|M)(\d+(?:\.\d+)?)X(\d+(?:\.\d+)?)", s)
    if m:
        return round(float(m.group(3)) * LB_FT_TO_KG_M, 2), "lb/ft in designation"

    # SHS / RHS: 150X150X6.0SHS, 150X50X3RHS, 89X3.5SHS (square shorthand)
    m = re.fullmatch(r"(\d+(?:\.\d+)?)X(\d+(?:\.\d+)?)X(\d+(?:\.\d+)?)(SHS|RHS)(?:\(.*\))?", s)
    if m:
        b, d, t = map(float, m.group(1, 2, 3))
        return round(_hollow_rect(b, d, t) * 1e-6 * DENSITY, 2), "calculated, AS/NZS 1163 radii"
    m = re.fullmatch(r"(\d+(?:\.\d+)?)X(\d+(?:\.\d+)?)SHS(?:\(.*\))?", s)
    if m:
        b, t = map(float, m.group(1, 2))
        return round(_hollow_rect(b, b, t) * 1e-6 * DENSITY, 2), "calculated, AS/NZS 1163 radii"

    # CHS: 88.9X3.2CHS
    m = re.fullmatch(r"(\d+(?:\.\d+)?)X(\d+(?:\.\d+)?)CHS(?:\(.*\))?", s)
    if m:
        dia, t = map(float, m.group(1, 2))
        area = math.pi / 4 * (dia ** 2 - (dia - 2 * t) ** 2)
        return round(area * 1e-6 * DENSITY, 2), "calculated"

    # Angles: 150X90X10UA, 75X75X6EA, 65X8EA (equal angle shorthand)
    m = re.fullmatch(r"(\d+)X(\d+)X(\d+(?:\.\d+)?)(EA|UA|L)", s)
    if m:
        b, d, t = map(float, m.group(1, 2, 3))
        return round(t * (b + d - t) * 1e-6 * DENSITY, 2), "calculated, approx. (no root radius)"
    m = re.fullmatch(r"(\d+)X(\d+(?:\.\d+)?)(EA|L)", s)
    if m:
        b, t = map(float, m.group(1, 2))
        return round(t * (2 * b - t) * 1e-6 * DENSITY, 2), "calculated, approx. (no root radius)"

    # Rods: M20ROD, M20RODBRACING, RB16, 20DIA, 20ROD, Ø20
    m = re.fullmatch(r"(?:M|RB|Ø)?(\d+(?:\.\d+)?)(?:ROD|DIA|RODBRACING|BAR)?.*", s)
    if m and re.match(r"(M|RB|Ø)\d|\d+(\.\d+)?(ROD|DIA)", s):
        dia = float(m.group(1))
        return round(math.pi / 4 * dia ** 2 * 1e-6 * DENSITY, 2), "calculated from diameter"

    if re.fullmatch(r"[CZ]\d{5}", s):
        return None, "cold-formed - enter supplier kg/m"
    return None, "not recognised - add to sections_custom.csv"


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:] or ["310UB40.4", "100PFC", "150x150x6.0 SHS", "89x89x3.5 SHS",
                                 "125x75x3.5 RHS", "88.9x3.2 CHS", "150x90x10UA", "M20 ROD",
                                 "W12x26", "C15024"]:
        kg, how = kg_per_m(arg)
        print(f"{arg:20s} {'' if kg is None else f'{kg:8.2f} kg/m'}  {how}")
