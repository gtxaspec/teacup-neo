"""POWER section -- rebuilt to the project's BUILD.md core directive:
connectivity by LABEL, not wires. Every pin gets either a power flag
placed directly on it (rotated parallel to the pin, value text kept
horizontal in the pin's own row) or a net label anchored exactly at the
pin. There is not a single drawn wire or junction in this sheet, which
structurally eliminates the wire-pass-through short class entirely.

All coordinates are in 50mil grid steps via S(); schgen asserts grid
alignment on every emitted coordinate.

Internal (single-sheet) nets use local labels named after their IC:
U1_EN, U1_SW, U1_BST, U1_VCC, U1_SS, U2_SW, U2_BST, U2_EN, U7_SW,
U7_BST, U7_EN, P3V3_FB, U4_CT. Board-wide nets keep their existing
global names. Pin-to-net assignments reproduce the pre-rebuild netlist
exactly (verified by component-connectivity diff), including R1 pulling
U1's EN up to +5V_SW (the input rail) as originally designed.
"""
import sys, uuid
sys.path.insert(0, '.')
from schgen import Sheet, GRID

TC = "/home/administrator/projects/teacup-neo/hw/teacup-carrier.kicad_sym"
DEV = "/usr/share/kicad/symbols/Device.kicad_sym"
PWR = "/usr/share/kicad/symbols/power.kicad_sym"
REGLIB = "/usr/share/kicad/symbols/Regulator_Linear.kicad_sym"

def S(n):
    return round(n * GRID, 2)

s = Sheet()
s.ensure_symbol(TC, "AP62600SJ-7", "teacup-carrier:AP62600SJ-7")
s.ensure_symbol(TC, "AP62300WU-7", "teacup-carrier:AP62300WU-7")
s.ensure_symbol(TC, "MCP4661-104E_ST", "teacup-carrier:MCP4661-104E_ST")
s.ensure_symbol(TC, "TPS22990DMLR", "teacup-carrier:TPS22990DMLR")
s.ensure_symbol(DEV, "R", "Device:R")
s.ensure_symbol(DEV, "C", "Device:C")
s.ensure_symbol(DEV, "L", "Device:L")
s.ensure_symbol(PWR, "GND", "power:GND")
s.ensure_symbol(PWR, "+3V3", "power:+3V3")
s.ensure_symbol(REGLIB, "L7805", "Regulator_Linear:L7805")
REG = "Regulator_Linear:L7805"

LABEL_ANGLE = {"right": 0, "left": 180, "up": 90, "down": 270}

def pin_net(pin_xy, net, direction, global_=None):
    """Net label anchored exactly at the pin, extending away from the
    component in the pin's own direction. Globals are auto-detected by
    name unless overridden: internal Ux_* / *_FB nets stay local."""
    if global_ is None:
        global_ = not (net.startswith(("U1_", "U2_", "U4_", "U5_", "U7_", "U14_")) or net.endswith("_FB"))
    s.label(net, pin_xy[0], pin_xy[1], LABEL_ANGLE[direction], global_=global_)

def vert2(lib, ref, val, x, y, top, bottom, fp):
    """Vertical 2-pin passive island: pin1 up, pin2 down; `top`/`bottom`
    are either ("flag", kind) or a net name string. Ref+value are placed
    beside the body (right side) so they never sit on the pins."""
    s.place(lib, ref, val, x, y, 0, footprint=fp,
            ref_at=(x + S(4), y - S(1), 0), value_at=(x + S(4), y + S(1), 0))
    p1 = s.pin(lib, x, y, 0, "1")
    p2 = s.pin(lib, x, y, 0, "2")
    for p, spec, d in ((p1, top, "up"), (p2, bottom, "down")):
        if isinstance(spec, tuple):
            s.flag(spec[1], p, "P", d)
        else:
            pin_net(p, spec, d)
    return p1, p2

def horiz2(lib, ref, val, x, y, left, right, fp):
    """Horizontal 2-pin passive island (placement angle 90 puts pin1 on
    the LEFT): pin1 <- left spec, pin2 -> right spec. Property angle 270
    cancels the symbol's own 90 rotation so ref/value render horizontal."""
    s.place(lib, ref, val, x, y, 90, footprint=fp,
            ref_at=(x, y - S(3), 270), value_at=(x, y + S(3), 270))
    p1 = s.pin(lib, x, y, 90, "1")
    p2 = s.pin(lib, x, y, 90, "2")
    for p, spec, d in ((p1, left, "left"), (p2, right, "right")):
        if isinstance(spec, tuple):
            s.flag(spec[1], p, "P", d)
        else:
            pin_net(p, spec, d)
    return p1, p2

GNDF = ("flag", "GND")
P3V3F = ("flag", "+3V3")

# ============ VCORE buck (U1, AP62600SJ-7) ============
U1 = "teacup-carrier:AP62600SJ-7"
u1x, u1y = S(48), S(24)
s.place(U1, "U1", "AP62600SJ-7", u1x, u1y, 0,
        footprint="teacup-carrier:QFN-12_L3.0-W2.0-P0.50-TL_AP62600SJ-7",
        ref_at=(u1x, u1y - S(9), 0), value_at=(u1x, u1y + S(9), 0))
P1 = lambda n: s.pin(U1, u1x, u1y, 0, str(n))

s.flag("GND", P1(1), "P", "left")            # PGND
pin_net(P1(2), "+5V_SW", "left")             # VIN
pin_net(P1(3), "U1_EN", "left")              # EN
s.flag("GND", P1(4), "P", "left")            # MODE
s.flag("GND", P1(5), "P", "left")            # FSEL
pin_net(P1(6), "PG_VCORE", "left")           # PG (open-drain, R2 pulls up)
pin_net(P1(12), "VCORE_FB_SEL", "right")     # FB -- jumper common pole, see JP2-JP6 below
s.flag("GND", P1(11), "P", "right")          # GND
pin_net(P1(10), "U1_SS", "right")            # SS/TR
pin_net(P1(9), "U1_VCC", "right")            # VCC
pin_net(P1(8), "U1_SW", "right")             # SW
pin_net(P1(7), "U1_BST", "right")            # BST

# U1 passive islands
py1 = S(48)
vert2("Device:C", "C1", "22uF", S(20), py1, "+5V_SW", GNDF, "Capacitor_SMD:C_0805_2012Metric")
vert2("Device:C", "C2", "100nF", S(29), py1, "+5V_SW", GNDF, "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:C", "C4", "1uF", S(38), py1, "U1_VCC", GNDF, "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:C", "C5", "4.7nF", S(47), py1, "U1_SS", GNDF, "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:C", "C3", "100nF", S(56), py1, "U1_BST", "U1_SW", "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:C", "C9", "22uF", S(65), py1, "VCORE", GNDF, "Capacitor_SMD:C_0805_2012Metric")
vert2("Device:C", "C10", "22uF", S(74), py1, "VCORE", GNDF, "Capacitor_SMD:C_0805_2012Metric")
vert2("Device:R", "R1", "100k", S(83), py1, "+5V_SW", "U1_EN", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R2", "10k", S(92), py1, P3V3F, "PG_VCORE", "Resistor_SMD:R_0402_1005Metric")
horiz2("Device:L", "L1", "2.2uH", S(106), py1, "U1_SW", "VCORE", "Inductor_SMD:L_1210_3225Metric")

# ============ VDDR buck (U2, AP62300WU-7) ============
U2 = "teacup-carrier:AP62300WU-7"
u2x, u2y = S(48), S(64)
s.place(U2, "U2", "AP62300WU-7", u2x, u2y, 0,
        footprint="teacup-carrier:TSOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL",
        ref_at=(u2x, u2y - S(6), 0), value_at=(u2x, u2y + S(6), 0))
P2 = lambda n: s.pin(U2, u2x, u2y, 0, str(n))

s.flag("GND", P2(1), "P", "left")            # GND
pin_net(P2(2), "U2_SW", "left")              # SW
pin_net(P2(3), "+5V_SW", "left")             # VIN
pin_net(P2(4), "VDDR_FB_SEL", "right")       # FB -- jumper common pole, see JP7-JP10 below
pin_net(P2(5), "U2_EN", "right")             # EN
pin_net(P2(6), "U2_BST", "right")            # BST

py2 = S(84)
vert2("Device:C", "C6", "10uF", S(20), py2, "+5V_SW", GNDF, "Capacitor_SMD:C_0805_2012Metric")
vert2("Device:C", "C7", "100nF", S(29), py2, "U2_BST", "U2_SW", "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:C", "C11", "22uF", S(38), py2, "VDDR", GNDF, "Capacitor_SMD:C_0805_2012Metric")
vert2("Device:R", "R3", "100k", S(47), py2, P3V3F, "U2_EN", "Resistor_SMD:R_0402_1005Metric")
horiz2("Device:L", "L2", "2.2uH", S(62), py2, "U2_SW", "VDDR", "Inductor_SMD:L_1210_3225Metric")

# ============ Main +3.3V buck (U7, AP62300WU-7) ============
u7x, u7y = S(48), S(100)
s.place(U2, "U7", "AP62300WU-7", u7x, u7y, 0,
        footprint="teacup-carrier:TSOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL",
        ref_at=(u7x, u7y - S(6), 0), value_at=(u7x, u7y + S(6), 0))
P7 = lambda n: s.pin(U2, u7x, u7y, 0, str(n))

s.flag("GND", P7(1), "P", "left")            # GND
pin_net(P7(2), "U7_SW", "left")              # SW
pin_net(P7(3), "+5V_SW", "left")             # VIN
pin_net(P7(4), "P3V3_FB", "right")           # FB
pin_net(P7(5), "U7_EN", "right")             # EN
pin_net(P7(6), "U7_BST", "right")            # BST

py7 = S(120)
vert2("Device:C", "C16", "10uF", S(20), py7, "+5V_SW", GNDF, "Capacitor_SMD:C_0805_2012Metric")
vert2("Device:C", "C17", "100nF", S(29), py7, "U7_BST", "U7_SW", "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:C", "C18", "22uF", S(38), py7, "+3V3", GNDF, "Capacitor_SMD:C_0805_2012Metric")
vert2("Device:R", "R5", "100k", S(47), py7, "+5V_SW", "U7_EN", "Resistor_SMD:R_0402_1005Metric")
# fixed 3.3V feedback divider: +3V3 -- R6 -- P3V3_FB -- R7 -- GND
vert2("Device:R", "R6", "31.6k", S(56), py7, P3V3F, "P3V3_FB", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R7", "10k", S(65), py7, "P3V3_FB", GNDF, "Resistor_SMD:R_0402_1005Metric")
horiz2("Device:L", "L3", "2.2uH", S(80), py7, "U7_SW", "+3V3", "Inductor_SMD:L_1210_3225Metric")

# ============ BMC-alive diode-OR (D1/D2): keep the ESP32 powered on ALT-only ============
# +5V_BMC (J9-only) normally feeds U5 alone; if J9 is unplugged and only
# +5V_ALT is present, the ESP32 would otherwise be fully dead (its own
# isolated domain, by design -- see io.kicad_sch Q1/Q2). D1/D2 diode-OR
# both candidate sources into U5_VIN, a node ONLY U5 sees -- U4 (the
# BMC-branch load switch feeding +5V_SW) still sources strictly from the
# real, undiluted +5V_BMC net, so its behavior stays unambiguous; this
# fix is scoped to "keep the BMC brain alive," not a second path to
# +5V_SW (U14/+5V_ALT is already the correct direct path for that).
# PMEG2010ER: 1A Schottky, 340mV Vf @ 1A (LCSC C82288) -- plenty of
# margin over the WROOM-1's peak draw, low enough drop to stay inside
# the AZ1117-3.3's dropout at that current (reconfirm against real load
# current at bring-up).
DSCH = "Device:D_Schottky"
s.ensure_symbol(DEV, "D_Schottky", "Device:D_Schottky")

d1x, d1y = S(108), S(10)
s.place(DSCH, "D1", "PMEG2010ER", d1x, d1y, 0,
        footprint="Diode_SMD:D_SOD-123W",
        ref_at=(d1x, d1y - S(3), 0), value_at=(d1x, d1y + S(3), 0))
pin_net(s.pin(DSCH, d1x, d1y, 0, "1"), "U5_VIN", "left")     # K
pin_net(s.pin(DSCH, d1x, d1y, 0, "2"), "+5V_BMC", "right")   # A

d2x, d2y = S(108), S(22)
s.place(DSCH, "D2", "PMEG2010ER", d2x, d2y, 0,
        footprint="Diode_SMD:D_SOD-123W",
        ref_at=(d2x, d2y - S(3), 0), value_at=(d2x, d2y + S(3), 0))
pin_net(s.pin(DSCH, d2x, d2y, 0, "1"), "U5_VIN", "left")     # K
pin_net(s.pin(DSCH, d2x, d2y, 0, "2"), "+5V_ALT", "right")   # A

# ============ Always-on 3.3V LDO (U5, AZ1117CH-3.3) ============
u5x, u5y = S(150), S(16)
s.place(REG, "U5", "AZ1117CH-3.3TRG1", u5x, u5y, 0,
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        extra_props={"Datasheet": "https://lcsc.com/product-detail/C92102.html"},
        ref_at=(u5x, u5y - S(6), 0), value_at=(u5x, u5y - S(4), 0))
pin_net(s.pin(REG, u5x, u5y, 0, "1"), "U5_VIN", "left")
s.flag("GND", s.pin(REG, u5x, u5y, 0, "2"), "P", "down")
pin_net(s.pin(REG, u5x, u5y, 0, "3"), "+3V3_ALWAYS", "right")
vert2("Device:C", "C14", "1uF", S(128), S(16), "U5_VIN", GNDF, "Capacitor_SMD:C_0603_1608Metric")
vert2("Device:C", "C15", "10uF", S(178), S(16), "+3V3_ALWAYS", GNDF, "Capacitor_SMD:C_0805_2012Metric")

# ============ +1.8V LDO (U6, AZ1117CH-1.8) ============
u6x, u6y = S(150), S(44)
s.place(REG, "U6", "AZ1117CH-1.8TRG1", u6x, u6y, 0,
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        extra_props={"Datasheet": "https://lcsc.com/product-detail/C95397.html"},
        ref_at=(u6x, u6y - S(6), 0), value_at=(u6x, u6y - S(4), 0))
pin_net(s.pin(REG, u6x, u6y, 0, "1"), "+3V3", "left")
s.flag("GND", s.pin(REG, u6x, u6y, 0, "2"), "P", "down")
pin_net(s.pin(REG, u6x, u6y, 0, "3"), "+1V8", "right")
vert2("Device:C", "C19", "1uF", S(128), S(44), "+3V3", GNDF, "Capacitor_SMD:C_0603_1608Metric")
vert2("Device:C", "C20", "10uF", S(178), S(44), "+1V8", GNDF, "Capacitor_SMD:C_0805_2012Metric")

# ============ BMC-branch load switch (U4, TPS22990DMLR) ============
# Gates +5V_BMC (the ESP32's own dedicated USB-C, isolated from every
# other source) onto the shared +5V_SW rail. EN_SW_BMC is arbitrated
# between GPIO (SW5V_EN_BMC, through R21), its own pulldown (R20), and
# SW2's throw1 on the bmc sheet (crosses in via this same label) -- one
# throw of the same on-off-on switch that forces the ALT branch (U14) on
# the other throw.
U4 = "teacup-carrier:TPS22990DMLR"
u4x, u4y = S(150), S(76)
s.place(U4, "U4", "TPS22990DMLR", u4x, u4y, 0,
        footprint="teacup-carrier:WSON-10_L3.0-W2.0-P0.50-BL-EP_TI_DML",
        ref_at=(u4x, u4y - S(9), 0), value_at=(u4x, u4y + S(9), 0))
P4 = lambda n: s.pin(U4, u4x, u4y, 0, str(n))

pin_net(P4(1), "U4_CT", "left")              # CT
# pin 2 NC -- deliberately unconnected per datasheet
pin_net(P4(3), "+5V_BMC", "left")            # VIN
pin_net(P4(4), "+5V_BMC", "left")            # VBIAS (tied to VIN)
pin_net(P4(5), "EN_SW_BMC", "left")          # ON
s.flag("GND", P4(6), "P", "right")           # GND
pin_net(P4(7), "PG_SW5V", "right")           # PG (open-drain, R4 pulls up)
pin_net(P4(8), "+5V_SW", "right")            # VOUT
pin_net(P4(9), "+5V_SW", "right")            # VOUT
pin_net(P4(10), "+5V_SW", "right")           # VOUT
pin_net(P4(11), "+5V_BMC", "right")          # VIN

vert2("Device:C", "C13", "1nF_TBD", S(132), S(96), "U4_CT", GNDF, "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:R", "R4", "10k", S(150), S(96), P3V3F, "PG_SW5V", "Resistor_SMD:R_0402_1005Metric")

# BMC-branch EN arbitration: GPIO drives through a 1k series resistor,
# a 100k pulldown keeps it safely off when undriven (ESP32 in reset/Hi-Z).
vert2("Device:R", "R21", "1k", S(132), S(60), "SW5V_EN_BMC", "EN_SW_BMC", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R20", "100k", S(141), S(60), "EN_SW_BMC", GNDF, "Resistor_SMD:R_0402_1005Metric")

# ============ ALT-branch load switch (U14, TPS22990DMLR) ============
# Gates +5V_ALT (the priority-OR'd DC jack / alt USB-C, see io.kicad_sch
# Q1/Q2) onto the same shared +5V_SW rail. EN_SW_ALT is arbitrated the
# same way as EN_SW_BMC (GPIO + pulldown) but is ALSO hard-overridable by
# SW2's throw4 on the bmc sheet, which ties this node to +5V_ALT (SW2's
# pole) when selected -- low-impedance, beats GPIO16's resistor-limited
# drive. Center = neither throw engaged, GPIO has full control.
U14 = "teacup-carrier:TPS22990DMLR"
u14x, u14y = S(210), S(76)
s.place(U14, "U14", "TPS22990DMLR", u14x, u14y, 0,
        footprint="teacup-carrier:WSON-10_L3.0-W2.0-P0.50-BL-EP_TI_DML",
        ref_at=(u14x, u14y - S(9), 0), value_at=(u14x, u14y + S(9), 0))
P14 = lambda n: s.pin(U14, u14x, u14y, 0, str(n))

pin_net(P14(1), "U14_CT", "left")            # CT
# pin 2 NC -- deliberately unconnected per datasheet
pin_net(P14(3), "+5V_ALT", "left")           # VIN
pin_net(P14(4), "+5V_ALT", "left")           # VBIAS (tied to VIN)
pin_net(P14(5), "EN_SW_ALT", "left")         # ON
s.flag("GND", P14(6), "P", "right")          # GND
pin_net(P14(7), "PG_SW5V_ALT", "right")      # PG (open-drain, R24 pulls up)
pin_net(P14(8), "+5V_SW", "right")           # VOUT (same shared rail as U4)
pin_net(P14(9), "+5V_SW", "right")           # VOUT
pin_net(P14(10), "+5V_SW", "right")          # VOUT
pin_net(P14(11), "+5V_ALT", "right")         # VIN

vert2("Device:C", "C23", "1nF_TBD", S(192), S(96), "U14_CT", GNDF, "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:R", "R24", "10k", S(210), S(96), P3V3F, "PG_SW5V_ALT", "Resistor_SMD:R_0402_1005Metric")

# ALT-branch EN arbitration -- same topology as the BMC branch, plus SW2's
# hard override on the bmc sheet (crosses in via the EN_SW_ALT label).
vert2("Device:R", "R23", "1k", S(192), S(60), "SW5V_EN_ALT", "EN_SW_ALT", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R22", "100k", S(201), S(60), "EN_SW_ALT", GNDF, "Resistor_SMD:R_0402_1005Metric")

# ============ Digipot (U3, MCP4661, both channels) ============
U3 = "teacup-carrier:MCP4661-104E_ST"
u3x, u3y = S(150), S(130)
s.place(U3, "U3", "MCP4661-104E_ST", u3x, u3y, 0,
        footprint="Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
        ref_at=(u3x, u3y - S(9), 0), value_at=(u3x, u3y + S(9), 0))
P3 = lambda n: s.pin(U3, u3x, u3y, 0, str(n))

s.flag("GND", P3(1), "P", "left")            # HVC/A0
pin_net(P3(2), "I2C_PWR_SCL", "left")        # SCL
pin_net(P3(3), "I2C_PWR_SDA", "left")        # SDA
s.flag("GND", P3(4), "P", "left")            # VSS
s.flag("GND", P3(5), "P", "left")            # P1B
pin_net(P3(6), "VDDR_FB_DIGIPOT", "left")    # P1W -- one jumper throw, not hard-wired to FB anymore
pin_net(P3(7), "VDDR", "left")               # P1A
pin_net(P3(8), "VCORE", "right")             # P0A
pin_net(P3(9), "VCORE_FB_DIGIPOT", "right")  # P0W -- one jumper throw, not hard-wired to FB anymore
s.flag("GND", P3(10), "P", "right")          # P0B
s.flag("+3V3", P3(11), "P", "right")         # WP
s.flag("GND", P3(12), "P", "right")          # A2
s.flag("GND", P3(13), "P", "right")          # A1
s.flag("+3V3", P3(14), "P", "right")         # VDD

vert2("Device:C", "C12", "100nF", S(200), S(130), P3V3F, GNDF, "Capacitor_SMD:C_0402_1005Metric")

# I2C_PWR bus pull-ups (digipot U3 + GPIO expander U15 on the bmc sheet,
# master on ESP32 GPIO4/5) -- neither device supplies its own, and I2C is
# open-drain, so without these the bus simply doesn't work. 4.7k to +3V3,
# standard value for a short, low-device-count, carrier-local bus.
vert2("Device:R", "R25", "4.7k", S(209), S(130), P3V3F, "I2C_PWR_SDA", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R26", "4.7k", S(218), S(130), P3V3F, "I2C_PWR_SCL", "Resistor_SMD:R_0402_1005Metric")

# ============ VCORE/VDDR voltage-select jumpers ============
# Explicit user direction: replace "trust the digipot's NV memory" as the
# power-up safety story with a hardware-deterministic default. U1/U2's FB
# pins (VCORE_FB_SEL / VDDR_FB_SEL above) are now the common pole of a
# jumper bank, not hard-wired to the digipot wiper. Every candidate divider
# -- 4 fixed presets for VCORE, 3 for VDDR, plus the digipot itself as one
# more candidate -- stays permanently powered across VOUT/GND regardless of
# jumper position (each draws only ~50-100uA, negligible against a
# multi-amp buck), so only the SELECTED network's midpoint is ever
# electrically tied to FB; the rest just idle. Populate exactly one shunt
# per regulator -- none leaves FB floating (dangerous), two shorts two
# dividers together (wrong, undefined voltage). Preset values computed from
# each buck's own FB reference (AP62600SJ-7: 0.6V, AP62300WU-7: 0.8V) via
# VOUT = VFB*(1+Rtop/Rbottom), Rbottom=10.0k shared reference, snapped to
# approximate E96 1% steps and deliberately biased slightly LOW rather than
# high -- safer to undervolt an unknown SoC than overvolt it. Verify exact
# E96 values against the real table before finalizing the BOM.
#
# "Computer" position routes FB to the digipot wiper exactly as before, so
# the EEPROM-on-interposer -> BMC-reads-it -> BMC-writes-digipot flow (SS7)
# still works whenever that position is deliberately selected -- it just
# can no longer influence the rail from any OTHER jumper position, which is
# what makes the preset positions safe regardless of digipot/EEPROM state.
# This is why JP1 and the mandatory bring-up checklist (formerly gating
# SW2, see bmc sheet) are gone: the checklist existed only to manage the
# exact risk this jumper bank now prevents in hardware. The user now sets
# these jumpers by hand to match whichever interposer/SoC is seated --
# manual, but that manual step is what removes the unsafe window.

def preset_divider(rtop_ref, rtop_val, rbot_ref, x, y, rail, mid_net):
    vert2("Device:R", rtop_ref, rtop_val, x, y, rail, mid_net, "Resistor_SMD:R_0402_1005Metric")
    vert2("Device:R", rbot_ref, "10.0k", x + S(9), y, mid_net, GNDF, "Resistor_SMD:R_0402_1005Metric")

CONNLIB_GENERIC = "/usr/share/kicad/symbols/Connector_Generic.kicad_sym"
s.ensure_symbol(CONNLIB_GENERIC, "Conn_01x02", "Connector_Generic:Conn_01x02")
JHDR = "Connector_Generic:Conn_01x02"
JFP = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"

def jumper(ref, val, x, y, pole_net, throw_net):
    # Ref/value pushed above/below the pin span (matching the headers
    # sheet's proven convention) rather than vert2's default beside-the-body
    # offset -- the pole/throw net labels here (VCORE_FB_SEL etc.) are long
    # enough to run into a close-beside ref/value at this tight jumper
    # pitch. Confirmed via check_overlaps.py.
    s.place(JHDR, ref, val, x, y, 0, footprint=JFP,
            ref_at=(x + S(2), y + S(4), 0), value_at=(x + S(2), y - S(4), 0))
    p1 = s.pin(JHDR, x, y, 0, "1")
    p2 = s.pin(JHDR, x, y, 0, "2")
    pin_net(p1, pole_net, "up")
    pin_net(p2, throw_net, "down")

# Placed BELOW the existing rows, side by side (VCORE then VDDR in X) rather
# than stacked in Y -- reusing the same x range already in use plus modest
# extension, staying well clear of both the bmc sheet (merge dx=S(240)) and
# the connector sheet (merge dy=S(180)) territories post-merge, and with
# generous row-to-row Y spacing so divider/jumper label text doesn't run
# into the next row. Confirmed clean via check_overlaps.py, not assumed.
# ---- VCORE: 4 presets (0.8/0.9/1.0/1.1V) + digipot, 5-way select ----
pv_y = S(150)
s.text("VCORE VOLTAGE SELECT", S(20), pv_y - S(6), 0, size=1.5, bold=True)
preset_divider("R27", "3.32k", "R28", S(20), pv_y, "VCORE", "VCORE_FB_0V8")
preset_divider("R29", "4.99k", "R30", S(38), pv_y, "VCORE", "VCORE_FB_0V9")
preset_divider("R31", "6.65k", "R32", S(56), pv_y, "VCORE", "VCORE_FB_1V0")
preset_divider("R33", "8.25k", "R34", S(74), pv_y, "VCORE", "VCORE_FB_1V1")

jv_y = S(182)
jumper("JP2", "0.8V", S(20), jv_y, "VCORE_FB_SEL", "VCORE_FB_0V8")
jumper("JP3", "0.9V", S(29), jv_y, "VCORE_FB_SEL", "VCORE_FB_0V9")
jumper("JP4", "1.0V", S(38), jv_y, "VCORE_FB_SEL", "VCORE_FB_1V0")
jumper("JP5", "1.1V", S(47), jv_y, "VCORE_FB_SEL", "VCORE_FB_1V1")
jumper("JP6", "COMPUTER", S(56), jv_y, "VCORE_FB_SEL", "VCORE_FB_DIGIPOT")

# ---- VDDR: 3 presets (1.35/1.5/1.8V) + digipot, 4-way select -- to the
# right of VCORE's block, same two Y rows, not below it. Kept tighter/
# further left than a first pass (which reached x=190.5, colliding with U3
# the digipot, sitting at that same x) -- last column now ends at x=141*1.27
# =179.07, clear of U3's body/value text.
s.text("VDDR VOLTAGE SELECT", S(100), pv_y - S(6), 0, size=1.5, bold=True)
preset_divider("R35", "6.81k", "R36", S(100), pv_y, "VDDR", "VDDR_FB_1V35")
preset_divider("R37", "8.66k", "R38", S(114), pv_y, "VDDR", "VDDR_FB_1V5")
preset_divider("R39", "12.4k", "R40", S(128), pv_y, "VDDR", "VDDR_FB_1V8")

jumper("JP7", "1.35V", S(100), jv_y, "VDDR_FB_SEL", "VDDR_FB_1V35")
jumper("JP8", "1.5V", S(109), jv_y, "VDDR_FB_SEL", "VDDR_FB_1V5")
jumper("JP9", "1.8V", S(118), jv_y, "VDDR_FB_SEL", "VDDR_FB_1V8")
jumper("JP10", "COMPUTER", S(127), jv_y, "VDDR_FB_SEL", "VDDR_FB_DIGIPOT")

out = s.render("Power", str(uuid.uuid4()), "/e91d090e-0b5e-4716-96ce-185f84fa3402", "2", paper="A3")
open("/home/administrator/projects/teacup-neo/hw/sheets/power.kicad_sch", "w").write(out)
print("wrote power.kicad_sch,", len(out), "bytes")
