"""Tidy the off-board 'staging pile' on the merge-test board into a neat,
grouped grid -- per explicit user direction on 2026-07-14: "sort and
organize the components that are off the right side of the board," scoped
to tidying THAT pile in place, not placing it onto the actual board (that
stays the user's own manual work).

108 of 134 footprints are currently sitting to the right of the board
outline (x > BOARD_W) -- everything except J1, the mounting holes, the
breakout headers, J6/J7/J8, and JP11/JP12. This groups them by the same
device+its-passives relationships used throughout this session (real
netlist membership, not guessed) and lays each group out as a small tidy
row, then stacks the rows into columns across the staging area. On-board
footprints are read for reference (nothing on-board is moved).

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 tidy_offboard_merge_test.py
"""
import pcbnew

HW = "/home/administrator/projects/teacup-neo/hw"
BOARD_PATH = f"{HW}/teacup-carrier-merge-test.kicad_pcb"
BOARD_W = 260.0


def mm(v):
    return pcbnew.FromMM(v)


def bbox_wh(fp):
    bb = fp.GetBoundingBox()
    return pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())


def anchor_offset(fp):
    bb = fp.GetBoundingBox()
    anchor = fp.GetPosition()
    center = bb.GetCenter()
    return pcbnew.ToMM(center.x - anchor.x), pcbnew.ToMM(center.y - anchor.y)


def place_center(fp, cx, cy):
    ox, oy = anchor_offset(fp)
    fp.SetPosition(pcbnew.VECTOR2I(mm(cx - ox), mm(cy - oy)))


board = pcbnew.LoadBoard(BOARD_PATH)
footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}

offboard = set()
for ref, fp in footprints.items():
    bb = fp.GetBoundingBox()
    if pcbnew.ToMM(bb.GetRight()) > BOARD_W:
        offboard.add(ref)

# Same device -> its-passives membership used in reflow_passives_merge_test.py
# (real netlist-derived groupings, not guessed) -- reused here purely as a
# GROUPING key (who belongs with whom), not for radial pin-matching, since
# this is a tidy-the-pile pass, not a final-placement pass.
GROUPS_RAW = {
    "U1": ["L1", "C3", "C4", "C5", "C9", "C10", "R1", "R2",
           "R27", "R28", "R29", "R30", "R31", "R32", "R33", "R34",
           "JP2", "JP3", "JP4", "JP5", "JP6"],
    "U2": ["L2", "C7", "C11", "R3",
           "R35", "R36", "R37", "R38", "R39", "R40",
           "JP7", "JP8", "JP9", "JP10"],
    "U7": ["L3", "C17", "C18", "R5", "R6", "R7"],
    "U5": ["C14", "C15"],
    "U6": ["C20", "C12", "C19"],
    "U3": ["R25", "R26"],
    "U4": ["C13", "R20", "R21", "R4", "D1", "C1", "C2", "C6", "C16"],
    "U14": ["C23", "R22", "R23", "R24", "D2"],
    "U8": ["C21", "C22", "R8", "R9", "R41", "R42"],
    "SW1": ["R10", "R11"],
    "SW2": [],
    "U13": ["U9", "C24"],
    "U11": ["U10"],
    "U15": ["C25", "C26"],
    "U12": [],
    "J2": ["R12", "R13"],
    "J9": ["R18", "R19", "C27"],
    "J5": ["R14", "C29"],
    "J3": [],
    "J4": [],
    "Q1": ["R15"],
    "Q2": ["R16", "R17", "C28"],
}

grouped_refs = set()
groups = []  # list of [ref, ...], anchor first
for anchor, members in GROUPS_RAW.items():
    row = [r for r in [anchor] + members if r in offboard]
    if row:
        groups.append(row)
        grouped_refs.update(row)

# any off-board ref not covered above (shouldn't be many, but don't silently
# drop anything) becomes its own singleton group.
leftover = sorted(offboard - grouped_refs)
for ref in leftover:
    groups.append([ref])
if leftover:
    print(f"note: {len(leftover)} off-board refs had no defined group, "
          f"placed as singletons: {leftover}")

# ---- lay out: each group as one tidy horizontal row (anchor then its
# members left to right), rows stacked into columns of a fixed height
# across the staging area starting just right of the board edge. ----------
STAGE_X0 = BOARD_W + 15.0
STAGE_Y0 = 10.0
COL_HEIGHT = 340.0
ROW_GAP = 4.0
ITEM_GAP = 2.0
COL_GAP = 8.0

cx, cy = STAGE_X0, STAGE_Y0
col_w = 0.0
for row in groups:
    # measure row height/width first
    row_h = 0.0
    sizes = []
    for ref in row:
        w, h = bbox_wh(footprints[ref])
        sizes.append((w, h))
        row_h = max(row_h, h)
    if cy + row_h > STAGE_Y0 + COL_HEIGHT:
        cx += col_w + COL_GAP
        cy = STAGE_Y0
        col_w = 0.0
    x = cx
    for ref, (w, h) in zip(row, sizes):
        place_center(footprints[ref], x + w / 2, cy + row_h / 2)
        x += w + ITEM_GAP
    col_w = max(col_w, x - cx - ITEM_GAP)
    cy += row_h + ROW_GAP

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"wrote {BOARD_PATH}")
print(f"tidied {len(offboard)} off-board footprints into {len(groups)} groups; "
      f"on-board footprints untouched")
