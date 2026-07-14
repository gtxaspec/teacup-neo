"""Swap SW2 pad 1 / pad 4 net assignments on the merge-test PCB to match the
schematic change (build_bmc.py): pin1 now EN_SW_ALT, pin4 now EN_SW_BMC.
Position/rotation untouched -- this only fixes the two pads' copper net
assignment so the board matches the corrected schematic. Per explicit user
direction, 2026-07-14.

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 swap_sw2_pins_merge_test.py
"""
import pcbnew

BOARD_PATH = "/home/administrator/projects/teacup-neo/hw/teacup-carrier-merge-test.kicad_pcb"

board = pcbnew.LoadBoard(BOARD_PATH)

sw2 = None
for fp in board.GetFootprints():
    if fp.GetReference() == "SW2":
        sw2 = fp
        break
if sw2 is None:
    raise SystemExit("SW2 not found on this board")

pad1 = pad4 = None
for pad in sw2.Pads():
    if pad.GetNumber() == "1":
        pad1 = pad
    elif pad.GetNumber() == "4":
        pad4 = pad
if pad1 is None or pad4 is None:
    raise SystemExit("SW2 pad 1 or pad 4 not found")

print(f"before: pad1={pad1.GetNetname()}  pad4={pad4.GetNetname()}")
net1, net4 = pad1.GetNet(), pad4.GetNet()
pad1.SetNet(net4)
pad4.SetNet(net1)
print(f"after:  pad1={pad1.GetNetname()}  pad4={pad4.GetNetname()}")

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"wrote {BOARD_PATH}")
