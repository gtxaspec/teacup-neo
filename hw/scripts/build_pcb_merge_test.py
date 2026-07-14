"""TEST-ONLY PCB attempt: reshape the teacup-neo carrier's rough placement to
read as a family member of TeaCup(C)3.3 (the older monolithic T31 board at
/mnt/c/Users/Administrator/Documents/GitHub/Teacup/TeaCup(C)3.3/), per explicit
user direction on 2026-07-13: "make teacup neo as similar to the 3.3 as
possible -- similar mounting holes, similar layout" -- as an attempt in a NEW
test board file, not touching the real teacup-carrier.kicad_pcb.

Adopted from 3.3 (measured directly off its .kicad_pcb, not guessed):
  - MountingHole:MountingHole_2.7mm_M2.5_Pad_Via footprint, 4 corners.
  - Rounded-rectangle outline, 3.1mm corner radius -- and on 3.3 each mounting
    hole sits EXACTLY at its corner's arc center (3.1mm inset from both
    edges), which is reused here so hole and corner share one constant.
  - The relative edge-hugging arrangement of the physical I/O connectors
    that exist on both boards (FPC camera + USB-A on the left edge, USB-C(s)
    + DC jack + audio jack along the bottom edge, microSD on the right edge)
    -- proportionally translated from 3.3's actual coordinates, not just
    eyeballed, then adapted for neo's larger connector set (2 FPCs, 2 USB-C
    vs 3.3's 1 each).

NOT attempted (per user direction, "no target size -- size it to fit"):
  matching 3.3's absolute 86.2x56.2mm footprint or its exact 80x50mm hole
  span. J1 (DDR4 UDIMM-288 socket) alone is ~152.5x15.6mm -- wider than the
  whole of 3.3 -- so neo's board is necessarily much bigger. Mounting holes
  reuse 3.3's footprint/corner-radius STYLE at new corner positions, per
  user's "same style only, free repositioning" answer.

J20-J35 (the ~180-signal bring-up breakout headers, no 3.3 equivalent) are
kept but corralled into one dedicated top strip, clearly a separate
"bring-up only" zone a production variant would drop -- per explicit user
direction, not auto-derived.

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 build_pcb_merge_test.py
"""
import re

import pcbnew

REPO = "/home/administrator/projects/teacup-neo"
HW = f"{REPO}/hw"
NETLIST = "/tmp/teacup-carrier.net"
CONNECTIONS = f"{HW}/CONNECTIONS.txt"
OUT = f"{HW}/teacup-carrier-merge-test.kicad_pcb"  # NEW file -- real board untouched

# ---------------------------------------------------------------- fp-lib-table
def parse_fp_lib_table(path):
    text = open(path).read()
    libs = {}
    for m in re.finditer(r'\(lib \(name "([^"]+)"\)\(type "[^"]*"\)\(uri "([^"]+)"\)', text):
        name, uri = m.group(1), m.group(2)
        uri = uri.replace("${KIPRJMOD}", HW)
        libs[name] = uri
    return libs

LIBS = parse_fp_lib_table(f"{HW}/fp-lib-table")
LIBS.setdefault("Diode_SMD", "/usr/share/kicad/footprints/Diode_SMD.pretty")
# Also missing from fp-lib-table (same class of gap as Diode_SMD, see
# build_pcb.py) -- MountingHole is a stock KiCad library, on disk, just never
# registered in this project's table.
LIBS.setdefault("MountingHole", "/usr/share/kicad/footprints/MountingHole.pretty")

FOOTPRINT_FIXUPS = {
    "Diode_SMD:D_SOD-123W": "Diode_SMD:Nexperia_CFP3_SOD-123W",
    "Package_SO:SOIC-8_5.23x5.23mm_P1.27mm": "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
}

# ---------------------------------------------------------------- netlist parsing
def paren_block(t, i):
    depth = 0; instr = False; start = i; n = len(t)
    while i < n:
        c = t[i]
        if c == '"' and t[i-1] != '\\':
            instr = not instr
        elif not instr:
            if c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: return t[start:i+1]
        i += 1
    raise ValueError("unterminated")

def parse_components(text):
    comps = {}
    i = text.find('(components')
    block = paren_block(text, i)
    for m in re.finditer(r'\(comp\s', block):
        cb = paren_block(block, m.start())
        ref_m = re.search(r'\(ref "([^"]+)"\)', cb)
        val_m = re.search(r'\(value "([^"]*)"\)', cb)
        fp_m = re.search(r'\(footprint "([^"]*)"\)', cb)
        if ref_m and fp_m:
            comps[ref_m.group(1)] = {
                "footprint": fp_m.group(1),
                "value": val_m.group(1) if val_m else "",
            }
    return comps

def parse_nets(text):
    nets = {}
    i = text.find('(nets')
    block = paren_block(text, i)
    for m in re.finditer(r'\(net\s', block):
        nb = paren_block(block, m.start())
        name_m = re.search(r'\(name "([^"]*)"\)', nb)
        name = name_m.group(1) if name_m else "?"
        pins = []
        for pm in re.finditer(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', nb):
            pins.append((pm.group(1), pm.group(2)))
        nets[name] = pins
    return nets

net_text = open(NETLIST).read()
components = parse_components(net_text)
nets = parse_nets(net_text)
print(f"parsed {len(components)} components, {len(nets)} nets")

def parse_clusters(path):
    text = open(path).read()
    sections = re.split(r'\n### (.+?)\n-+\n', text)[1:]
    clusters = {}
    for title, body in zip(sections[0::2], sections[1::2]):
        for ref_m in re.finditer(r'^([A-Z]+\d+)\s+\(', body, re.M):
            clusters[ref_m.group(1)] = title
    return clusters

CLUSTERS = parse_clusters(CONNECTIONS)

# ---------------------------------------------------------------- board setup
board = pcbnew.CreateEmptyBoard()
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(4)

def mm(v):
    return pcbnew.FromMM(v)

# Overall size derived bottom-up (see module docstring): J1 alone needs
# ~152.5mm of clear width, plus left/right edge connector columns, plus a
# dedicated top strip for the bring-up headers (now much shorter since the
# J20-J35 double-row conversion -- no longer the 60mm-long single-row THT
# bars that forced the old 280x240 placeholder).
BOARD_W, BOARD_H = 260.0, 360.0
CORNER_R = 3.1  # matches 3.3's corner radius AND its hole-to-edge inset exactly

# Rounded-rectangle outline, 3.1mm corner radius -- same construction 3.3
# uses (4x line + 4x 90-degree arc). Not just cosmetic: with a plain sharp-
# cornered rect, each mounting hole's copper annular ring (which sits AT the
# corner, per 3.3's own hole-inset-equals-corner-radius convention) pokes
# past the board edge -- confirmed by checking bounding boxes after the
# first pass. The round-over is what makes that hole placement valid.
import math
def add_line(x1, y1, x2, y2):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    seg.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(mm(0.1))
    board.Add(seg)

def add_corner_arc(ccx, ccy, start_deg, end_deg):
    # 90-degree arc around corner center (ccx,ccy), radius CORNER_R
    mid_deg = (start_deg + end_deg) / 2
    def pt(deg):
        r = math.radians(deg)
        return ccx + CORNER_R * math.cos(r), ccy + CORNER_R * math.sin(r)
    sx, sy = pt(start_deg)
    mx, my = pt(mid_deg)
    ex, ey = pt(end_deg)
    arc = pcbnew.PCB_SHAPE(board)
    arc.SetShape(pcbnew.SHAPE_T_ARC)
    arc.SetArcGeometry(pcbnew.VECTOR2I(mm(sx), mm(sy)),
                        pcbnew.VECTOR2I(mm(mx), mm(my)),
                        pcbnew.VECTOR2I(mm(ex), mm(ey)))
    arc.SetLayer(pcbnew.Edge_Cuts)
    arc.SetWidth(mm(0.1))
    board.Add(arc)

R = CORNER_R
add_line(R, 0, BOARD_W - R, 0)                      # top
add_line(BOARD_W, R, BOARD_W, BOARD_H - R)          # right
add_line(BOARD_W - R, BOARD_H, R, BOARD_H)          # bottom
add_line(0, BOARD_H - R, 0, R)                      # left
add_corner_arc(BOARD_W - R, R, -90, 0)               # top-right
add_corner_arc(BOARD_W - R, BOARD_H - R, 0, 90)      # bottom-right
add_corner_arc(R, BOARD_H - R, 90, 180)              # bottom-left
add_corner_arc(R, R, 180, 270)                        # top-left

# ---------------------------------------------------------------- footprint loading + placement
def load_fp(fp_id):
    fp_id = FOOTPRINT_FIXUPS.get(fp_id, fp_id)
    lib, name = fp_id.split(":", 1)
    if lib not in LIBS:
        raise ValueError(f"library '{lib}' not in fp-lib-table (and no fixup)")
    fp = pcbnew.FootprintLoad(LIBS[lib], name)
    if fp is None:
        raise ValueError(f"footprint '{name}' not found in {LIBS[lib]}")
    return fp

def bbox_wh(fp):
    bb = fp.GetBoundingBox()
    return pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())

def anchor_offset(fp):
    """(center - anchor) in mm, current orientation -- see build_pcb.py for
    why this matters (a footprint's SetPosition anchor is not always its
    bbox center)."""
    bb = fp.GetBoundingBox()
    anchor = fp.GetPosition()
    center = bb.GetCenter()
    return pcbnew.ToMM(center.x - anchor.x), pcbnew.ToMM(center.y - anchor.y)

def place_center(fp, cx, cy):
    ox, oy = anchor_offset(fp)
    fp.SetPosition(pcbnew.VECTOR2I(mm(cx - ox), mm(cy - oy)))

# ---- real collision avoidance -- tracks every placed footprint's box so
# later placement passes (the radial block placer below) can push a
# candidate position further out until it's actually clear, rather than
# trusting position formulas alone. -----------------------------------
OCCUPIED = []  # list of (x0, y0, x1, y1) in mm
MARGIN = 0.3

def register_occupied(cx, cy, w, h):
    OCCUPIED.append((cx - w / 2 - MARGIN, cy - h / 2 - MARGIN, cx + w / 2 + MARGIN, cy + h / 2 + MARGIN))

def collides(cx, cy, w, h):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    for ox0, oy0, ox1, oy1 in OCCUPIED:
        if x0 < ox1 and x1 > ox0 and y0 < oy1 and y1 > oy0:
            return True
    return False

def resolve_and_register(cx, cy, w, h, push_ux, push_uy, step=1.0, max_steps=200):
    x, y = cx, cy
    steps = 0
    while collides(x, y, w, h) and steps < max_steps:
        x += push_ux * step
        y += push_uy * step
        steps += 1
    register_occupied(x, y, w, h)
    return x, y

def register_fp(fp):
    bb = fp.GetBoundingBox()
    w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
    center = bb.GetCenter()
    register_occupied(pcbnew.ToMM(center.x), pcbnew.ToMM(center.y), w, h)

# ---- 4x mounting holes, 3.3's exact footprint + corner-radius inset -------
MH_FP = "MountingHole:MountingHole_2.7mm_M2.5_Pad_Via"
mounting_holes = {}
for name, (hx, hy) in {
    "H1": (CORNER_R, CORNER_R),
    "H2": (BOARD_W - CORNER_R, CORNER_R),
    "H3": (CORNER_R, BOARD_H - CORNER_R),
    "H4": (BOARD_W - CORNER_R, BOARD_H - CORNER_R),
}.items():
    fp = load_fp(MH_FP)
    fp.SetReference(name)
    fp.SetValue("MountingHole_Pad")
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    place_center(fp, hx, hy)
    board.Add(fp)
    mounting_holes[name] = fp
    register_fp(fp)

# ---- load every schematic-driven footprint (excludes the 4 mounting holes,
# which have no schematic symbol -- they're PCB-only, same as on 3.3) ------
footprints = {}
load_errors = []
for ref, info in sorted(components.items()):
    try:
        fp = load_fp(info["footprint"])
    except Exception as e:
        load_errors.append((ref, info["footprint"], str(e)))
        continue
    fp.SetReference(ref)
    fp.SetValue(info["value"])
    footprints[ref] = fp

# ---- curated edge-hugging placement for the physical I/O connectors that
# exist on both boards, translated from 3.3's own coordinates (see the
# module docstring's fractional-position derivation) rather than eyeballed.
# left edge: FPC cameras (2x, neo only) + USB-A, top to bottom, matching
# 3.3's left-edge order (FPC above USB-A). bottom edge: USB-C(s) + DC jack +
# audio jack, left to right, matching 3.3's bottom-edge order. right edge:
# microSD, matching 3.3's right-edge placement.
EDGE_MARGIN = 14.0  # clearance from board edge to connector body centerline

def place_left_edge(refs_y):
    for ref, y in refs_y:
        fp = footprints[ref]
        fp.SetOrientationDegrees(90)  # cable exits toward the left edge
        w, h = bbox_wh(fp)
        place_center(fp, EDGE_MARGIN, y)

def place_bottom_edge(refs_x):
    for ref, x in refs_x:
        fp = footprints[ref]
        place_center(fp, x, BOARD_H - EDGE_MARGIN)

def place_right_edge(refs_y):
    for ref, y in refs_y:
        fp = footprints[ref]
        fp.SetOrientationDegrees(90)
        place_center(fp, BOARD_W - EDGE_MARGIN, y)

HEADER_STRIP_H = 58.0  # top "bring-up only" zone, see place_in_box below

# J1 sits centered in the middle band, below the header strip, above the
# bottom-edge connector row -- it needs its own clear lane, not shared with
# anything else (see build_pcb.py for its bbox note: ~152.5x15.6mm).
J1_Y = HEADER_STRIP_H + 45.0

place_left_edge([
    ("J7", HEADER_STRIP_H + 22),   # camera FPC 0 -- upper, mirrors 3.3's J13
    ("J8", HEADER_STRIP_H + 46),   # camera FPC 1 -- neo-only, stacked below J7
    ("J3", BOARD_H - 60),          # USB-A -- lower on the edge, mirrors 3.3's J3
])
place_bottom_edge([
    ("J2", 60),    # USB-C ALT -- mirrors 3.3's single USB-C
    ("J9", 90),    # USB-C BMC -- neo-only, alongside J2
    ("J5", 122),   # DC jack -- mirrors 3.3's J8
    ("J6", 152),   # audio jack -- mirrors 3.3's J10
])
place_right_edge([
    ("J4", HEADER_STRIP_H + 75),   # microSD -- mirrors 3.3's J2
])
CURATED = {"J2", "J3", "J4", "J5", "J6", "J7", "J8", "J9"}
for ref in CURATED:
    if ref in footprints:
        register_fp(footprints[ref])

# ---- J1 (DDR4 UDIMM-288 socket) -- centered, own clear lane ---------------
if "J1" in footprints:
    place_center(footprints["J1"], BOARD_W / 2, J1_Y)
    register_fp(footprints["J1"])

# ---- functional-block placement, replacing the old whole-sheet box-dump --
# 3.3 is not organized by schematic-sheet ("POWER"/"BMC"/etc) at all -- it's
# organized by CIRCUIT: each regulator sits with its own tight column of
# decoupling caps, the SoC sits in a ring of its own load caps + crystal,
# the NOR flash pair sits together with its chip-select header, and every
# connector's own support passives (pull resistors, TVS, bulk caps) sit
# immediately beside that connector -- confirmed by clustering 3.3's actual
# footprint coordinates (4.5mm proximity groups), not assumed. Replicated
# here as named blocks (real net-membership, read off CONNECTIONS.txt, not
# guessed) positioned in the same LEFT/RIGHT/CENTER relationship 3.3 uses:
# regulators upper-right, SoC/BMC-equivalent center-left, NOR-flash-and-
# support lower-right, each curated connector's passives right beside it.
BLOCKS = {
    # ---- POWER sheet, split by which regulator/circuit each part serves --
    "VCORE": ["U1", "L1", "C3", "C4", "C5", "C9", "C10", "R1", "R2",
              "R27", "R28", "R29", "R30", "R31", "R32", "R33", "R34",
              "JP2", "JP3", "JP4", "JP5", "JP6"],
    "VDDR": ["U2", "L2", "C7", "C11", "R3",
             "R35", "R36", "R37", "R38", "R39", "R40",
             "JP7", "JP8", "JP9", "JP10"],
    "P3V3_BUCK": ["U7", "L3", "C17", "C18", "R5", "R6", "R7"],
    "ALWAYS_LDO": ["U5", "C14", "C15"],
    "V1V8_LDO": ["U6", "C20", "C12", "C19"],
    "DIGIPOT": ["U3", "R25", "R26"],
    "LOAD_SWITCHES": ["U4", "U14", "C13", "C23", "D1", "D2",
                       "R20", "R21", "R22", "R23", "R24", "R4",
                       "C1", "C2", "C6", "C16"],
    # ---- BMC sheet, split the same way -- mirrors 3.3's IC1+crystal ring
    # (BMC_CORE), its S1/S2 switches (BMC_SWITCHES), and its NOR-flash-pair
    # block (NOR_FLASH) ----
    "BMC_CORE": ["U8", "C21", "C22", "R8", "R9", "R41", "R42"],
    "BMC_SWITCHES": ["SW1", "SW2", "R10", "R11"],
    "NOR_FLASH": ["U9", "U10", "U11", "U13", "C24"],
    "EXPANDER": ["U12", "U15", "C25", "C26"],
    # ---- CARRIER I/O passives, one small block per curated connector,
    # placed beside that connector below rather than lumped together ----
    "IO_J2": ["R12", "R13"],
    "IO_J9": ["R18", "R19", "C27"],
    "IO_J5": ["R14", "C29"],
    "IO_POWER_OR": ["Q1", "Q2", "R15", "R16", "R17", "C28"],
    "IO_J7": ["JP11"],
    "IO_J8": ["JP12"],
}
BLOCKED_REFS = {r for refs in BLOCKS.values() for r in refs}

placed_positions = {}
GAP = 3.0  # tight, matching 3.3's own dense decoupling-cap spacing

# ---- radial placement: satellites land next to the SPECIFIC anchor pad
# they actually connect to (via the real netlist), not just stacked in a
# box -- this is what was missing before: 3.3's decoupling caps sit right
# at the pin they bypass, fanned around the IC, not lined up in a column
# with no relationship to which pin is which. ---------------------------
REF_NETS = {}       # ref -> set(netnames touching any of its pins)
REF_PIN_NET = {}    # ref -> {pin: netname}
for netname, pins in nets.items():
    for r, p in pins:
        REF_NETS.setdefault(r, set()).add(netname)
        REF_PIN_NET.setdefault(r, {})[p] = netname

def get_pad_positions_mm(fp):
    return {p.GetNumber(): (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            for p in fp.Pads()}

def place_satellites_around(anchor_ref, cx, cy, satellites, base_r=3.5):
    """cx,cy = anchor's already-placed center (mm). Each satellite is
    placed just outside the specific anchor pad it shares a net with (fanned
    out perpendicular to the anchor->pad direction if several satellites
    share that same pad), falling back to a ring around the anchor center
    if no direct pad match exists."""
    afp = footprints.get(anchor_ref)
    apad_net = REF_PIN_NET.get(anchor_ref, {})
    apads = get_pad_positions_mm(afp) if afp else {}
    aw, ah = bbox_wh(afp) if afp else (3.0, 3.0)
    # radial floor = the anchor's own half-diagonal, so satellites clear its
    # body regardless of exactly where its matched pad sits (a QFN's pad is
    # often only ~1mm from center -- pushing out from the PAD by base_r
    # alone isn't enough clearance from the package body itself, which is
    # what caused the first pass's anchor<->satellite overlaps).
    anchor_half = math.hypot(aw, ah) / 2
    pad_fan = {}
    for i, sref in enumerate(satellites):
        sfp = footprints.get(sref)
        if sfp is None:
            continue
        snets = REF_NETS.get(sref, set())
        target = None
        pkey = None
        for padnum, netname in apad_net.items():
            if netname in snets and padnum in apads:
                target, pkey = apads[padnum], padnum
                break
        if target is None:
            ang0 = (i * 360.0 / max(len(satellites), 1)) * math.pi / 180
            ux, uy = math.cos(ang0), math.sin(ang0)
            pkey = f"_ring{i}"
        else:
            tx, ty = target
            dx, dy = tx - cx, ty - cy
            dist = math.hypot(dx, dy)
            if dist < 0.01:
                ang0 = (hash(sref) % 360) * math.pi / 180
                ux, uy = math.cos(ang0), math.sin(ang0)
            else:
                ux, uy = dx / dist, dy / dist
        px, py = -uy, ux
        n = pad_fan.get(pkey, 0)
        pad_fan[pkey] = n + 1
        w, h = bbox_wh(sfp)
        r = anchor_half + base_r + max(w, h) / 2
        fan_offset = ((n + 1) // 2) * (max(w, h) + 1.5) * (1 if n % 2 == 0 else -1)
        nx, ny = cx + ux * r + px * fan_offset, cy + uy * r + py * fan_offset
        # push further out along the same ray until clear of anything already
        # placed (same-anchor satellites that share a node with EACH OTHER
        # but not the anchor -- e.g. a feedback-divider pair -- both fall
        # back to the ring and can land close enough in angle to still
        # collide; this is the actual fix for that, not more formula-tuning)
        nx, ny = resolve_and_register(nx, ny, w, h, ux, uy)
        ox, oy = anchor_offset(sfp)
        sfp.SetPosition(pcbnew.VECTOR2I(mm(nx - ox), mm(ny - oy)))
        placed_positions[sref] = (nx, ny)

def place_anchor(ref, cx, cy):
    fp = footprints[ref]
    place_center(fp, cx, cy)
    w, h = bbox_wh(fp)
    register_occupied(cx, cy, w, h)
    placed_positions[ref] = (cx, cy)

# Single-anchor groups: (anchor_ref, satellites, (cx, cy)). Centers keep the
# same LEFT/RIGHT/CENTER floorplan relationship as before (regulators
# upper-right of the body, BMC/NOR center-left) -- see prior box layout,
# now used as anchor points instead of box corners.
BODY_TOP = J1_Y + 25
SINGLE_ANCHOR_GROUPS = [
    ("U1", BLOCKS["VCORE"][1:], (168, BODY_TOP + 60)),
    ("U2", BLOCKS["VDDR"][1:], (200, BODY_TOP + 60)),
    ("U7", BLOCKS["P3V3_BUCK"][1:], (223, BODY_TOP + 25)),
    ("U5", BLOCKS["ALWAYS_LDO"][1:], (223, BODY_TOP + 75)),
    ("U6", BLOCKS["V1V8_LDO"][1:], (221, BODY_TOP + 105)),
    ("U3", BLOCKS["DIGIPOT"][1:], (223, BODY_TOP + 138)),
    ("U8", BLOCKS["BMC_CORE"][1:], (55, BODY_TOP + 25)),
]
# Multi-anchor groups: block's ICs paired with their OWN directly net-
# connected satellites (verified via CONNECTIONS.txt, e.g. U9 shares
# NOR_U4_CE with U13, U10 shares NOR_U5_CE with U11), plus a small leftover
# "shared" group (bulk caps common to both halves) placed at the midpoint.
MULTI_ANCHOR_GROUPS = [
    # (anchors: [(ref, satellites, (cx,cy)), ...], shared_refs, shared_center)
    ([("U4", ["C13", "R20", "R21", "R4", "D1"], (150, BODY_TOP + 172)),
      ("U14", ["C23", "R22", "R23", "R24", "D2"], (185, BODY_TOP + 172))],
     ["C1", "C2", "C6", "C16"], (167, BODY_TOP + 185)),
    ([("SW1", ["R10", "R11"], (35, BODY_TOP + 75)),
      ("SW2", [], (55, BODY_TOP + 75))],
     [], None),
    ([("U13", ["U9", "C24"], (100, BODY_TOP + 15)),
      ("U11", ["U10"], (130, BODY_TOP + 15))],
     [], None),
    ([("U15", ["C25", "C26"], (100, BODY_TOP + 65)),
      ("U12", [], (125, BODY_TOP + 65))],
     [], None),
    ([("Q1", ["R15"], (140, BODY_TOP + 186)),
      ("Q2", ["R16", "R17"], (160, BODY_TOP + 186))],
     ["C28"], (150, BODY_TOP + 196)),
]
# IO_* groups: anchor is an already-placed EXTERNAL connector (curated
# above), not something placed here -- satellites fan out around its real
# pad positions the same way.
IO_ANCHOR_GROUPS = [
    ("J2", BLOCKS["IO_J2"]),
    ("J9", BLOCKS["IO_J9"]),
    ("J5", BLOCKS["IO_J5"]),
    ("J7", BLOCKS["IO_J7"]),
    ("J8", BLOCKS["IO_J8"]),
]

for ref, fp in footprints.items():
    if ref == "J1" or ref in CURATED:
        placed_positions[ref] = (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))

# Pass 1: place + register EVERY anchor first (single- and multi-anchor
# groups alike) before radiating any satellites. Doing satellites group-by-
# group interleaved with anchor placement was the actual bug behind the
# last few overlaps: a satellite could get pushed clear of every anchor
# placed SO FAR, but not one placed a moment later (e.g. SW1's satellites
# radiating before SW2 -- its own group-mate -- had even been placed).
for anchor_ref, satellites, (cx, cy) in SINGLE_ANCHOR_GROUPS:
    place_anchor(anchor_ref, cx, cy)
for anchors, shared, shared_center in MULTI_ANCHOR_GROUPS:
    for anchor_ref, satellites, (cx, cy) in anchors:
        place_anchor(anchor_ref, cx, cy)

# Pass 2: now radiate every satellite, with every anchor on the board
# already registered as an obstacle.
for anchor_ref, satellites, (cx, cy) in SINGLE_ANCHOR_GROUPS:
    place_satellites_around(anchor_ref, cx, cy, satellites)
for anchors, shared, shared_center in MULTI_ANCHOR_GROUPS:
    for anchor_ref, satellites, (cx, cy) in anchors:
        place_satellites_around(anchor_ref, cx, cy, satellites)
    if shared:
        scx, scy = shared_center
        box = (scx - 10, scy - 6, 20, 12)
        cur = (box[0], box[1], 0.0, 0.0)
        for sref in shared:
            sfp = footprints[sref]
            bb = sfp.GetBoundingBox()
            anchor_pos = sfp.GetPosition()
            center = bb.GetCenter()
            ox = pcbnew.ToMM(center.x - anchor_pos.x)
            oy = pcbnew.ToMM(center.y - anchor_pos.y)
            w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
            bx, by, bw, bh = box
            x, y, row_h, col_w = cur
            if y + h > by + bh:
                x += col_w + GAP; y = by; row_h = 0; col_w = 0
            tcx, tcy = x + w / 2, y + h / 2
            # this simple cursor-fill (unlike the radial placer) doesn't know
            # about anything already on the board -- push straight down
            # until clear rather than trusting the cursor alone.
            tcx, tcy = resolve_and_register(tcx, tcy, w, h, 0.0, 1.0)
            sfp.SetPosition(pcbnew.VECTOR2I(mm(tcx - ox), mm(tcy - oy)))
            placed_positions[sref] = (tcx, tcy)
            cur = (x, y + h + GAP, max(row_h, h), max(col_w, w))

for anchor_ref, satellites in IO_ANCHOR_GROUPS:
    acx, acy = placed_positions[anchor_ref]
    place_satellites_around(anchor_ref, acx, acy, satellites, base_r=6.0)

# IO_POWER_OR is a multi-anchor group with no external connector -- handled
# above via MULTI_ANCHOR_GROUPS already (Q1/Q2 entry).

# Headers keep the old whole-sheet box-fill -- they're not a "circuit
# block" in 3.3's sense (no 3.3 equivalent beyond "breakout headers along
# the top edge", already matched), just corralled bring-up-only real estate.
HEADERS_BOX = (10, 8, BOARD_W - 20, HEADER_STRIP_H - 12)
headers_cursor = (HEADERS_BOX[0], HEADERS_BOX[1], 0.0, 0.0)
def place_in_box(ref, fp, box, cursor):
    bb0 = fp.GetBoundingBox()
    if pcbnew.ToMM(bb0.GetHeight()) > 30 and pcbnew.ToMM(bb0.GetWidth()) < pcbnew.ToMM(bb0.GetHeight()):
        fp.SetOrientationDegrees(90)
    bb = fp.GetBoundingBox()
    anchor = fp.GetPosition()
    center = bb.GetCenter()
    offset_x = pcbnew.ToMM(center.x - anchor.x)
    offset_y = pcbnew.ToMM(center.y - anchor.y)
    w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
    bx, by, bw, bh = box
    x, y, row_h, col_w = cursor
    if y + h > by + bh:
        x += col_w + GAP; y = by; row_h = 0; col_w = 0
    if x + w > bx + bw:
        print(f"WARNING: {ref} ({w:.1f}x{h:.1f}mm) doesn't fit in its box "
              f"({bw}x{bh}mm) even in a fresh column -- placed anyway, will overlap")
    target_cx, target_cy = x + w / 2, y + h / 2
    fp.SetPosition(pcbnew.VECTOR2I(mm(target_cx - offset_x), mm(target_cy - offset_y)))
    return (x, y + h + GAP, max(row_h, h), max(col_w, w))

# Bus-name silkscreen label for each breakout header -- short form of the
# same cluster titles already used in headers.kicad_sch (build_headers.py's
# CLUSTERS/SPARE_CLUSTERS), so the physical board reads the same way the
# schematic does instead of just bare ref designators. Per explicit user
# direction, 2026-07-13.
HEADER_LABELS = {
    "J20": "GMAC0", "J21": "GMAC1", "J22": "UART0", "J23": "UART2", "J24": "UART3",
    "J25": "SSI0", "J26": "SSI1", "J27": "PWM", "J28": "SAR-ADC", "J29": "SMB",
    "J30": "GPIO", "J31": "SPARE1", "J32": "SPARE2", "J33": "SPARE3",
    "J34": "SPARE4", "J35": "SPARE5",
}

def add_silk_text(text, x, y, size=1.4):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    board.Add(t)

leftover = []
for ref, fp in footprints.items():
    if ref in placed_positions:
        continue
    if CLUSTERS.get(ref) == "PIN BREAKOUT HEADERS":
        headers_cursor = place_in_box(ref, fp, HEADERS_BOX, headers_cursor)
        bb = fp.GetBoundingBox()
        label_x = pcbnew.ToMM(bb.GetCenter().x)
        label_y = pcbnew.ToMM(bb.GetTop()) - 2.0
        add_silk_text(HEADER_LABELS.get(ref, ref), label_x, label_y)
    else:
        leftover.append(ref)
        fp.SetPosition(pcbnew.VECTOR2I(mm(5), mm(5)))
    placed_positions[ref] = (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))

for ref, fp in footprints.items():
    board.Add(fp)

if leftover:
    print(f"WARNING: {len(leftover)} refs matched no block and no header cluster "
          f"(parked at 5,5): {leftover}")

if load_errors:
    print(f"FOOTPRINT LOAD ERRORS ({len(load_errors)}):")
    for ref, fpid, err in load_errors:
        print(f"  {ref}: {fpid} -- {err}")

# ---------------------------------------------------------------- net assignment
net_assign_errors = []
for netname, pins in nets.items():
    if not pins:
        continue
    ninfo = pcbnew.NETINFO_ITEM(board, netname)
    board.Add(ninfo)
    for ref, pin in pins:
        fp = footprints.get(ref)
        if fp is None:
            continue
        matched = [p for p in fp.Pads() if p.GetNumber() == pin]
        if not matched:
            net_assign_errors.append((ref, pin, netname))
            continue
        for pad in matched:
            pad.SetNet(ninfo)

if net_assign_errors:
    print(f"NET ASSIGNMENT ERRORS ({len(net_assign_errors)}), first 20:")
    for ref, pin, netname in net_assign_errors[:20]:
        print(f"  {ref} pin {pin} -> {netname}: pad not found")

pcbnew.SaveBoard(OUT, board)
print(f"wrote {OUT}")
print(f"board size: {BOARD_W} x {BOARD_H} mm (3.3 for comparison: 86.2 x 56.2 mm)")
print(f"footprints placed: {len(footprints) + 4} / {len(components) + 4} (incl. 4 mounting holes)")
print(f"nets created: {board.GetNetCount()}")
