"""Add a GND copper pour on both F.Cu and B.Cu, filling the (already
resized -- see resize_merge_test.py, run first) merge-test board's
interior. Per explicit user direction, 2026-07-14.

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 pour_merge_test.py
"""
import pcbnew

BOARD_PATH = "/home/administrator/projects/teacup-neo/hw/teacup-carrier-merge-test.kicad_pcb"
INSET = 0.5  # copper-to-board-edge clearance


def mm(v):
    return pcbnew.FromMM(v)


board = pcbnew.LoadBoard(BOARD_PATH)
ALL_FOOTPRINTS = list(board.GetFootprints())

# remove any existing zones first -- re-running this after a board resize
# would otherwise leave stale zones sized to the OLD outline alongside the
# new ones instead of replacing them.
old_zones = list(board.Zones())
for z in old_zones:
    board.Remove(z)
if old_zones:
    print(f"removed {len(old_zones)} stale zone(s) from a previous run")

# GND net code -- board.GetNetInfo()/FindNet()/GetNetcodeFromNetname() all
# returned an untyped SwigPyObject in this KiCad build (confirmed by trying
# all three); reading it off an existing GND-connected pad works instead.
netcode = None
for fp in ALL_FOOTPRINTS:
    if fp.GetReference() in ("H1", "H2", "H3", "H4"):
        continue  # MountingHole's .Pads() misbehaves the same way its .GetBoundingBox() did
    for pad in fp.Pads():
        if pad.GetNetname() == "GND":
            netcode = pad.GetNetCode()
            break
    if netcode is not None:
        break
if netcode is None:
    raise SystemExit("GND net not found on this board")

# board outline extent, from the Edge.Cuts geometry resize_merge_test.py
# just wrote (min/max over every Edge.Cuts shape's start/mid/end points).
xs, ys = [], []
for shape in board.GetDrawings():
    if not hasattr(shape, "GetLayer") or shape.GetLayer() != pcbnew.Edge_Cuts:
        continue
    for getter in ("GetStart", "GetEnd"):
        if hasattr(shape, getter):
            p = getattr(shape, getter)()
            xs.append(pcbnew.ToMM(p.x)); ys.append(pcbnew.ToMM(p.y))
NX0, NY0, NX1, NY1 = min(xs), min(ys), max(xs), max(ys)
print(f"board outline: ({NX0:.1f},{NY0:.1f}) to ({NX1:.1f},{NY1:.1f})")

zones = []
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNetCode(netcode)
    zone.SetMinThickness(mm(0.2))
    zone.SetLocalClearance(mm(0.3))
    outline = zone.Outline()
    outline.NewOutline()
    zx0, zy0, zx1, zy1 = NX0 + INSET, NY0 + INSET, NX1 - INSET, NY1 - INSET
    outline.Append(mm(zx0), mm(zy0))
    outline.Append(mm(zx1), mm(zy0))
    outline.Append(mm(zx1), mm(zy1))
    outline.Append(mm(zx0), mm(zy1))
    board.Add(zone)
    zones.append(zone)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(zones)

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"wrote {BOARD_PATH}")
print("GND pour added on F.Cu + B.Cu")
