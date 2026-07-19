"""DDR4 UDIMM-288 card edge (interposer side) -- connectivity by label,
same convention as the rest of this project. Every one of the 288
fingers gets a global label matching pinout_288.csv's carrier_net column
verbatim, so it ties to the same-named net wherever it's used on the
SoC sheet (soc.kicad_sch) -- and, on the real board, to the matching
net on the carrier's own J1 socket. Fingers this particular SoC doesn't
drive (MIPI1_*, GMAC1_*, UART3_*, PWM4-7, GPIO1-15, and the handful of
genuine pin-sharing conflicts resolved in favor of something else) get
their label placed same as any other -- they just have nothing else on
this sheet to connect to, which is the intended "unstuffed" state.
Per explicit user direction, 2026-07-18.
"""
import sys, uuid, csv
sys.path.insert(0, '.')
from schgen import Sheet, GRID

TI = "/home/administrator/projects/teacup-neo/hw/interposer/teacup-interposer.kicad_sym"
PWR = "/usr/share/kicad/symbols/power.kicad_sym"
PINOUT_CSV = "/home/administrator/projects/teacup-neo/hw/interposer/pinout_288.csv"

def S(n):
    return round(n * GRID, 2)

s = Sheet()
s.ensure_symbol(TI, "DIMM-DDR4", "teacup-interposer:DIMM-DDR4")
s.ensure_symbol(PWR, "GND", "power:GND")

LABEL_ANGLE = {"right": 0, "left": 180, "up": 90, "down": 270}

J1 = "teacup-interposer:DIMM-DDR4"
jx, jy = S(80), S(400)
s.place(J1, "J1", "DIMM-DDR4", jx, jy, 0,
        footprint="teacup-interposer:DIMM-DDR4",
        ref_at=(jx, jy - S(155), 0), value_at=(jx, jy + S(155), 0))

rows = list(csv.DictReader(open(PINOUT_CSV)))
assert len(rows) == 288

for row in rows:
    num = row["finger"]
    net = row["carrier_net"]
    p = s.pin_pos(J1, jx, jy, 0, num)
    d = s.pin_dir(J1, num)
    if net == "GND":
        s.flag("GND", p, "D", d)
    else:
        s.label(net, p[0], p[1], LABEL_ANGLE[d], global_=True)

out = s.render("DDR4 UDIMM-288 Card Edge (interposer)", str(uuid.uuid4()), "/d2e3f4a5-0001-4000-8000-000000000001", "2", paper="A2")
open("/home/administrator/projects/teacup-neo/hw/interposer/sheets/ddr4_edge.kicad_sch", "w").write(out)
print("wrote ddr4_edge.kicad_sch,", len(out), "bytes")
