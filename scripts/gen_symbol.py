#!/usr/bin/env python3
"""Generate a KiCad 9 symbol for T41NQ (also fits T41XQ/LQ) from t41nq_pins.csv.
Pins grouped by function onto 4 sides. Appends to hw/teacup.kicad_sym.
"""
import csv, re

CSV = "/home/turismo/projects/teacup-t41/docs/t41nq_pins.csv"
LIB = "/home/turismo/projects/teacup-t41/hw/teacup.kicad_sym"
GRID = 2.54

rows = list(csv.DictReader(open(CSV)))
by_pin = {int(r["pin"]): r for r in rows}

# electrical type per pin
def etype(r):
    g = r["group"]; f = r["functions"]
    if g in ("power_core", "power_io"): return "power_in"
    if g == "ground": return "power_in"
    if f in ("DDRVDD","DDRPLL_VCCA","DDR_VREF","CSI_VCCA18","CODEC_USB_AVDD",
             "SADC_VREFP_AVDD","USB_AVD33","EFUSE_AVDD"): return "power_in"
    if g == "ddr" and f in ("DDR_ZQ","RZQ"): return "passive"
    if g in ("mipi","usb","audio") or f in ("SADC_VIN0",): return "passive"
    if f == "POR_CTL": return "input"
    if f in ("EXCLK_XIN",): return "input"
    if f in ("EXCLK_XOUT",): return "output"
    return "bidirectional"

# assign each pin to a side by group, with per-pin overrides to balance L/R
SIDE = {
  "cis_ctl":"L","sfc":"L","msc0":"L","uart0":"R","uart_ssi0":"L",
  "gmac":"R","pb_misc":"R","pwm":"R","uart1":"R",
  "power_core":"T","power_io":"T","osc":"T","boot":"T","sysctl":"T","otp":"T",
  "mipi":"B","usb":"B","audio":"B","sadc":"B","ddr":"B","ground":"B",
}
# move the PC-bank UART2/SMB1 pins to the right to even out sides
PIN_SIDE = {89:"R", 90:"R", 91:"R", 92:"R"}
sides = {"L":[], "R":[], "T":[], "B":[]}
for p in sorted(by_pin):
    r = by_pin[p]
    sides[PIN_SIDE.get(p, SIDE[r["group"]])].append(p)

def label(r):
    f = r["functions"].split("|")[0]
    gpio = r["gpio"]
    # primary name: prefer dedicated function, annotate gpio
    if gpio and f != gpio:
        return f"{f}/{gpio}" if len(f) <= 14 else gpio
    return gpio or f

# geometry
nL, nR = len(sides["L"]), len(sides["R"])
nT, nB = len(sides["T"]), len(sides["B"])
rows_v = max(nL, nR)
cols_h = max(nT, nB)
# +3 grid margin so L/R labels near corners clear the T/B vertical labels
H = (rows_v + 3) * GRID
W = (cols_h + 3) * GRID
# round half-extents to grid
halfW = round((W/2)/GRID)*GRID
halfH = round((H/2)/GRID)*GRID

pins_sexp = []
def emit(pin, x, y, rot, length, name):
    r = by_pin[pin]
    et = etype(r)
    nm = name.replace('"',"")
    pins_sexp.append(f'''    (pin {et} line (at {x:.2f} {y:.2f} {rot}) (length {length})
      (name "{nm}" (effects (font (size 1.0 1.0))))
      (number "{pin}" (effects (font (size 0.9 0.9))))
    )''')

LEN = 3.81
# Left: pins point right (rot 0), x = -halfW-LEN, stack top->down
y0 = (nL-1)/2 * GRID
for i,p in enumerate(sides["L"]):
    emit(p, -halfW-LEN, round(y0 - i*GRID,2), 0, LEN, label(by_pin[p]))
# Right: pins point left (rot 180), x = +halfW+LEN
y0 = (nR-1)/2 * GRID
for i,p in enumerate(sides["R"]):
    emit(p, halfW+LEN, round(y0 - i*GRID,2), 180, LEN, label(by_pin[p]))
# Top: pins point down (rot 270), y = +halfH+LEN, left->right
x0 = -(nT-1)/2 * GRID
for i,p in enumerate(sides["T"]):
    emit(p, round(x0 + i*GRID,2), halfH+LEN, 270, LEN, label(by_pin[p]))
# Bottom: pins point up (rot 90), y = -halfH-LEN
x0 = -(nB-1)/2 * GRID
for i,p in enumerate(sides["B"]):
    emit(p, round(x0 + i*GRID,2), -halfH-LEN, 90, LEN, label(by_pin[p]))

rect = f'''    (rectangle (start {-halfW:.2f} {halfH:.2f}) (end {halfW:.2f} {-halfH:.2f})
      (stroke (width 0.254) (type default)) (fill (type background))
    )'''

sym = f'''  (symbol "T41NQ" (in_bom yes) (on_board yes)
    (property "Reference" "IC" (at {-halfW:.2f} {halfH+2.54:.2f} 0)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "T41NQ" (at {-halfW:.2f} {halfH+5.08:.2f} 0)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "teacup:QFN96_10x10_P0.35_EP7.6x7.2_T41" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "T41NQ_ds_v1.6" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "ki_description" "Ingenic T41NQ QFN-96 XBurst2 ISP SoC, SIP 128MB DDR3L (XQ=256MB, LQ=64MB, pin-identical)" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (symbol "T41NQ_0_1"
{rect}
    )
    (symbol "T41NQ_1_1"
{chr(10).join(pins_sexp)}
    )
  )'''

# insert before final closing paren of the .kicad_sym file
content = open(LIB).read()
assert '"T41NQ"' not in content, "T41NQ symbol already present; aborting"
idx = content.rstrip().rfind(")")
new = content.rstrip()[:idx] + sym + "\n)\n"
open(LIB,"w").write(new)
print(f"symbol T41NQ: L={nL} R={nR} T={nT} B={nB} pins, box {2*halfW:.1f}x{2*halfH:.1f}mm")
print(f"appended to {LIB}")
