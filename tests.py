"""Quick checks against published catalogue values (run: python tests.py)."""
from steel_sections import kg_per_m

CASES = {  # designation: (published kg/m, tolerance %)
    "310UB40.4": (40.4, 0.1), "100PFC": (8.33, 0.1), "50x50x3.0 SHS": (4.25, 1.5),
    "100x100x6.0 SHS": (16.7, 1.5), "88.9x3.2 CHS": (6.76, 1.0), "75x75x6EA": (6.81, 2.5),
    "M20 ROD": (2.47, 1.0), "W12x26": (38.7, 0.5),
}
fail = 0
for s, (ref, tol) in CASES.items():
    kg, how = kg_per_m(s)
    ok = kg is not None and abs(kg - ref) / ref * 100 <= tol
    fail += not ok
    print(f"{'OK ' if ok else 'BAD'} {s:18s} calc {kg}  ref {ref}  ({how})")
assert kg_per_m("C15024")[0] is None
print("all passed" if not fail else f"{fail} failed")
