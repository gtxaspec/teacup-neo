"""Shrink the merge-test board's outline down to snugly enclose the current
component layout (the user did substantial manual placement since the last
script touched this file -- nothing but the outline and the 4 mounting
holes gets moved here). Per explicit user direction, 2026-07-14.

Split out from GND-pour work (see pour_merge_test.py) into its own process:
mixing PCB_SHAPE add/remove with ZONE creation in one pcbnew Python session
made unrelated footprints' .Pads() intermittently return untyped/broken
SWIG objects in this KiCad build -- a real environment instability, not a
logic bug. Running each phase as a fresh process against the saved file
sidesteps it entirely.

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 resize_merge_test.py
"""
import math
import pcbnew

BOARD_PATH = "/home/administrator/projects/teacup-neo/hw/teacup-carrier-merge-test.kicad_pcb"
MARGIN = 6.0        # clearance from the tightest component edge to the new board edge
CORNER_R = 3.1      # same corner-radius / hole-inset convention used throughout this board


def mm(v):
    return pcbnew.FromMM(v)


board = pcbnew.LoadBoard(BOARD_PATH)
ALL_FOOTPRINTS = list(board.GetFootprints())

# ---- 1. real extent of every actual component (mounting holes excluded --
# those are about to be repositioned to the new corners, not "enclosed"). --
x0s, y0s, x1s, y1s = [], [], [], []
mounting_holes = {}
for fp in ALL_FOOTPRINTS:
    ref = fp.GetReference()
    if ref in ("H1", "H2", "H3", "H4"):
        mounting_holes[ref] = fp
        continue
    bb = fp.GetBoundingBox()
    x0s.append(pcbnew.ToMM(bb.GetLeft())); y0s.append(pcbnew.ToMM(bb.GetTop()))
    x1s.append(pcbnew.ToMM(bb.GetRight())); y1s.append(pcbnew.ToMM(bb.GetBottom()))

NX0, NY0 = min(x0s) - MARGIN, min(y0s) - MARGIN
NX1, NY1 = max(x1s) + MARGIN, max(y1s) + MARGIN
NW, NH = NX1 - NX0, NY1 - NY0
print(f"component extent: x {min(x0s):.1f}-{max(x1s):.1f}, y {min(y0s):.1f}-{max(y1s):.1f}")
print(f"new board: ({NX0:.1f},{NY0:.1f}) to ({NX1:.1f},{NY1:.1f}) = {NW:.1f} x {NH:.1f} mm")

# ---- 2. remove the old Edge.Cuts outline ----------------------------------
for shape in list(board.GetDrawings()):
    if hasattr(shape, "GetLayer") and shape.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(shape)

# ---- 3. draw the new rounded-rect outline (same construction as the
# original: 4 lines + 4 quarter-circle arcs, corner radius == mounting-hole
# inset, same convention already established for this board). -------------
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

# ---- 4. move the 4 mounting holes to the new corners (same inset==radius
# convention as before -- see build_pcb_merge_test.py). --------------------
new_corners = {
    "H1": (NX0 + R, NY0 + R),
    "H2": (NX1 - R, NY0 + R),
    "H3": (NX0 + R, NY1 - R),
    "H4": (NX1 - R, NY1 - R),
}
for ref, (cx, cy) in new_corners.items():
    if ref in mounting_holes:
        # mounting holes are symmetric (anchor == center) -- SetPosition
        # directly rather than going through a bbox-based anchor_offset,
        # which misbehaves on this footprint type in this KiCad build
        # (GetBoundingBox() returns an untyped SwigPyObject for it
        # specifically, not a normal BOX2I).
        mounting_holes[ref].SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"wrote {BOARD_PATH}")
print(f"board resized to {NW:.1f} x {NH:.1f} mm")
