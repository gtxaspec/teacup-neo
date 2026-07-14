"""Carrier physical I/O section -- connectivity by label per BUILD.md,
same system as the approved power/bmc/connector sheets: flags directly on
power pins (parallel), labels directly on signal pins, no wires, 50mil
grid. Duplicate-position pins (USB-C's stacked A/B VBUS pins) are labeled
once per unique position to avoid printing the same text twice on itself."""
import sys, uuid
sys.path.insert(0, '.')
from schgen import Sheet, GRID

TC = "/home/administrator/projects/teacup-neo/hw/teacup-carrier.kicad_sym"
CONNLIB = "/usr/share/kicad/symbols/Connector.kicad_sym"
AUDIO = "/usr/share/kicad/symbols/Connector_Audio.kicad_sym"
DEV = "/usr/share/kicad/symbols/Device.kicad_sym"
PWR = "/usr/share/kicad/symbols/power.kicad_sym"
FETLIB = "/usr/share/kicad/symbols/Transistor_FET.kicad_sym"

def S(n):
    return round(n * GRID, 2)

s = Sheet()
s.ensure_symbol(CONNLIB, "USB_C_Receptacle_USB2.0_16P", "Connector:USB_C_Receptacle_USB2.0_16P")
s.ensure_symbol(CONNLIB, "USB_A", "Connector:USB_A")
s.ensure_symbol(CONNLIB, "Micro_SD_Card", "Connector:Micro_SD_Card")
s.ensure_symbol(CONNLIB, "Barrel_Jack_Switch", "Connector:Barrel_Jack_Switch")
s.ensure_symbol(AUDIO, "AudioJack4_Ground", "Connector_Audio:AudioJack4_Ground")
s.ensure_symbol(TC, "SFW15R-2STE1LF_C3167933", "teacup-carrier:SFW15R-2STE1LF_C3167933")
s.ensure_symbol(DEV, "R", "Device:R")
s.ensure_symbol(DEV, "C", "Device:C")
# AO3401A's real pin data lives in TP0610T (it "extends" that base symbol in
# KiCad's library -- an inheritance schgen's simple text loader doesn't
# resolve), so load TP0610T's body but cache/rename it under the AO3401A
# lib_id via ensure_symbol's existing rename mechanism. This makes ERC flag
# a harmless "Symbol 'AO3401A' doesn't match copy in library" warning
# (expected: the cached copy is a flattened expansion, not a byte-identical
# "extends" reference) -- clears with a one-click "Update Symbols from
# Library" in the GUI if it bothers you; pins/footprint are already
# correct either way. Per-instance
# footprint/value overrides in place() make the borrowed block's own
# (irrelevant) default properties harmless.
s.ensure_symbol(FETLIB, "TP0610T", "Transistor_FET:AO3401A")
s.ensure_symbol(PWR, "GND", "power:GND")
s.ensure_symbol(PWR, "+3V3", "power:+3V3")

LABEL_ANGLE = {"right": 0, "left": 180, "up": 90, "down": 270}
# Q1_GATE/Q2_GATE and the 2nd USB-C's CC lines stay local to this sheet;
# DCJACK_VBUS/ALTUSB_VBUS/+5V_ALT/+5V_BMC/BMC_USB_D+-/- all cross to the
# power or bmc sheets and must stay global (the ic_pins()/vert2() default).
LOCAL_NETS = {"USBC_CC1", "USBC_CC2", "USBC2_CC1", "USBC2_CC2", "Q1_GATE", "Q2_GATE"}
GNDF = ("flag", "GND")
P3V3F = ("flag", "+3V3")

def ic_pins(lib_id, x, y, pinmap):
    """Label/flag each pin; positions are deduped so stacked same-net pins
    (e.g. USB-C A4/B4 VBUS at identical coordinates) get one annotation."""
    seen = set()
    for num, spec in pinmap.items():
        if spec is None:
            continue
        p = s.pin_pos(lib_id, x, y, 0, str(num))
        if p in seen:
            continue
        seen.add(p)
        d = s.pin_dir(lib_id, str(num))
        if isinstance(spec, tuple):
            s.flag(spec[1], p, "I", d)
        else:
            s.label(spec, p[0], p[1], LABEL_ANGLE[d], global_=spec not in LOCAL_NETS)

def vert2(lib, ref, val, x, y, top, bottom, fp):
    s.place(lib, ref, val, x, y, 0, footprint=fp,
            ref_at=(x + S(4), y - S(1), 0), value_at=(x + S(4), y + S(1), 0))
    for pn, spec, d in (("1", top, "up"), ("2", bottom, "down")):
        p = s.pin(lib, x, y, 0, pn)
        if isinstance(spec, tuple):
            s.flag(spec[1], p, "I", d)
        else:
            s.label(spec, p[0], p[1], LABEL_ANGLE[d], global_=spec not in LOCAL_NETS)

# ============ USB-C (J2): alt power input + host data to interposer ============
# VBUS is a candidate power source (OR'd against the DC jack, DC jack has
# priority -- see Q1/Q2 below), not tied to BMC power at all: this port is
# fully isolated from the ESP32's own supply so a USB connection here can
# never backfeed the BMC. D+/D- are shared with J3 (see there).
J2 = "Connector:USB_C_Receptacle_USB2.0_16P"
j2x, j2y = S(40), S(40)
s.place(J2, "J2", "TYPE-C-31-M-12", j2x, j2y, 0,
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
        ref_at=(j2x, j2y - S(18), 0), value_at=(j2x, j2y + S(18), 0))
ic_pins(J2, j2x, j2y, {
    "A1": GNDF, "A12": GNDF, "B1": GNDF, "B12": GNDF, "S1": GNDF,
    "A4": "ALTUSB_VBUS", "B4": "ALTUSB_VBUS", "A9": "ALTUSB_VBUS", "B9": "ALTUSB_VBUS",
    "A5": "USBC_CC1", "B5": "USBC_CC2",
    # D+/D- shared with J3 (USB-A) -- one logical host port on the
    # interposer SoC, two physical connectors. Peripheral use only
    # (USB wifi/keyboard/hub); not a power path.
    "A7": "USBA_HOST_DM", "B7": "USBA_HOST_DM",
    "A6": "USBA_HOST_DP", "B6": "USBA_HOST_DP",
    # SBU1/SBU2 (A8/B8) deliberately unconnected
})

# CC pulldowns: 5.1k to GND (UFP/sink presentation for vSafe5V)
vert2("Device:R", "R12", "5.1k", S(85), S(36), "USBC_CC1", GNDF, "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R13", "5.1k", S(94), S(36), "USBC_CC2", GNDF, "Resistor_SMD:R_0402_1005Metric")

# ============ Dedicated BMC USB-C (J9): ESP32's own port ============
# Powers the BMC exclusively (+5V_BMC -> U5 on the power sheet, isolated
# from every other 5V source on the board) and carries the ESP32's own
# USB-CDC data lines -- this is what J2 used to (wrongly) share.
J9 = "Connector:USB_C_Receptacle_USB2.0_16P"
j9x, j9y = S(90), S(70)
s.place(J9, "J9", "TYPE-C-31-M-12", j9x, j9y, 0,
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
        ref_at=(j9x, j9y - S(18), 0), value_at=(j9x, j9y + S(18), 0))
ic_pins(J9, j9x, j9y, {
    "A1": GNDF, "A12": GNDF, "B1": GNDF, "B12": GNDF, "S1": GNDF,
    "A4": "+5V_BMC", "B4": "+5V_BMC", "A9": "+5V_BMC", "B9": "+5V_BMC",
    "A5": "USBC2_CC1", "B5": "USBC2_CC2",
    "A7": "BMC_USB_DM", "B7": "BMC_USB_DM",
    "A6": "BMC_USB_DP", "B6": "BMC_USB_DP",
    # SBU1/SBU2 (A8/B8) deliberately unconnected
})
vert2("Device:R", "R18", "5.1k", S(115), S(66), "USBC2_CC1", GNDF, "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R19", "5.1k", S(124), S(66), "USBC2_CC2", GNDF, "Resistor_SMD:R_0402_1005Metric")
# Bulk/bypass cap right at the raw VBUS input, before it reaches U4 (power
# sheet) -- was previously undecoupled all the way from the connector.
vert2("Device:C", "C27", "10uF", S(65), S(100), "+5V_BMC", GNDF, "Capacitor_SMD:C_0805_2012Metric")

# ============ Priority power-OR (Q1/Q2): DC jack over alt USB-C ============
# Two P-FETs OR DCJACK_VBUS and ALTUSB_VBUS onto +5V_ALT, which feeds the
# BMC/ALT 2:1 select on the power sheet. Both self-enable from their own
# VBUS via a gate pulldown; Q2's gate is additionally biased toward
# DCJACK_VBUS through R16, so whenever the DC jack has power, Q2's gate
# sits close to its own source and it stays off -- deterministic hardware
# priority, no firmware involved. AO3401A-class P-FET: SOT-23, Vgs(th)
# ~-0.9V, plenty of margin off a 5V rail (see docs/UNIVERSAL.md sourcing).
#
# Uses the dedicated Transistor_FET:AO3401A library symbol, not the generic
# Device:Q_PMOS -- Q_PMOS's pin NUMBERS are the letters "G"/"D"/"S"
# themselves (a schematic-only placeholder, never meant to auto-associate
# with a real footprint's numeric pads), so a PCB pass found 6 pins with no
# net assigned at all. AO3401A has real numeric pins (1=G, 2=S, 3=D --
# confirmed against AOS's own datasheet pinout diagram AND an independent
# third-party pin table, since KiCad's library and my own reading of the
# datasheet graphic initially disagreed on the 2-vs-3 assignment) and is
# already paired with the same SOT-23 footprint used here. Same pin
# geometry as Q_PMOS at each position, so only the lookup string changes.
AO3401A = "Transistor_FET:AO3401A"
AO_G, AO_S, AO_D = "1", "2", "3"

def q_pin(lib_id, x, y, num, spec, angle=0):
    p = s.pin(lib_id, x, y, angle, num)
    d = s.pin_dir(lib_id, num)
    if isinstance(spec, tuple):
        s.flag(spec[1], p, "Q", d)
    else:
        s.label(spec, p[0], p[1], LABEL_ANGLE[d], global_=spec not in LOCAL_NETS)

q1x, q1y = S(90), S(130)
s.place(AO3401A, "Q1", "AO3401A", q1x, q1y, 0,
        footprint="Package_TO_SOT_SMD:SOT-23",
        ref_at=(q1x - S(8), q1y - S(3), 0), value_at=(q1x - S(8), q1y + S(3), 0))
q_pin(AO3401A, q1x, q1y, AO_S, "DCJACK_VBUS")
q_pin(AO3401A, q1x, q1y, AO_D, "+5V_ALT")
q_pin(AO3401A, q1x, q1y, AO_G, "Q1_GATE")
vert2("Device:R", "R15", "100k", q1x, S(145), "Q1_GATE", GNDF, "Resistor_SMD:R_0402_1005Metric")

q2x, q2y = S(105), S(130)
s.place(AO3401A, "Q2", "AO3401A", q2x, q2y, 0,
        footprint="Package_TO_SOT_SMD:SOT-23",
        ref_at=(q2x - S(8), q2y - S(3), 0), value_at=(q2x - S(8), q2y + S(3), 0))
q_pin(AO3401A, q2x, q2y, AO_S, "ALTUSB_VBUS")
q_pin(AO3401A, q2x, q2y, AO_D, "+5V_ALT")
q_pin(AO3401A, q2x, q2y, AO_G, "Q2_GATE")
vert2("Device:R", "R16", "4.7k", S(105), S(145), "DCJACK_VBUS", "Q2_GATE", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R17", "100k", S(114), S(145), "Q2_GATE", GNDF, "Resistor_SMD:R_0402_1005Metric")
# Bulk/bypass cap at the OR'd output node, before +5V_ALT reaches U14
# (power sheet) -- was previously undecoupled all the way from Q1/Q2's
# drains.
vert2("Device:C", "C28", "10uF", S(120), S(160), "+5V_ALT", GNDF, "Capacitor_SMD:C_0805_2012Metric")

# ============ USB-A (J3): host port to interposer SoC ============
J3 = "Connector:USB_A"
j3x, j3y = S(40), S(90)
s.place(J3, "J3", "TE_292303-7", j3x, j3y, 0,
        footprint="Connector_USB:USB_A_TE_292303-7_Horizontal",
        ref_at=(j3x, j3y - S(8), 0), value_at=(j3x, j3y + S(8), 0))
ic_pins(J3, j3x, j3y, {
    "1": "USB1_VBUS_OUT",
    "2": "USBA_HOST_DM",
    "3": "USBA_HOST_DP",
    "4": GNDF,
})
# pin 5 (shield) is 2.54mm beside pin 4, both GND pointing down -- its flag
# text is staggered lower so the two "GND" texts don't collide.
s.flag("GND", s.pin_pos(J3, j3x, j3y, 0, "5"), "I", s.pin_dir(J3, "5"), text_steps=6)

# ============ MicroSD (J4): boot media, MSC0 to interposer SoC ============
J4 = "Connector:Micro_SD_Card"
j4x, j4y = S(40), S(125)
s.place(J4, "J4", "Hirose_DM3D-SF", j4x, j4y, 0,
        footprint="Connector_Card:microSD_HC_Hirose_DM3D-SF",
        ref_at=(j4x, j4y - S(10), 0), value_at=(j4x, j4y + S(10), 0))
ic_pins(J4, j4x, j4y, {
    "1": "MSC0_D2", "2": "MSC0_D3_CD", "3": "MSC0_CMD",
    "4": P3V3F, "5": "MSC0_CLK", "6": GNDF,
    "7": "MSC0_D0", "8": "MSC0_D1", "9": GNDF,
})

# ============ DC power jack (J5): raw 5V input, alternate to USB-C ============
# Pin assignment per Barrel_Jack_Switch generic symbol convention (center
# pin=1, sleeve/GND=2, presence-detect switch=3) -- CONFIRM against the
# actual Wurth 694106301002 datasheet pinout before fab.
J5 = "Connector:Barrel_Jack_Switch"
j5x, j5y = S(40), S(160)
s.place(J5, "J5", "Wuerth_694106301002", j5x, j5y, 0,
        footprint="Connector_BarrelJack:BarrelJack_Wuerth_6941xx301002",
        ref_at=(j5x, j5y - S(6), 0), value_at=(j5x, j5y + S(6), 0))
ic_pins(J5, j5x, j5y, {
    "1": "DCJACK_VBUS",
    "2": GNDF,
    "3": "DCJACK_PRESENT",
})
vert2("Device:R", "R14", "10k", S(85), S(160), P3V3F, "DCJACK_PRESENT", "Resistor_SMD:R_0402_1005Metric")
# Bulk/bypass cap right at the barrel jack -- user-facing external power
# input, previously had zero local capacitance before Q1's source.
vert2("Device:C", "C29", "10uF", S(100), S(160), "DCJACK_VBUS", GNDF, "Capacitor_SMD:C_0805_2012Metric")

# ============ Headphone jack (J6): HPOUTL only, mono per UNIVERSAL.md ============
J6 = "Connector_Audio:AudioJack4_Ground"
j6x, j6y = S(40), S(190)
s.place(J6, "J6", "AudioJack4_Ground", j6x, j6y, 0,
        footprint="Connector_Audio:Jack_3.5mm_PJ320D_Horizontal",
        ref_at=(j6x, j6y - S(6), 0), value_at=(j6x, j6y + S(6), 0))
ic_pins(J6, j6x, j6y, {
    # Full match to 3.3's own J10 (same jack, same footprint) -- verified
    # directly against its PCB netlist, not assumed by generic "sleeve =
    # ground" convention (which is wrong for this part: 3.3 actually grounds
    # R2 and uses S for the mic signal). AudioJack4_Ground's "G" pin (a
    # separate ground LUG) has no matching pad on the real
    # Jack_3.5mm_PJ320D_Horizontal footprint at all -- that part only
    # brings out T/R1/R2/S plus two non-plated mechanical holes -- so it's
    # left unmapped rather than wired to a net with nowhere to land.
    "T": "HPOUTL",
    "R1": "HPOUTL",
    "R2": GNDF,
    "S": "MICLP",
})

# ============ MIPI CSI FFC connectors (J7/J8) ============
# Physical pin-for-pin match to TeaCup(C)3.3's real J13 FFC connector --
# verified directly against 3.3's own PCB netlist (12-30-23-Teacup.kicad_pcb-
# revC.kicad_pcb), NOT the generic "RPi/Arducam" 15-pin CSI convention this
# was originally (wrongly) built to. A sensor module built for 3.3 plugs
# into this exact physical pin mapping; the previous generic version put
# +3V3 on pin 1's neighbor GND, swapped the CLK/D0 lane order, and reversed
# every differential pair's P/N polarity -- pin 1 alone would have put the
# sensor's +3V3 input directly onto this board's GND.
# 3.3 also drives pin 5 (sensor enable) through a 3-pin jumper (its J15:
# GPIO on one end, hardwired +3V3 on the other) rather than a bare GPIO --
# replicated below as JP11/JP12 so the enable line can be tied always-on
# instead of firmware-controlled, same as 3.3.
GEN = "/usr/share/kicad/symbols/Connector_Generic.kicad_sym"
s.ensure_symbol(GEN, "Conn_01x03", "Connector_Generic:Conn_01x03")
JUMPER3_FP = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical_SMD_Pin1Left"

FFC = "teacup-carrier:SFW15R-2STE1LF_C3167933"
for ref, jpref, fy, jpy, pfx in (
    ("J7", "JP11", S(40), S(30), "MIPI0"),
    ("J8", "JP12", S(100), S(90), "MIPI1"),
):
    fx = S(150)
    s.place(FFC, ref, "SFW15R-2STE1LF", fx, fy, 0,
            footprint="teacup-carrier:FPC-SMD_15P-P1.00_SFW15R-2STE1LF",
            ref_at=(fx, fy - S(21), 0), value_at=(fx, fy + S(21), 0))
    ic_pins(FFC, fx, fy, {
        1: P3V3F, 2: f"{pfx}_SCCB_SDA", 3: f"{pfx}_SCCB_SCL", 4: P3V3F,
        5: f"{pfx}_SENSOR_EN", 6: GNDF,
        7: f"{pfx}_CLKP", 8: f"{pfx}_CLKN", 9: GNDF,
        10: f"{pfx}_D1P", 11: f"{pfx}_D1N", 12: GNDF,
        13: f"{pfx}_D0P", 14: f"{pfx}_D0N", 15: GNDF,
        # 16/17 mounting tabs unconnected
    })

    # sensor-enable select jumper (matches 3.3's J15): pin1=GPIO, pin2=the
    # wiper that actually feeds the FPC's pin 5, pin3=+3V3.
    jpx = S(185)
    s.place("Connector_Generic:Conn_01x03", jpref, "EN_SEL", jpx, jpy, 0,
            footprint=JUMPER3_FP,
            ref_at=(jpx + S(4), jpy - S(2), 0), value_at=(jpx + S(4), jpy + S(2), 0))
    ic_pins("Connector_Generic:Conn_01x03", jpx, jpy, {
        "1": f"{pfx}_GPIO", "2": f"{pfx}_SENSOR_EN", "3": P3V3F,
    })

out = s.render("Carrier Physical I O", str(uuid.uuid4()), "/1f26de08-f02d-4283-b132-5069c9b5ce98", "5", paper="A3")
open("/home/administrator/projects/teacup-neo/hw/sheets/io.kicad_sch", "w").write(out)
print("wrote io.kicad_sch,", len(out), "bytes")
