"""Initial interposer PCB -- rough first-pass placement only, no routing.
Same approach as the carrier's own build_pcb.py: reads the exported
netlist (kicadsexpr) and programmatically builds the board via the
pcbnew Python API, since there's no netlist-to-PCB importer in
kicad-cli. Board outline is NOT drawn separately -- the DIMM-DDR4
footprint's own Edge.Cuts geometry (the real JEDEC UDIMM card outline,
notch + latch cutouts included) IS the board outline once J1 is placed
at the origin.

Run with the real KiCad 10.0.4 install:
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 build_pcb.py
"""
import re
import pcbnew

REPO = "/home/administrator/projects/teacup-neo/hw/interposer"
NETLIST = "/tmp/interposer.net"
OUT = f"{REPO}/teacup-interposer.kicad_pcb"

def parse_fp_lib_table(path, kiprjmod):
    text = open(path).read()
    libs = {}
    for m in re.finditer(r'\(lib \(name "([^"]+)"\)\(type "[^"]*"\)\(uri "([^"]+)"\)', text):
        name, uri = m.group(1), m.group(2)
        uri = uri.replace("${KIPRJMOD}", kiprjmod)
        uri = uri.replace("${KICAD10_FOOTPRINT_DIR}", "/usr/share/kicad/footprints")
        libs[name] = uri
    return libs

LIBS = parse_fp_lib_table(f"{REPO}/fp-lib-table", REPO)

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

# ---------------------------------------------------------------- board setup
board = pcbnew.CreateEmptyBoard()
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(4)  # docs/BUILD.md Phase 2: "1.0 mm board, 4-layer"
ds.SetBoardThickness(pcbnew.FromMM(1.0))

def mm(v):
    return pcbnew.FromMM(v)

def load_fp(fp_id):
    lib, name = fp_id.split(":", 1)
    if lib not in LIBS:
        raise ValueError(f"library '{lib}' not in fp-lib-table")
    fp = pcbnew.FootprintLoad(LIBS[lib], name)
    if fp is None:
        raise ValueError(f"footprint '{name}' not found in {LIBS[lib]}")
    return fp

# J1 (DIMM-DDR4): placed at the origin, unrotated -- its own Edge.Cuts
# geometry becomes the board outline. Real UDIMM card, 133.35 x 31.25mm,
# pad row at y=-0.25 (component area is y ~ -29.75..-2, well clear of
# the top-edge notch/latch cutouts, which only exist near y > -2).
J1_X, J1_Y = 0.0, 0.0

# IC1 (T31ZX QFN89, ~10.25x10.25mm courtyard) centered in the available
# component strip, roughly under the middle of the card.
IC1_X, IC1_Y = 0.0, -16.0

# Local support passives, clustered near IC1 -- rough scatter, not a
# considered layout (matches the carrier's own "rough first pass, user
# refines by hand" convention).
PASSIVE_POS = {
    "Y1": (-25.0, -8.0), "C20": (-20.0, -8.0), "C21": (-15.0, -8.0), "R21": (-10.0, -8.0),
    "R10": (-25.0, -24.0), "R11": (-20.0, -24.0), "C19": (-15.0, -24.0), "C22": (-10.0, -24.0),
    "C37": (15.0, -6.0), "C41": (19.0, -6.0), "C42": (23.0, -6.0), "C43": (27.0, -6.0),
    "C44": (31.0, -6.0), "C45": (35.0, -6.0), "C46": (39.0, -6.0),
    "C25": (15.0, -26.0), "C26": (19.0, -26.0), "C28": (23.0, -26.0), "C30": (27.0, -26.0),
    "C31": (31.0, -26.0), "C32": (35.0, -26.0), "C34": (39.0, -26.0), "C35": (43.0, -26.0),
    "U4": (48.0, -16.0),
    "#PWR91": (10.0, -2.0), "#PWR92": (13.0, -2.0), "#PWR93": (16.0, -2.0), "#PWR94": (19.0, -2.0),
    # Bring-up test points, strung along the far edge (y=-28, well clear of
    # the notch/latch area near the pad row and away from every other
    # cluster) for easy probe access with the module seated.
    "TP1": (-60.0, -27.0), "TP2": (-45.0, -27.0), "TP3": (-30.0, -27.0),
    "TP4": (0.0, -27.0), "TP5": (13.0, -21.0), "TP6": (33.0, -21.0), "TP7": (50.0, -27.0),
}

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
    elif ref == "IC1":
        fp.SetPosition(pcbnew.VECTOR2I(mm(IC1_X), mm(IC1_Y)))
    elif ref in PASSIVE_POS:
        x, y = PASSIVE_POS[ref]
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    else:
        print(f"WARNING: {ref} has no placement rule -- parked at (0,10)")
        fp.SetPosition(pcbnew.VECTOR2I(mm(0), mm(10)))
    board.Add(fp)

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
print(f"footprints placed: {len(footprints)} / {len(components)}")
print(f"nets created: {board.GetNetCount()}")
