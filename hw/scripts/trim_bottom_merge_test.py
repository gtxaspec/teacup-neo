"""Trim the merge-test board's BOTTOM edge only by 400mil (10.16mm), so it
sits close to where the bottom-edge ports (J2/J3/J4/J5/J9) actually are,
rather than the more generous uniform margin from the last resize. Top,
left, and right edges untouched. Per explicit user direction, 2026-07-14.

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 trim_bottom_merge_test.py
"""
import math
import pcbnew

BOARD_PATH = "/home/administrator/projects/teacup-neo/hw/teacup-carrier-merge-test.kicad_pcb"
TRIM_MM = 10.16     # 400 mil
CORNER_R = 3.1


def mm(v):
    return pcbnew.FromMM(v)


board = pcbnew.LoadBoard(BOARD_PATH)

# ---- 1. current outline extent, read directly off the Edge.Cuts shapes ---
xs, ys = [], []
old_shapes = []
for shape in board.GetDrawings():
    if not hasattr(shape, "GetLayer") or shape.GetLayer() != pcbnew.Edge_Cuts:
        continue
    old_shapes.append(shape)
    for getter in ("GetStart", "GetEnd"):
        if hasattr(shape, getter):
            p = getattr(shape, getter)()
            xs.append(pcbnew.ToMM(p.x)); ys.append(pcbnew.ToMM(p.y))
NX0, NY0, NX1, NY1_old = min(xs), min(ys), max(xs), max(ys)
NY1 = NY1_old - TRIM_MM
print(f"old bottom edge: {NY1_old:.2f}  new bottom edge: {NY1:.2f}")
print(f"new board: ({NX0:.1f},{NY0:.1f}) to ({NX1:.1f},{NY1:.1f}) = {NX1-NX0:.1f} x {NY1-NY0:.1f} mm")

# ---- 2. remove the old Edge.Cuts outline ----------------------------------
for shape in old_shapes:
    board.Remove(shape)

# ---- 3. redraw outline with the new (shorter) bottom edge -----------------
def add_line(x1, y1, x2, y2):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    seg.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(mm(0.1))
    board.Add(seg)


def add_corner_arc(ccx, ccy, start_deg, end_deg):
    mid_deg = (start_deg + end_deg) / 2
    def pt(deg):
        r = math.radians(deg)
        return ccx + CORNER_R * math.cos(r), ccy + CORNER_R * math.sin(r)
    sx, sy = pt(start_deg); mx, my = pt(mid_deg); ex, ey = pt(end_deg)
    arc = pcbnew.PCB_SHAPE(board)
    arc.SetShape(pcbnew.SHAPE_T_ARC)
    arc.SetArcGeometry(pcbnew.VECTOR2I(mm(sx), mm(sy)),
                        pcbnew.VECTOR2I(mm(mx), mm(my)),
                        pcbnew.VECTOR2I(mm(ex), mm(ey)))
    arc.SetLayer(pcbnew.Edge_Cuts)
    arc.SetWidth(mm(0.1))
    board.Add(arc)


R = CORNER_R
add_line(NX0 + R, NY0, NX1 - R, NY0)                   # top
add_line(NX1, NY0 + R, NX1, NY1 - R)                   # right
add_line(NX1 - R, NY1, NX0 + R, NY1)                   # bottom
add_line(NX0, NY1 - R, NX0, NY0 + R)                   # left
add_corner_arc(NX1 - R, NY0 + R, -90, 0)                # top-right
add_corner_arc(NX1 - R, NY1 - R, 0, 90)                 # bottom-right
add_corner_arc(NX0 + R, NY1 - R, 90, 180)               # bottom-left
add_corner_arc(NX0 + R, NY0 + R, 180, 270)              # top-left

# ---- 4. move ONLY the bottom two mounting holes (H3/H4) up to match; top
# two (H1/H2) untouched. ----------------------------------------------------
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref in ("H3", "H4"):
        p = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(p.x, mm(NY1 - R)))

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"wrote {BOARD_PATH}")
