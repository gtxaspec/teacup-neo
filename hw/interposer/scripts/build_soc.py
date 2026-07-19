"""Interposer SoC section (T31ZX reference) -- connectivity by label, same
convention as the carrier's own scripts: every pin gets either a power
flag or a net label placed directly on it, no drawn wires. Component
values/footprints and the crystal/VREF/VCM bias topology are lifted
verbatim from TeaCup 3.3's tested schematic (the exact circuits this
project is standardizing on). Pin-to-net assignments come from
../pinout_288.csv, cross-referenced against T31ZX's real pin functions
and resolved for every genuine pin-sharing conflict (see that file and
session history for the reasoning behind each call). Per explicit user
direction, 2026-07-18.
"""
import sys, uuid
sys.path.insert(0, '.')
from schgen import Sheet, GRID

TI = "/home/administrator/projects/teacup-neo/hw/interposer/teacup-interposer.kicad_sym"
DEV = "/usr/share/kicad/symbols/Device.kicad_sym"
PWR = "/usr/share/kicad/symbols/power.kicad_sym"
FLASH = "/usr/share/kicad/symbols/Memory_Flash.kicad_sym"

def S(n):
    return round(n * GRID, 2)

s = Sheet()
s.ensure_symbol(TI, "T31ZX", "teacup-interposer:T31ZX")
s.ensure_symbol(DEV, "R", "Device:R")
s.ensure_symbol(DEV, "C", "Device:C")
s.ensure_symbol(DEV, "Crystal_GND24", "Device:Crystal_GND24")
s.ensure_symbol(FLASH, "W25Q32JVSS", "Memory_Flash:W25Q32JVSS")
s.ensure_symbol(PWR, "GND", "power:GND")
s.ensure_symbol(PWR, "PWR_FLAG", "power:PWR_FLAG")

LABEL_ANGLE = {"right": 0, "left": 180, "up": 90, "down": 270}
GNDF = ("flag", "GND")

# ---------- place T31ZX ----------
IC1 = "teacup-interposer:T31ZX"
icx, icy = S(140), S(160)
s.place(IC1, "IC1", "T31ZX", icx, icy, 0,
        footprint="teacup-interposer:QFN35P900X900X90-89N-D",
        ref_at=(icx, icy - S(70), 0), value_at=(icx, icy + S(70), 0))

# per-pin assignment: ("NET"|"RAIL", net_name) | ("LOCAL", local_net_name) | ("GND",)
# LOCAL nets stay sheet-local (no global_); NET/RAIL/SPARE are global so
# they reach the DDR4 edge connector sheet.
PIN_ASSIGN = {
    "1": ("NET", "PWM0"), "2": ("NET", "PWM1"),
    "3": ("RAIL", "+1V8"),
    "4": ("LOCAL", "EXCLK_O"), "5": ("LOCAL", "EXCLK_I"),
    "6": ("RAIL", "+1V8"),
    "7": ("NET", "SPARE_P173"),
    "8": ("NET", "SPARE_P174"),
    "9": ("RAIL", "+1V8"),
    "10": ("RAIL", "VCORE"),
    "11": ("NET", "SPARE_P175"),
    "12": ("NET", "SMB0_SCK"), "13": ("NET", "SMB0_SDA"),
    "14": ("NET", "MSC1_CMD"), "15": ("NET", "MSC1_CLK"),
    "16": ("NET", "MIPI0_GPIO"),
    "17": ("NET", "SPARE_P176"),
    "18": ("NET", "UART2_RXD"), "19": ("NET", "UART2_TXD"),
    "20": ("NET", "UART2_RTS"), "21": ("NET", "UART2_CTS"),
    "22": ("NET", "SPARE_P177"), "23": ("NET", "SPARE_P178"),
    "24": ("NET", "MIPI0_D0N"), "25": ("NET", "MIPI0_D0P"),
    "26": ("NET", "MIPI0_CLKN"), "27": ("NET", "MIPI0_CLKP"),
    "28": ("NET", "MIPI0_D1N"), "29": ("NET", "MIPI0_D1P"),
    "30": ("RAIL", "VCORE"), "31": ("RAIL", "+1V8"),
    "32": ("NET", "SAR_AUX0"),
    "33": ("RAIL", "+1V8"), "34": ("RAIL", "+1V8"),
    "35": ("NET", "USBA_HOST_DM"), "36": ("NET", "USBA_HOST_DP"),
    "37": ("RAIL", "+3V3"), "38": ("RAIL", "+1V8"),
    "39": ("RAIL", "VCORE"), "40": ("RAIL", "+3V3"),
    "41": ("NET", "MICLP"),
    "42": ("LOCAL", "VCM"),
    "43": ("RAIL", "+1V8"),
    "44": ("NET", "HPOUTL"),
    "45": ("NET", "SSI0_CE0"), "46": ("NET", "SSI0_DR"),
    "47": ("NET", "SSI0_DT"), "48": ("NET", "SSI0_CLK"),
    "49": ("NET", "MSC0_D1"), "50": ("NET", "MSC0_D0"),
    "51": ("NET", "MSC0_CLK"), "52": ("NET", "MSC0_CMD"),
    "53": ("NET", "MSC0_D3_CD"), "54": ("NET", "MSC0_D2"),
    "55": ("RAIL", "VCORE"), "56": ("RAIL", "+3V3"),
    "57": ("NET", "GMAC0_MDIO"), "58": ("NET", "GMAC0_MDCK"),
    "59": ("NET", "GMAC0_RXDV"),
    "60": ("NET", "GMAC0_RXD0"), "61": ("NET", "GMAC0_RXD1"),
    "62": ("NET", "GMAC0_TXCLK"), "63": ("NET", "GMAC0_PHYCLK"),
    "64": ("NET", "GMAC0_TXD0"), "65": ("NET", "GMAC0_TXD1"),
    "66": ("NET", "GMAC0_TXEN"),
    "67": ("NET", "SPARE_P179"),
    "68": ("NET", "UART0_RTS"), "69": ("NET", "UART0_CTS"),
    "70": ("NET", "UART0_TXD"), "71": ("NET", "UART0_RXD"),
    "72": ("RAIL", "VCORE"),
    "73": ("NET", "SPARE_P180"), "74": ("NET", "SPARE_P181"),
    "75": ("RAIL", "+1V8"), "76": ("RAIL", "+1V8"),
    "77": ("LOCAL", "VREF"),
    "78": ("RAIL", "VCORE"), "79": ("RAIL", "+1V8"),
    "80": ("NET", "GPIO0"),
    "81": ("NET", "SSI1_CE0"), "82": ("NET", "SSI1_CLK"),
    "83": ("RAIL", "VCORE"), "84": ("RAIL", "+3V3"),
    "85": ("NET", "PWM3"), "86": ("NET", "PWM2"),
    "87": ("NET", "SMB1_SCK"), "88": ("NET", "SMB1_SDA"),
    "89": ("GND",),
}
assert len(PIN_ASSIGN) == 89

for num, entry in PIN_ASSIGN.items():
    p = s.pin_pos(IC1, icx, icy, 0, num)
    d = s.pin_dir(IC1, num)
    kind = entry[0]
    if kind == "GND":
        s.flag("GND", p, "S", d)
    elif kind == "LOCAL":
        s.label(entry[1], p[0], p[1], LABEL_ANGLE[d], global_=False)
    else:  # NET or RAIL -- both cross to the DDR4 edge connector sheet
        s.label(entry[1], p[0], p[1], LABEL_ANGLE[d], global_=True)

# ============ Local support circuitry (values/topology per TeaCup 3.3) ============

RAIL_NAMES = {"+1V8", "+3V3", "VCORE", "VDDR"}

def vert2(lib, ref, val, x, y, top, bottom, fp):
    s.place(lib, ref, val, x, y, 0, footprint=fp,
            ref_at=(x + S(4), y - S(1), 0), value_at=(x + S(4), y + S(1), 0))
    for pn, spec, d in (("1", top, "up"), ("2", bottom, "down")):
        p = s.pin(lib, x, y, 0, pn)
        if isinstance(spec, tuple):
            s.flag(spec[1], p, "S", d)
        else:
            s.label(spec, p[0], p[1], LABEL_ANGLE[d], global_=spec in RAIL_NAMES)

# --- Crystal: Y1 (24MHz) + C20/C21 (12pF load) + R21 (1M feedback) ---
# Y1 pin1->EXCLK_I, pin3->EXCLK_O, pin2 (case, shared position with hidden
# pin4)->GND -- exact TeaCup 3.3 topology, using Crystal_GND24 since the
# real part is a 4-pad case-grounded crystal, not a plain 2-pin one.
CRYSTAL = "Device:Crystal_GND24"
cx, cy = S(20), S(20)
s.place(CRYSTAL, "Y1", "24 MHz", cx, cy, 0,
        footprint="Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm",
        ref_at=(cx, cy - S(6), 0), value_at=(cx, cy + S(6), 0))
for pn, spec in (("1", "EXCLK_I"), ("2", GNDF), ("3", "EXCLK_O")):
    p = s.pin(CRYSTAL, cx, cy, 0, pn)
    d = s.pin_dir(CRYSTAL, pn)
    if isinstance(spec, tuple):
        s.flag(spec[1], p, "S", d)
    else:
        s.label(spec, p[0], p[1], LABEL_ANGLE[d], global_=False)

vert2("Device:C", "C20", "12pF", S(30), S(20), "EXCLK_I", GNDF, "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:C", "C21", "12pF", S(38), S(20), "EXCLK_O", GNDF, "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:R", "R21", "1M", S(46), S(20), "EXCLK_I", "EXCLK_O", "Resistor_SMD:R_0402_1005Metric")

# --- ADC VREF bias: +1V8 --R10-- VREF --R11-- GND, C19 bypass on VREF ---
vert2("Device:R", "R10", "100k", S(20), S(35), "+1V8", "VREF", "Resistor_SMD:R_0603_1608Metric")
vert2("Device:R", "R11", "100k", S(28), S(35), "VREF", GNDF, "Resistor_SMD:R_0603_1608Metric")
vert2("Device:C", "C19", "100nF", S(36), S(35), "VREF", GNDF, "Capacitor_SMD:C_0603_1608Metric")

# --- Audio codec VCM bypass ---
# Footprint matches the hand-solder-friendly pad variant used for the
# real routed placement on the board (C_0603_1608Metric_Pad1.08x0.95mm_
# HandSolder, not the machine-solder default), per explicit user
# direction, 2026-07-18.
vert2("Device:C", "C22", "4.7uF", S(20), S(45), "VCM", GNDF,
      "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder")

# --- +3V3 decoupling (x3, 100nF/0402, matches TeaCup 3.3's C36/C38/C39
# -- C23/C24 are also part of that same TeaCup 3.3 +3V3 bank but aren't
# on the board yet, so not added here). Per explicit user direction,
# 2026-07-18. ---
for i, ref in enumerate(["C36", "C38", "C39"]):
    vert2("Device:C", ref, "100nF", S(20 + i * 6), S(80), "+3V3", GNDF, "Capacitor_SMD:C_0402_1005Metric")

# --- VCORE decoupling (x7, 100nF/0402, matches TeaCup 3.3's C37/C41-C46) ---
for i, ref in enumerate(["C37", "C41", "C42", "C43", "C44", "C45", "C46"]):
    vert2("Device:C", ref, "100nF", S(20 + i * 6), S(60), "VCORE", GNDF, "Capacitor_SMD:C_0402_1005Metric")

# --- VDDR (+1V8) decoupling (x8, 100nF/0402, matches TeaCup 3.3's C25/C26/C28/C30-C32/C34/C35) ---
for i, ref in enumerate(["C25", "C26", "C28", "C30", "C31", "C32", "C34", "C35"]):
    vert2("Device:C", ref, "100nF", S(20 + i * 6), S(70), "+1V8", GNDF, "Capacitor_SMD:C_0402_1005Metric")

# --- Optional self-contained NOR flash (SFC0 bus) -- TeaCup 3.3's U4 ---
FLASHLIB = "Memory_Flash:W25Q32JVSS"
fx, fy = S(70), S(45)
s.place(FLASHLIB, "U4", "W25Q32JVSS", fx, fy, 0,
        footprint="Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
        ref_at=(fx, fy - S(6), 0), value_at=(fx, fy + S(6), 0))
U4_PINS = {
    "1": "SSI0_CE0", "2": "SSI0_DT", "3": "+1V8", "4": ("flag", "GND"),
    "5": "SSI0_DR", "6": "SSI0_CLK", "7": "+1V8", "8": "+1V8",
}
for pn, spec in U4_PINS.items():
    p = s.pin(FLASHLIB, fx, fy, 0, pn)
    d = s.pin_dir(FLASHLIB, pn)
    if isinstance(spec, tuple):
        s.flag(spec[1], p, "S", d)
    else:
        s.label(spec, p[0], p[1], LABEL_ANGLE[d], global_=True)

# --- PWR_FLAG markers: +1V8/+3V3/VCORE are carrier-sourced (cross the
# DDR4 edge connector, no local regulator on this module), so ERC needs
# an explicit "this is externally driven" marker on each, same idiom as
# any KiCad design with an off-sheet supply. ---
PWRFLAG = "power:PWR_FLAG"
for i, railname in enumerate(["+1V8", "+3V3", "VCORE"]):
    px, py = S(80 + i * 8), S(45)
    s.place(PWRFLAG, f"#PWR9{i+1}", "PWR_FLAG", px, py, 0)
    p = s.pin(PWRFLAG, px, py, 0, "1")
    s.label(railname, p[0], p[1], LABEL_ANGLE[s.pin_dir(PWRFLAG, "1")], global_=True)
# GND flag too -- IC1's exposed-pad pin (89) is typed power-input, and
# nothing else on this sheet's GND net is a power-output pin, so ERC
# needs the same "trust this is driven" marker here as on the rails.
gx, gy = S(104), S(45)
s.place(PWRFLAG, "#PWR94", "PWR_FLAG", gx, gy, 0)
p = s.pin(PWRFLAG, gx, gy, 0, "1")
s.flag("GND", p, "S", s.pin_dir(PWRFLAG, "1"))

# --- Bring-up test points: power rails + USB host data. Large 2.0x2.0mm
# SMD pads (easily probed with a hook/multimeter), each just a global
# label tying it to the same net as everywhere else -- including +5V_SW,
# which nothing on this SoC sheet otherwise consumes (T31 has no raw-5V
# pin), but is still worth a probe point to confirm the carrier's
# switched rail is actually reaching the socket. Per explicit user
# direction, 2026-07-18. ---
s.ensure_symbol("/usr/share/kicad/symbols/Connector.kicad_sym", "TestPoint", "Connector:TestPoint")
TP = "Connector:TestPoint"
TP_FOOTPRINT = "TestPoint:TestPoint_Pad_2.0x2.0mm"
TEST_POINTS = ["VCORE", "+1V8", "+3V3", "+5V_SW", "GND", "USBA_HOST_DP", "USBA_HOST_DM"]
for i, netname in enumerate(TEST_POINTS):
    ref = f"TP{i+1}"
    tx, ty = S(80 + i * 10), S(55)
    s.place(TP, ref, netname, tx, ty, 0, footprint=TP_FOOTPRINT,
            ref_at=(tx, ty - S(3), 0), value_at=(tx, ty + S(3), 0))
    p = s.pin(TP, tx, ty, 0, "1")
    d = s.pin_dir(TP, "1")
    if netname == "GND":
        s.flag("GND", p, "S", d)
    else:
        s.label(netname, p[0], p[1], LABEL_ANGLE[d], global_=True)

out = s.render("SoC (T31ZX reference)", str(uuid.uuid4()), "/c1d2e3f4-0001-4000-8000-000000000001", "1", paper="A2")
open("/home/administrator/projects/teacup-neo/hw/interposer/sheets/soc.kicad_sch", "w").write(out)
print("wrote soc.kicad_sch,", len(out), "bytes")
