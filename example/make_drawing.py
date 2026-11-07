"""Fictitious A3 framing sheet (S1) for a 24 x 12 m portal-frame shed, plus a colour takeoff markup.
Paper units are millimetres; drawings at 1:100 (1 m = 10 mm)."""
import csv
import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

plt.rcParams["font.family"] = "DejaVu Sans"
K = 10.0                       # mm per metre at 1:100
T5 = math.tan(math.radians(5))
C5 = math.cos(math.radians(5))
H = 4.5                        # eave height, m
RIDGE = H + 6 * T5

COL = {"C1": "#E53935", "EC1": "#E53935", "R1": "#FB8C00", "P1": "#1E88E5", "EP1": "#1E88E5",
       "G1": "#00897B", "G2": "#00897B", "BR1": "#D81B60", "BR2": "#D81B60", "S1": "#8E24AA",
       "FB1": "#8E24AA", "DH1": "#43A047", "PJ1": "#43A047", "PH1": "#43A047"}


class Sheet:
    def __init__(self, markup):
        self.markup = markup
        self.fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, 420)
        self.ax.set_ylim(0, 297)
        self.ax.axis("off")
        self.counts = {}

    def line(self, p, q, lw=0.35, color="black", ls="-", mark=None, z=2):
        self.ax.plot([p[0], q[0]], [p[1], q[1]], lw=lw, color=color, ls=ls, zorder=z,
                     solid_capstyle="butt")
        if self.markup and mark:
            self.ax.plot([p[0], q[0]], [p[1], q[1]], lw=4.2, color=COL[mark], alpha=0.38,
                         zorder=1, solid_capstyle="butt")

    def text(self, x, y, s, size=5.5, **kw):
        kw.setdefault("ha", "center")
        kw.setdefault("va", "center")
        self.ax.text(x, y, s, fontsize=size, zorder=5, **kw)

    def count_tag(self, x, y, mark, n):
        if self.markup:
            self.ax.add_patch(Circle((x, y), 1.9, fc=COL[mark], ec="white", lw=0.4, alpha=0.9, zorder=6))
            self.ax.text(x, y, str(n), fontsize=4.2, color="white", ha="center", va="center",
                         zorder=7, fontweight="bold")

    def bubble(self, x, y, s):
        self.ax.add_patch(Circle((x, y), 3.2, fc="white", ec="black", lw=0.35, zorder=4))
        self.text(x, y, s, size=6.5)

    def dim(self, p, q, off, label, vertical=False):
        """Linear dimension between p and q, offset perpendicular by off (mm)."""
        if vertical:
            x = p[0] + off
            self.line((p[0], p[1]), (x + 1, p[1]), lw=0.15)
            self.line((q[0], q[1]), (x + 1, q[1]), lw=0.15)
            self.line((x, p[1]), (x, q[1]), lw=0.2)
            for yy in (p[1], q[1]):
                self.line((x - 0.8, yy - 0.8), (x + 0.8, yy + 0.8), lw=0.3)
            self.text(x - 1.6, (p[1] + q[1]) / 2, label, size=4.5, rotation=90)
        else:
            y = p[1] + off
            self.line((p[0], p[1]), (p[0], y - 1), lw=0.15)
            self.line((q[0], q[1]), (q[0], y - 1), lw=0.15)
            self.line((p[0], y), (q[0], y), lw=0.2)
            for xx in (p[0], q[0]):
                self.line((xx - 0.8, y - 0.8), (xx + 0.8, y + 0.8), lw=0.3)
            self.text((p[0] + q[0]) / 2, y + 1.6, label, size=4.5)

    def title(self, x, y, s, scale="1:100"):
        self.text(x, y, s, size=7.5, ha="left", fontweight="bold")
        self.ax.plot([x, x + len(s) * 1.75], [y - 2.2, y - 2.2], lw=0.5, color="black")
        self.text(x, y - 4.5, scale, size=5, ha="left")


def roof_plan(sh, x0, y0):
    """Plan: grids 1-5 along x (6 m bays), A (y0) to B (y0+120)."""
    L, W = 24.0, 12.0
    gx = [x0 + i * 6 * K for i in range(5)]
    yA, yB = y0, y0 + W * K
    yR = y0 + 6 * K
    for i, x in enumerate(gx):
        sh.line((x, yA - 6), (x, yB + 4), lw=0.2, ls=(0, (6, 2, 1, 2)), color="#555")
        sh.bubble(x, yB + 7.2, str(i + 1))
    for y, n in ((yA, "A"), (yB, "B")):
        sh.line((x0 - 8, y), (gx[-1] + 4, y), lw=0.2, ls=(0, (6, 2, 1, 2)), color="#555")
        sh.bubble(x0 - 11.2, y, n)
    sh.line((x0, yR), (gx[-1], yR), lw=0.25, ls=(0, (8, 2, 2, 2)), color="#555")
    sh.text(gx[-1] + 6, yR, "RIDGE", size=4.2, ha="left")
    # rafters (portal frames) on every grid
    for i, x in enumerate(gx):
        sh.line((x, yA), (x, yR), lw=1.0, mark="R1")
        sh.line((x, yR), (x, yB), lw=1.0, mark="R1")
        sh.count_tag(x + 2.6, yA + 30, "R1", 2 * i + 1)
        sh.count_tag(x + 2.6, yB - 30, "R1", 2 * i + 2)
    sh.text(gx[2] - 3, yA + 45, "R1", size=5, rotation=90)
    # columns
    n = 0
    for x in gx:
        for y in (yA, yB):
            n += 1
            sh.ax.add_patch(Rectangle((x - 1.3, y - 1.0), 2.6, 2.0, fc="black", zorder=3))
            sh.count_tag(x - 3.6, y + (3.4 if y == yA else -3.4), "C1", n)
    sh.text(gx[0] + 5.5, yA - 3.5, "C1", size=5)
    k = 0
    for x in (gx[0], gx[-1]):
        for ym in (4, 8):
            k += 1
            y = yA + ym * K
            sh.ax.add_patch(Rectangle((x - 1.5, y - 1.5), 3, 3, fc="white", ec="black", lw=0.5, zorder=3))
            sh.count_tag(x + (-4 if x == gx[0] else 4), y, "EC1", k)
    sh.text(gx[0] - 5.5, yA + 6 * K, "EC1", size=4.6, rotation=90)
    # purlins: 6 rows each side, first 150 from eave, then 1150 crs (on slope)
    s_list = [0.15 + 1.15 * i for i in range(6)]
    for s in s_list:
        for y in (yA + s * C5 * K, yB - s * C5 * K):
            if abs(s - 0.15) < 1e-6:
                continue
            sh.line((gx[0], y), (gx[-1], y), lw=0.3, mark="P1")
    for y in (yA + 0.15 * C5 * K, yB - 0.15 * C5 * K):
        sh.line((gx[0], y), (gx[-1], y), lw=0.55, ls=(0, (4, 1.5)), mark="EP1")
    sh.text(gx[1] + 30, yA + 0.15 * C5 * K + 2.2, "EP1  C20019", size=4.4)
    sh.text(gx[1] + 30, yA + s_list[2] * C5 * K + 2.2, "P1  Z20019 @ 1150 MAX", size=4.4)
    sh.text(gx[3] + 30, yB - s_list[2] * C5 * K + 2.2, "P1", size=4.4)
    # roof bracing in end bays, both sides of ridge
    for b in (0, 3):
        xa, xb = gx[b], gx[b + 1]
        for ya, yb in ((yA, yR), (yR, yB)):
            sh.line((xa, ya), (xb, yb), lw=0.4, ls=(0, (5, 1.5)), mark="BR1")
            sh.line((xa, yb), (xb, ya), lw=0.4, ls=(0, (5, 1.5)), mark="BR1")
        sh.line((xa, yR), (xb, yR), lw=0.9, mark="S1")
        sh.text((xa + xb) / 2, yR + 2.4, "S1", size=4.6)
    sh.text((gx[0] + gx[1]) / 2 + 9, yA + 18, "BR1", size=4.6)
    # fly braces at grids 2-4, purlins 2, 4, 6 each side
    for x in gx[1:4]:
        for s in (s_list[1], s_list[3], s_list[5]):
            for y in (yA + s * C5 * K, yB - s * C5 * K):
                sh.line((x - 2.2, y - 1.4), (x + 2.2, y + 1.4), lw=0.35, mark="FB1")
    sh.text(gx[2] + 7, yB - s_list[3] * C5 * K - 3.2, "FB1", size=4.4)
    # dimensions
    for i in range(4):
        sh.dim((gx[i], yA - 6), (gx[i + 1], yA - 6), -6, "6000")
    sh.dim((gx[0], yA - 6), (gx[-1], yA - 6), -13, "24000")
    sh.dim((x0 - 16, yA), (x0 - 16, yB), -5, "12000", vertical=True)
    sh.title(x0, yA - 27, "ROOF FRAMING PLAN")


def frame_section(sh, x0, y0, k=K, scale="1:150"):
    """Typical portal frame, grids 2-4."""
    w = 12 * k
    eave, ridge = H * k, RIDGE * k
    sh.line((x0 - 5, y0), (x0 + w + 5, y0), lw=0.5)
    for i in range(int((w + 10) / 9)):
        sh.line((x0 - 5 + i * 9, y0 - 1.2), (x0 - 3 + i * 9, y0), lw=0.2)
    for x in (x0, x0 + w):
        sh.line((x, y0), (x, y0 + eave), lw=1.1, mark="C1")
    sh.count_tag(x0 - 3.2, y0 + eave / 2, "C1", 2)
    sh.text(x0 + 2.6, y0 + eave * 0.45, "C1", size=4.2, rotation=90)
    sh.line((x0, y0 + eave), (x0 + w / 2, y0 + ridge), lw=0.9, mark="R1")
    sh.line((x0 + w / 2, y0 + ridge), (x0 + w, y0 + eave), lw=0.9, mark="R1")
    sh.count_tag(x0 + w * 0.75, y0 + eave + w * 0.25 * T5 - 3.2, "R1", 2)
    sh.text(x0 + w * 0.27, y0 + eave + w * 0.27 * T5 - 3.4, "R1  250UB25.7", size=4.2, rotation=5)
    for (px, py), sgn in (((x0, y0 + eave), 1), ((x0 + w, y0 + eave), -1)):
        sh.ax.add_patch(Polygon([(px, py), (px + sgn * 7, py + 7 * T5), (px, py - 3)],
                                closed=True, fc="#BBB", ec="black", lw=0.2, zorder=3))
    for i in range(6):
        s = 0.15 + 1.15 * i
        for side in (1, -1):
            px = x0 + s * C5 * k if side == 1 else x0 + w - s * C5 * k
            py = y0 + eave + s * C5 * k * T5
            mk = "EP1" if i == 0 else "P1"
            sh.ax.add_patch(Rectangle((px - 0.6, py + 0.4), 1.2, 1.5, fc="white", ec="black", lw=0.3, zorder=3))
            if sh.markup:
                sh.ax.add_patch(Rectangle((px - 1.1, py), 2.2, 2.3, fc=COL[mk], alpha=0.4, zorder=1))
    for x in (x0, x0 + w):
        for h in (1.2, 2.4, 3.6):
            dx = -2.1 if x == x0 else 0.5
            sh.ax.add_patch(Rectangle((x + dx, y0 + h * k - 0.8), 1.6, 1.6, fc="white", ec="black", lw=0.3, zorder=3))
            if sh.markup:
                sh.ax.add_patch(Rectangle((x + dx - 0.4, y0 + h * k - 1.2), 2.4, 2.4, fc=COL["G1"], alpha=0.4, zorder=1))
    sh.text(x0 - 9.5, y0 + 1.8 * k, "G1", size=4.2)
    sh.text(x0 + w / 2, y0 + ridge + 3, "P1 / EP1", size=4.2)
    sh.dim((x0, y0), (x0 + w, y0), -5, "12000")
    sh.dim((x0 + w, y0), (x0 + w, y0 + eave), 6, "4500", vertical=True)
    sh.title(x0, y0 - 13, "TYPICAL PORTAL FRAME - GRIDS 2 TO 4", scale)


def end_wall(sh, x0, y0, grid=1, k=K, scale="1:150"):
    """End wall elevation: grid 1 roller door, grid 5 personnel door."""
    w = 12 * k
    eave = H * k
    sh.line((x0 - 5, y0), (x0 + w + 5, y0), lw=0.5)
    for x in (x0, x0 + w):
        sh.line((x, y0), (x, y0 + eave), lw=1.1, mark="C1")
    sh.line((x0, y0 + eave), (x0 + w / 2, y0 + RIDGE * k), lw=0.9, mark="R1")
    sh.line((x0 + w / 2, y0 + RIDGE * k), (x0 + w, y0 + eave), lw=0.9, mark="R1")
    for j, xm in enumerate((4, 8)):
        x = x0 + xm * k
        sh.line((x, y0), (x, y0 + (H + 4 * T5) * k), lw=0.8, mark="EC1")
        sh.count_tag(x + 2.8, y0 + 6, "EC1", (1 if grid == 1 else 3) + j)
    sh.text(x0 + 4 * k - 2.4, y0 + 3.2 * k, "EC1", size=4.2, rotation=90)
    if grid == 1:
        sh.line((x0 + 4 * k, y0 + 4 * k), (x0 + 8 * k, y0 + 4 * k), lw=0.8, mark="DH1")
        sh.text(x0 + 6 * k, y0 + 4 * k + 2.2, "DH1  100PFC", size=4.2)
        sh.ax.add_patch(Rectangle((x0 + 4 * k, y0), 4 * k, 4 * k, fc="none", ec="black", lw=0.25, ls="--", zorder=2))
        sh.text(x0 + 6 * k, y0 + 2 * k, "ROLLER DOOR\n4000 x 4000", size=4.2)
        for h in (1.2, 2.4, 3.6):
            y = y0 + h * k
            sh.line((x0, y), (x0 + 4 * k, y), lw=0.45, mark="G2")
            sh.line((x0 + 8 * k, y), (x0 + w, y), lw=0.45, mark="G2")
    else:
        for h in (1.2, 2.4, 3.6):
            y = y0 + h * k
            if h == 1.2:
                sh.line((x0, y), (x0 + 9 * k, y), lw=0.45, mark="G2")
                sh.line((x0 + 10 * k, y), (x0 + w, y), lw=0.45, mark="G2")
            else:
                sh.line((x0, y), (x0 + w, y), lw=0.45, mark="G2")
        for xm in (9, 10):
            sh.line((x0 + xm * k, y0), (x0 + xm * k, y0 + 2.4 * k), lw=0.7, mark="PJ1")
        sh.line((x0 + 9 * k, y0 + 2.1 * k), (x0 + 10 * k, y0 + 2.1 * k), lw=0.7, mark="PH1")
        sh.text(x0 + 9.5 * k, y0 + 1.0 * k, "PD", size=4.0)
        sh.text(x0 + 10.8 * k, y0 + 0.55 * k, "PJ1 / PH1", size=3.9, ha="left")
    sh.text(x0 + 2 * k, y0 + 2.4 * k + 2.0, "G2  C15015", size=4.2)
    for a in range(3):
        sh.dim((x0 + 4 * a * k, y0), (x0 + 4 * (a + 1) * k, y0), -5, "4000")
    sh.title(x0, y0 - 13, f"END WALL ELEVATION - GRID {grid}", scale)


def side_wall(sh, x0, y0, k=K, scale="1:150"):
    """Side wall elevation, grid A: girts G1, bracing BR2 in end bays."""
    gx = [x0 + i * 6 * k for i in range(5)]
    sh.line((x0 - 5, y0), (gx[-1] + 5, y0), lw=0.5)
    for x in gx:
        sh.line((x, y0), (x, y0 + H * k), lw=1.1, mark="C1")
    sh.line((gx[0], y0 + H * k), (gx[-1], y0 + H * k), lw=0.6, ls=(0, (4, 1.5)), mark="EP1")
    for h in (1.2, 2.4, 3.6):
        sh.line((gx[0], y0 + h * k), (gx[-1], y0 + h * k), lw=0.4, mark="G1")
    n = 0
    for b in (0, 3):
        for (p, q) in (((gx[b], y0), (gx[b + 1], y0 + H * k)), ((gx[b], y0 + H * k), (gx[b + 1], y0))):
            sh.line(p, q, lw=0.4, ls=(0, (5, 1.5)), mark="BR2")
            n += 1
            sh.count_tag(p[0] + (q[0] - p[0]) * 0.25, p[1] + (q[1] - p[1]) * 0.25, "BR2", n)
    sh.text((gx[0] + gx[1]) / 2, y0 + H * k * 0.62, "BR2  M20 ROD", size=4.2)
    sh.text((gx[1] + gx[2]) / 2, y0 + 2.4 * k + 2.0, "G1  Z15015 (3 ROWS)", size=4.2)
    sh.text((gx[2] + gx[3]) / 2, y0 + H * k + 2.0, "EP1  C20019", size=4.2)
    sh.dim((gx[0], y0), (gx[0], y0 + H * k), -7, "4500", vertical=True)
    sh.title(x0, y0 - 9, "SIDE WALL ELEVATION - GRID A (GRID B SIMILAR, BR2 x 4 PER WALL)", scale)


def schedule_and_title(sh, members, markup):
    x0, x1 = 300, 410
    sh.ax.add_patch(Rectangle((x0, 12), x1 - x0, 275, fc="none", ec="black", lw=0.5))
    y = 281
    sh.text(x0 + 3, y, "TAKEOFF LEGEND" if markup else "MEMBER SCHEDULE", size=7, ha="left",
            fontweight="bold")
    y -= 7
    cols = (x0 + 3, x0 + 15, x0 + 46, x0 + 88, x0 + 101) if markup else (x0 + 3, x0 + 15, x0 + 46)
    heads = ("MARK", "SECTION", "DESCRIPTION", "QTY", "TOTAL m") if markup else ("MARK", "SECTION", "DESCRIPTION")
    for c, h in zip(cols, heads):
        sh.text(c, y, h, size=4.6, ha="left", fontweight="bold")
    y -= 2.5
    sh.ax.plot([x0 + 2, x1 - 2], [y, y], lw=0.3, color="black")
    for m in members:
        y -= 5.2
        if markup:
            sh.ax.add_patch(Rectangle((x0 + 2.2, y - 1.6), 2.6, 3.2, fc=COL[m["mark"]], alpha=0.6, ec="none"))
        sh.text(cols[0] + (4 if markup else 0), y, m["mark"], size=4.6, ha="left")
        sh.text(cols[1], y, m["section"], size=4.6, ha="left")
        desc = m["description"] if len(m["description"]) <= 36 else m["description"][:35] + "."
        sh.text(cols[2], y, desc, size=4.4, ha="left")
        if markup:
            sh.text(cols[3] + 6, y, m["qty"], size=4.6, ha="right")
            tot = float(m["qty"]) * float(m["length_m"])
            sh.text(cols[4] + 6, y, f"{tot:.1f}", size=4.6, ha="right")
    y -= 6
    notes = (["MEASUREMENT NOTES", "1. Lengths centre-line, grid to grid.",
              "2. Purlins/girts: 24.0 m + 3 laps x 0.9 m.",
              "3. Plates, bolts, cleats, bridging excluded.",
              "4. Counts shown in coloured tags.",
              "5. Full quantities: Steel_BoM_Machinery_Shed.xlsx"]
             if markup else
             ["GENERAL NOTES", "1. Steel grade 300PLUS U.N.O., hollow sections C450L0.",
              "2. Roof pitch 5 deg, eave height 4500 above FFL.",
              "3. Purlins Z20019 lapped 15% of span at frames.",
              "4. Rod bracing with turnbuckles, end bays.",
              "5. Fictitious project - for demonstration only."])
    sh.ax.plot([x0 + 2, x1 - 2], [y + 2, y + 2], lw=0.3, color="black")
    for i, n in enumerate(notes):
        sh.text(x0 + 3, y - 3 - i * 4.6, n, size=4.6 if i else 5.2, ha="left",
                fontweight="bold" if i == 0 else "normal")
    # title block
    tb = 12
    sh.ax.plot([x0, x1], [tb + 52, tb + 52], lw=0.5, color="black")
    rows = [("PROJECT", "RURAL MACHINERY SHED 24 x 12 m"), ("", "SAMPLE - FICTITIOUS PROJECT"),
            ("SHEET", "FRAMING PLAN, SECTION AND ELEVATIONS"),
            ("PREPARED", "SERGEI GRISHUTOV - QUANTITY SURVEYOR"),
            ("SCALE", "AS SHOWN @ A3"), ("DATE", "NOV 2026")]
    for i, (k, v) in enumerate(rows):
        yy = tb + 46 - i * 5.6
        sh.text(x0 + 3, yy, k, size=4.2, ha="left", color="#555")
        sh.text(x0 + 22, yy, v, size=5, ha="left", fontweight="bold" if i < 2 else "normal")
    sh.text(x1 - 10, tb + 6.5, "S1" + ("-M" if markup else ""), size=12, fontweight="bold")
    sh.text(x1 - 32, tb + 6.5, "REV A", size=6)
    if markup:
        sh.ax.add_patch(Rectangle((x0 + 3, tb + 2), 52, 8, fc="none", ec="#D81B60", lw=0.8))
        sh.text(x0 + 29, tb + 6, "TAKEOFF MARKUP", size=6.5, color="#D81B60", fontweight="bold")
    else:
        sh.ax.add_patch(Rectangle((x0 + 3, tb + 2), 52, 8, fc="none", ec="black", lw=0.6))
        sh.text(x0 + 29, tb + 6, "NOT FOR CONSTRUCTION", size=6, fontweight="bold")


def make(markup, members, out_pdf, out_png):
    sh = Sheet(markup)
    sh.ax.add_patch(Rectangle((10, 10), 400, 277, fc="none", ec="black", lw=0.7))
    roof_plan(sh, 45, 152)
    k = 1000 / 150
    side_wall(sh, 45, 83, k)
    end_wall(sh, 212, 83, 1, k)
    frame_section(sh, 45, 31, k)
    end_wall(sh, 150, 31, 5, k)
    schedule_and_title(sh, members, markup)
    sh.fig.savefig(out_pdf)
    sh.fig.savefig(out_png, dpi=150)
    plt.close(sh.fig)


if __name__ == "__main__":
    with open(sys.argv[1] if len(sys.argv) > 1 else "members.csv", newline="") as f:
        members = list(csv.DictReader(f))
    make(False, members, "S1_Machinery_Shed_Framing.pdf", "S1_Machinery_Shed_Framing.png")
    make(True, members, "S1_Machinery_Shed_Takeoff_Markup.pdf", "S1_Machinery_Shed_Takeoff_Markup.png")
    print("ok")
