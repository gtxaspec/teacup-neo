"""Add the new J36 (UART1 console breakout) footprint to the merge-test
board -- schematic-only until now (build_headers.py). Placed next to
J22/J23/J24 (the other UART breakout headers), same footprint/orientation,
nothing else on the board touched. Per explicit user direction, 2026-07-14.

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 add_j36_merge_test.py
"""
import re
import pcbnew

HW = "/home/administrator/projects/teacup-neo/hw"
BOARD_PATH = f"{HW}/teacup-carrier-merge-test.kicad_pcb"


def mm(v):
    return pcbnew.FromMM(v)


def parse_fp_lib_table(path):
    text = open(path).read()
    libs = {}
    for m in re.finditer(r'\(lib \(name "([^"]+)"\)\(type "[^"]*"\)\(uri "([^"]+)"\)', text):
        name, uri = m.group(1), m.group(2)
        libs[name] = uri.replace("${KIPRJMOD}", HW)
    return libs


LIBS = parse_fp_lib_table(f"{HW}/fp-lib-table")

board = pcbnew.LoadBoard(BOARD_PATH)
if any(fp.GetReference() == "J36" for fp in board.GetFootprints()):
    raise SystemExit("J36 already on this board -- not adding a duplicate")

fp = pcbnew.FootprintLoad(LIBS["Connector_PinHeader_2.54mm"], "PinHeader_1x03_P2.54mm_Vertical")
fp.SetReference("J36")
fp.SetValue("HDR_J36")

# place just above J24 (the topmost of the existing UART headers), same x
# and rotation, continuing their 7mm spacing.
fp.SetOrientationDegrees(90)
fp.SetPosition(pcbnew.VECTOR2I(mm(206.9), mm(75.0)))
board.Add(fp)

pin_to_net = {"1": "GND", "2": "UART1_RX", "3": "UART1_TX"}
for pad in fp.Pads():
    netname = pin_to_net.get(pad.GetNumber())
    if netname is None:
        continue
    ninfo = None
    for other_fp in board.GetFootprints():
        for other_pad in other_fp.Pads():
            if other_pad.GetNetname() == netname:
                ninfo = other_pad.GetNet()
                break
        if ninfo is not None:
            break
    if ninfo is None:
        print(f"WARNING: no existing pad found on net {netname} to copy net info from")
        continue
    pad.SetNet(ninfo)

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"wrote {BOARD_PATH}")
for pad in fp.Pads():
    print(" pad", pad.GetNumber(), "->", pad.GetNetname())
