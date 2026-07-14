"""Reflow ONLY the passive components (R/C/L/D) on the merge-test board to
sit next to the specific device pin they connect to, per the real netlist --
"place the passives near the devices that use them as shown in the
schematic," per explicit user direction on 2026-07-14.

Unlike build_pcb_merge_test.py, this LOADS the existing board rather than
building one from scratch: the user has since done substantial manual
layout (repositioned every IC, connector, and header) and that work must
not be touched. Every device/connector/header/mounting-hole position is
read as-is and used only as a reference point for where to put its
passives -- nothing but R/C/L/D footprints ever gets moved or rotated.

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 reflow_passives_merge_test.py
"""
import re
import math

import pcbnew

HW = "/home/administrator/projects/teacup-neo/hw"
NETLIST = "/tmp/teacup-carrier.net"
BOARD_PATH = f"{HW}/teacup-carrier-merge-test.kicad_pcb"


def mm(v):
    return pcbnew.FromMM(v)


def paren_block(t, i):
    depth = 0; instr = False; start = i; n = len(t)
    while i < n:
        c = t[i]
        if c == '"' and t[i - 1] != '\\':
            instr = not instr
        elif not instr:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return t[start:i + 1]
        i += 1
    raise ValueError("unterminated")


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
nets = parse_nets(net_text)

REF_NETS = {}       # ref -> set(netnames touching any of its pins)
REF_PIN_NET = {}    # ref -> {pin: netname}
for netname, pins in nets.items():
    for r, p in pins:
        REF_NETS.setdefault(r, set()).add(netname)
        REF_PIN_NET.setdefault(r, {})[p] = netname

# ---- same block membership as build_pcb_merge_test.py (real net-derived,
# not guessed) -- see that script for how each was verified against
# CONNECTIONS.txt. Reused as-is; only which MEMBERS actually get MOVED
# changes here (passives only, see PASSIVE_RE filter below). ---------------
BLOCKS_RAW = {
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
    "U4": ["C13", "R20", "R21", "R4", "D1"],
    "U14": ["C23", "R22", "R23", "R24", "D2"],
    "U8": ["C21", "C22", "R8", "R9", "R41", "R42"],
    "SW1": ["R10", "R11"],
    "U13": ["U9", "C24"],
    "U11": ["U10"],
    "U15": ["C25", "C26"],
    "J2": ["R12", "R13"],
    "J9": ["R18", "R19", "C27"],
    "J5": ["R14", "C29"],
    "Q1": ["R15"],
    "Q2": ["R16", "R17"],
    "J7": ["JP11"],
    "J8": ["JP12"],
}
# "Shared" passives with no single anchor (both LOAD_SWITCHES halves, both
# power-OR FETs) -- fanned around the midpoint of their two anchors instead.
SHARED_GROUPS = [
    (["U4", "U14"], ["C1", "C2", "C6", "C16"]),
    (["Q1", "Q2"], ["C28"]),
]

PASSIVE_RE = re.compile(r'^[RCLD]\d+$')

board = pcbnew.LoadBoard(BOARD_PATH)
footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}


def bbox_wh(fp):
    bb = fp.GetBoundingBox()
    return pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())


def anchor_offset(fp):
    bb = fp.GetBoundingBox()
    anchor = fp.GetPosition()
    center = bb.GetCenter()
    return pcbnew.ToMM(center.x - anchor.x), pcbnew.ToMM(center.y - anchor.y)


def get_pad_positions_mm(fp):
    return {p.GetNumber(): (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
            for p in fp.Pads()}


def center_mm(fp):
    bb = fp.GetBoundingBox()
    c = bb.GetCenter()
    return pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)


# ---- collision tracking: EVERY footprint currently on the board (devices,
# connectors, headers, mounting holes -- all untouched user layout) is an
# obstacle from the start. Passives get registered as they're placed so
# later ones avoid earlier ones too. ---------------------------------------
OCCUPIED = []
MARGIN = 0.3


def register_occupied(cx, cy, w, h):
    OCCUPIED.append((cx - w / 2 - MARGIN, cy - h / 2 - MARGIN, cx + w / 2 + MARGIN, cy + h / 2 + MARGIN))


def collides(cx, cy, w, h):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    for ox0, oy0, ox1, oy1 in OCCUPIED:
        if x0 < ox1 and x1 > ox0 and y0 < oy1 and y1 > oy0:
            return True
    return False


def resolve_and_register(cx, cy, w, h, push_ux, push_uy, step=1.0, max_steps=300):
    x, y = cx, cy
    steps = 0
    while collides(x, y, w, h) and steps < max_steps:
        x += push_ux * step
        y += push_uy * step
        steps += 1
    register_occupied(x, y, w, h)
    return x, y


movable_refs = set()
for anchor, members in BLOCKS_RAW.items():
    for m in members:
        if PASSIVE_RE.match(m):
            movable_refs.add(m)
for _, shared in SHARED_GROUPS:
    movable_refs.update(shared)

# register every footprint NOT about to be moved -- i.e. every device,
# connector, header, mounting hole, AND any BLOCKS_RAW member that isn't a
# plain R/C/L/D (JP jumpers, or the odd IC-as-satellite like NOR_FLASH's
# U9/U10) -- exactly as the user left them.
for ref, fp in footprints.items():
    if ref in movable_refs:
        continue
    w, h = bbox_wh(fp)
    cx, cy = center_mm(fp)
    register_occupied(cx, cy, w, h)


def place_satellites_around(anchor_ref, satellites, base_r=3.5):
    afp = footprints.get(anchor_ref)
    if afp is None:
        print(f"WARNING: anchor {anchor_ref} not found on board")
        return
    cx, cy = center_mm(afp)
    apad_net = REF_PIN_NET.get(anchor_ref, {})
    apads = get_pad_positions_mm(afp)
    aw, ah = bbox_wh(afp)
    anchor_half = math.hypot(aw, ah) / 2
    pad_fan = {}
    for i, sref in enumerate(satellites):
        sfp = footprints.get(sref)
        if sfp is None:
            print(f"WARNING: satellite {sref} not found on board (skipped)")
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
        nx, ny = resolve_and_register(nx, ny, w, h, ux, uy)
        ox, oy = anchor_offset(sfp)
        sfp.SetPosition(pcbnew.VECTOR2I(mm(nx - ox), mm(ny - oy)))


for anchor_ref, members in BLOCKS_RAW.items():
    satellites = [m for m in members if PASSIVE_RE.match(m)]
    place_satellites_around(anchor_ref, satellites)

for anchors, shared in SHARED_GROUPS:
    pts = [center_mm(footprints[a]) for a in anchors if a in footprints]
    if not pts:
        continue
    scx = sum(p[0] for p in pts) / len(pts)
    scy = sum(p[1] for p in pts) / len(pts)
    box = (scx - 10, scy - 6, 20, 12)
    cur = (box[0], box[1], 0.0, 0.0)
    GAP = 3.0
    for sref in shared:
        sfp = footprints.get(sref)
        if sfp is None:
            continue
        ox, oy = anchor_offset(sfp)
        w, h = bbox_wh(sfp)
        bx, by, bw, bh = box
        x, y, row_h, col_w = cur
        if y + h > by + bh:
            x += col_w + GAP; y = by; row_h = 0; col_w = 0
        tcx, tcy = x + w / 2, y + h / 2
        tcx, tcy = resolve_and_register(tcx, tcy, w, h, 0.0, 1.0)
        sfp.SetPosition(pcbnew.VECTOR2I(mm(tcx - ox), mm(tcy - oy)))
        cur = (x, y + h + GAP, max(row_h, h), max(col_w, w))

# ---- sanity: did every R/C/L/D on the board get covered by some group? ---
all_passives = {ref for ref in footprints if PASSIVE_RE.match(ref)}
uncovered = all_passives - movable_refs
if uncovered:
    print(f"WARNING: {len(uncovered)} passives matched no block (left untouched): {sorted(uncovered)}")

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"wrote {BOARD_PATH}")
print(f"moved {len(movable_refs)} passives around their devices, everything else untouched")
