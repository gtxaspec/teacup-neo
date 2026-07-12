"""Initial PCB board file -- rough first-pass placement only, no routing.

Reads the schematic netlist (kicadsexpr format) and hw/fp-lib-table to
programmatically build teacup-carrier.kicad_pcb via the pcbnew Python API
(there is no netlist-to-PCB importer in kicad-cli -- "Update PCB from
Schematic" is GUI-only). Component clustering (POWER/CONNECTOR/BMC/IO/
HEADERS) is read directly from CONNECTIONS.txt's own section headers,
which are ground truth for which sheet each ref came from -- more
reliable than guessing from ref-number ranges.

Run with the real KiCad 10.0.4 install (the stray 9.0.8 kicad-cli in
/usr/bin does not match what's installed):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 build_pcb.py

KNOWN SCHEMATIC BUG (not fixed here -- out of scope, flagged for the
schematic side): build_power.py hardcodes D1/D2's footprint as
"Diode_SMD:D_SOD-123W", which does not exist in any installed KiCad
library (checked). PMEG2010ER is a Nexperia part in a real SOD-123W
package, and the actual matching footprint is
"Diode_SMD:Nexperia_CFP3_SOD-123W" -- used here as a placement-only
substitute so the PCB can be built at all. The schematic's own footprint
field should be corrected to match (and "Diode_SMD" added to
hw/fp-lib-table, which doesn't list it either) independently of this PCB
work.
"""
import re, os

import pcbnew

REPO = "/home/administrator/projects/teacup-neo"
HW = f"{REPO}/hw"
NETLIST = "/tmp/teacup-carrier.net"
CONNECTIONS = f"{HW}/CONNECTIONS.txt"
OUT = f"{HW}/teacup-carrier.kicad_pcb"

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
# Diode_SMD is on disk (standard KiCad install) but was never added to this
# project's fp-lib-table -- confirmed missing, not a typo on my part.
LIBS.setdefault("Diode_SMD", "/usr/share/kicad/footprints/Diode_SMD.pretty")

# The schematic's own D_SOD-123W string doesn't exist in any library
# (checked exhaustively under /usr/share/kicad/footprints). Substitute the
# real Nexperia SOD-123W footprint for PMEG2010ER (a real Nexperia part) --
# see module docstring. Same underlying bug class for U13: the schematic's
# "5.23x5.23mm" SOIC-8 string doesn't exist in the standard library, which
# rounds to one decimal ("5.3x5.3mm") -- same real package, just a
# formatting mismatch against KiCad's naming convention.
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
    comps = {}  # ref -> dict(footprint, value)
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
    nets = {}  # net name -> [(ref, pin), ...]
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

# ---------------------------------------------------------------- cluster from CONNECTIONS.txt
def parse_clusters(path):
    text = open(path).read()
    sections = re.split(r'\n### (.+?)\n-+\n', text)[1:]  # [title, body, title, body, ...]
    clusters = {}  # ref -> section title
    for title, body in zip(sections[0::2], sections[1::2]):
        for ref_m in re.finditer(r'^([A-Z]+\d+)\s+\(', body, re.M):
            clusters[ref_m.group(1)] = title
    return clusters

CLUSTERS = parse_clusters(CONNECTIONS)
missing_cluster = [r for r in components if r not in CLUSTERS]
if missing_cluster:
    print("WARNING: refs with no cluster assignment (placed at origin fallback):", missing_cluster)

# ---------------------------------------------------------------- board setup
board = pcbnew.CreateEmptyBoard()
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(4)  # docs/UNIVERSAL.md SS1: "4-layer carrier suffices"

def mm(v):
    return pcbnew.FromMM(v)

# Placeholder board outline -- NOT a considered mechanical decision, just
# large enough to fit J1 (152.5 x 15.6mm bbox, pads spanning x -69..+69mm
# relative to its own origin) plus every other cluster without cramming.
# Real outline needs actual mechanical/enclosure requirements. Enlarged
# from an initial 210x170 after DRC caught real overlaps: several pin
# headers (J31-J35, up to 25 pins) are ~60mm+ long, which blew straight
# through a too-small header region into J1's own row.
BOARD_W, BOARD_H = 280.0, 240.0
outline = pcbnew.PCB_SHAPE(board)
outline.SetShape(pcbnew.SHAPE_T_RECT)
outline.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
outline.SetEnd(pcbnew.VECTOR2I(mm(BOARD_W), mm(BOARD_H)))
outline.SetLayer(pcbnew.Edge_Cuts)
outline.SetWidth(mm(0.15))
board.Add(outline)

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

# J1: DDR4 UDIMM-288 socket, the board's central mechanical feature -- long
# edge connector, placed along the bottom edge, centered horizontally.
# Its own origin is at the pad-array center (pads span x -69..+69, y
# -2.3..+2.3 relative to placement point), so placing it at
# (BOARD_W/2, BOARD_H - 15) puts the pad row well clear of the board's
# bottom edge -- reasonable clearance for a connector this size.
J1_X, J1_Y = BOARD_W / 2, BOARD_H - 15.0

# Cluster placement regions (rough boxes to scatter components into, NOT
# final placement -- user refines by hand per the project's established
# preference for manual layout). Headers gets a full-width strip just
# above J1: several of J20-J35 are single-row THT headers up to 25 pins
# (~60mm long) -- far too tall to fit standing up in a modest box, so
# they're rotated 90 degrees (see place_in_box) to lie flat and need
# width, not height, which this strip provides.
CLUSTER_BOXES = {
    "POWER": (10, 10, 130, 90),                     # upper-left: bucks, digipot, voltage-select jumpers
    "BMC - ESP32-S3": (145, 10, 130, 90),            # upper-right: ESP32 + support chips
    "CARRIER PHYSICAL I/O": (10, 105, 100, 95),      # left, above J1: user-facing I/O
    "PIN BREAKOUT HEADERS": (115, 105, 155, 95),     # right, above J1: header banks (rotated flat)
}

placed_positions = {}  # ref -> (x, y) mm, for net-assignment bookkeeping only

GAP = 5.0  # mm between adjacent footprints -- generous margin for a rough pass.
def place_in_box(ref, fp, box, cursor):
    # Long single-row THT headers (up to 25 pins, ~60mm) get rotated flat
    # (90 degrees) before measuring their bbox -- standing up, one alone
    # could blow through an entire cluster box and overlap a neighboring
    # cluster.
    bb0 = fp.GetBoundingBox()
    if pcbnew.ToMM(bb0.GetHeight()) > 30 and pcbnew.ToMM(bb0.GetWidth()) < pcbnew.ToMM(bb0.GetHeight()):
        fp.SetOrientationDegrees(90)

    # Root cause of real DRC overlaps on an earlier pass (J21/J25 pads
    # landing directly in each other's courtyards despite non-overlapping
    # bbox math): a footprint's anchor (what SetPosition moves) is NOT
    # always its bbox center. PinHeader_1x11's anchor sits at pin 1, ~13mm
    # from its actual bbox center -- naively setting the anchor to the
    # desired bbox-center silently mis-places the real pads by that much.
    # Confirmed via a direct FootprintLoad + GetBoundingBox check before
    # writing this fix, not assumed. Compute the anchor->center offset in
    # the current (possibly just-rotated) orientation and correct for it.
    bb = fp.GetBoundingBox()
    anchor = fp.GetPosition()
    center = bb.GetCenter()
    offset_x = pcbnew.ToMM(center.x - anchor.x)
    offset_y = pcbnew.ToMM(center.y - anchor.y)
    w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())

    bx, by, bw, bh = box
    x, y, row_h, col_w = cursor
    if y + h > by + bh:  # column full -- start a new column
        x += col_w + GAP
        y = by
        row_h = 0
        col_w = 0
    if x + w > bx + bw:
        print(f"WARNING: {ref} ({w:.1f}x{h:.1f}mm) doesn't fit in its cluster box "
              f"({bw}x{bh}mm) even in a fresh column -- placed anyway, will overlap")
    target_cx, target_cy = x + w / 2, y + h / 2
    fp.SetPosition(pcbnew.VECTOR2I(mm(target_cx - offset_x), mm(target_cy - offset_y)))
    row_h = max(row_h, h)
    col_w = max(col_w, w)
    return (x, y + h + GAP, row_h, col_w)

cursors = {name: (box[0], box[1], 0.0, 0.0) for name, box in CLUSTER_BOXES.items()}

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

    if ref == "J1":
        fp.SetPosition(pcbnew.VECTOR2I(mm(J1_X), mm(J1_Y)))
    else:
        cluster = CLUSTERS.get(ref)
        box = CLUSTER_BOXES.get(cluster)
        if box is None:
            print(f"WARNING: {ref} has no matching cluster box (cluster={cluster!r}) -- parked at (5,5)")
            fp.SetPosition(pcbnew.VECTOR2I(mm(5), mm(5)))
        else:
            cursors[cluster] = place_in_box(ref, fp, box, cursors[cluster])
    board.Add(fp)
    placed_positions[ref] = (
        pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
    )

if load_errors:
    print(f"FOOTPRINT LOAD ERRORS ({len(load_errors)}):")
    for ref, fpid, err in load_errors:
        print(f"  {ref}: {fpid} -- {err}")

# ---------------------------------------------------------------- net assignment
net_assign_errors = []
netcode = 1
for netname, pins in nets.items():
    if not pins:
        continue
    ninfo = pcbnew.NETINFO_ITEM(board, netname)
    board.Add(ninfo)
    for ref, pin in pins:
        fp = footprints.get(ref)
        if fp is None:
            continue  # already reported as a load error above
        # Some footprints (WSON-10's ganged VOUT, ESP32-S3-WROOM-1's
        # multi-region GND pad) have MULTIPLE physical pads sharing the
        # same pad number. FindPadByNumber() only returns the first match,
        # leaving the others unassigned (real bug, caught by DRC's
        # "shorting_items": one pad on the intended net, its same-numbered
        # sibling left on no net at all, which DRC correctly flags as two
        # different nets touching). Assign to every matching pad instead.
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
print(f"footprints placed: {len(footprints)} / {len(components)}")
print(f"nets created: {board.GetNetCount()}")
