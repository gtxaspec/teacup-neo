"""Add a "UART1" silkscreen label above J36, matching the bus-name labels
every other breakout header already has (build_pcb_merge_test.py's
HEADER_LABELS) -- J36 was added later via a separate targeted script
(add_j36_merge_test.py) and never got one. Per explicit user direction,
2026-07-14.

Run with the real KiCad 10.0.4 install (see build_pcb.py for why):
    LD_LIBRARY_PATH=/opt/kicad10/AppDir/shared/lib:/opt/kicad10/AppDir/usr/lib \
        /opt/kicad10/AppDir/bin/python3.11 label_j36_merge_test.py
"""
import pcbnew

BOARD_PATH = "/home/administrator/projects/teacup-neo/hw/teacup-carrier-merge-test.kicad_pcb"


def mm(v):
    return pcbnew.FromMM(v)


board = pcbnew.LoadBoard(BOARD_PATH)

j36 = None
for fp in board.GetFootprints():
    if fp.GetReference() == "J36":
        j36 = fp
        break
if j36 is None:
    raise SystemExit("J36 not found on this board")

bb = j36.GetBoundingBox()
label_x = pcbnew.ToMM(bb.GetCenter().x)
label_y = pcbnew.ToMM(bb.GetTop()) - 2.0

t = pcbnew.PCB_TEXT(board)
t.SetText("UART1")
t.SetPosition(pcbnew.VECTOR2I(mm(label_x), mm(label_y)))
t.SetLayer(pcbnew.F_SilkS)
size = 1.4
t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
t.SetTextThickness(mm(size * 0.15))
board.Add(t)

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"wrote {BOARD_PATH}")
print(f"UART1 label placed at ({label_x:.1f}, {label_y:.1f})")
