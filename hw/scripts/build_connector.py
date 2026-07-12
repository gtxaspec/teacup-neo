"""DDR4 UDIMM-288 connector section -- connectivity by label per BUILD.md,
same system as the approved power/bmc sheets: flags directly on power pins
(parallel to the pin, value text in-row), labels directly on signal pins,
no wires, 50mil grid throughout."""
import sys, uuid
sys.path.insert(0, '.')
from schgen import Sheet, GRID

TC = "/home/administrator/projects/teacup-neo/hw/teacup-carrier.kicad_sym"
PWR = "/usr/share/kicad/symbols/power.kicad_sym"

def S(n):
    return round(n * GRID, 2)

s = Sheet()
s.ensure_symbol(TC, "AH58893-T9B10-3F", "teacup-carrier:AH58893-T9B10-3F")
s.ensure_symbol(PWR, "GND", "power:GND")
CONN = "teacup-carrier:AH58893-T9B10-3F"

LABEL_ANGLE = {"right": 0, "left": 180, "up": 90, "down": 270}

def unit_pin(ux, uy, unit, num, spec):
    if spec is None:
        return
    p = s.pin_pos(CONN, ux, uy, 0, str(num))
    d = s.pin_dir(CONN, str(num))
    if spec == "GND":
        s.flag("GND", p, "C", d)
    else:
        # RESERVED_* pins are placeholders local to this sheet; the rest
        # cross to other sections and stay global.
        s.label(spec, p[0], p[1], LABEL_ANGLE[d],
                global_=not spec.startswith("RESERVED_"))

# ============ Unit 1 (pins 1-48): infrastructure crossings ============
u1x, u1y = S(40), S(56)
s.place(CONN, "J1", "AH58893-T9B10-3F", u1x, u1y, 0, unit=1,
        footprint="teacup-carrier:DDR4288S0511H_UDIMM288",
        ref_at=(u1x, u1y - S(26), 0), value_at=(u1x, u1y + S(26), 0))

UNIT1 = {
    1: "VCORE", 2: "VCORE", 3: "VCORE", 4: "VCORE",
    5: "GND", 6: "GND", 7: "GND", 8: "GND",
    9: "VDDR", 10: "VDDR",
    11: "GND", 12: "GND",
    13: "+3V3", 14: "+3V3",
    15: "+1V8", 16: "+1V8",
    17: "+5V_MODEA", 18: "+5V_MODEA",
    19: "GND", 20: "GND", 21: "GND", 22: "GND",
    23: "I2C_ID_SDA", 24: "I2C_ID_SCL",
    25: "VCORE_SNS",
    26: "BOOTSEL",
    27: "RESET_EN",
    28: "SFC_CS", 29: "SFC_CLK",
    30: "SFC_IO0", 31: "SFC_IO1", 32: "SFC_IO2", 33: "SFC_IO3",
    34: "UART1_TX", 35: "UART1_RX",
    36: "GND", 37: "GND", 38: "GND", 39: "GND", 40: "GND",
}
# Pins 41-48: explicitly reserved -- the per-SoC GPIO/peripheral superset
# mapping is a separate task (docs/UNIVERSAL.md SS8 geography-first rule);
# labeled placeholders keep them visible without inventing assignments.
for p in range(41, 49):
    UNIT1[p] = f"RESERVED_P{p}"
# 41/42 carry the shared USB host data pair (J2 alt-USB-C + J3 USB-A, same
# logical port) across to the interposer SoC -- placed next to the pin
# 36-40 GND run for flanking. Not RESERVED: these are live global nets.
UNIT1[41] = "USBA_HOST_DP"
UNIT1[42] = "USBA_HOST_DM"
# 43-48: ESP-Hosted full-duplex SPI (BMC ESP32-S3 -> interposer SoC), using
# up the last of unit 1's reserved pins. No spare pins left for GND
# flanking here (unit 1 is now fully populated); the pin 36-40 GND run
# sits 1-3 positions away, which is what real physical adjacency on the
# connector allows -- same caveat as the MIPI/MSC0 crossing.
UNIT1[43] = "HOSTED_SPI_CLK"
UNIT1[44] = "HOSTED_SPI_MOSI"
UNIT1[45] = "HOSTED_SPI_MISO"
UNIT1[46] = "HOSTED_SPI_CS"
UNIT1[47] = "HOSTED_HANDSHAKE"
UNIT1[48] = "HOSTED_DATA_READY"

for num, spec in UNIT1.items():
    unit_pin(u1x, u1y, 1, num, spec)

# ============ Unit 2 (pins 49-96): microSD + headphone + 2x MIPI camera ============
u2x, u2y = S(110), S(56)
s.place(CONN, "J1", "AH58893-T9B10-3F", u2x, u2y, 0, unit=2,
        ref_at=(u2x, u2y - S(26), 0), value_at=(u2x, u2y + S(26), 0))

UNIT2 = {
    # microSD bus -- GND bracketing the whole group, plus CLK specifically
    # sandwiched between two GND pins for a clean return path on the
    # highest-frequency single-ended line in this group.
    49: "GND", 50: "MSC0_CLK", 51: "GND",
    52: "MSC0_CMD", 53: "MSC0_D0", 54: "MSC0_D1", 55: "MSC0_D2", 56: "MSC0_D3_CD",
    57: "GND",
    # Headphone -- sensitive analog, isolated on both sides.
    58: "HPOUTL",
    59: "GND",
    # MIPI0: GPIO/SCCB (low-speed control, no special isolation needed)
    # then each D-PHY differential pair gets its own GND immediately before
    # it, separating it from its neighbor -- the pair itself (N/P) stays
    # adjacent since splitting a differential pair with GND would break the
    # coupling it needs, not help it.
    60: "MIPI0_GPIO", 61: "MIPI0_SCCB_SDA", 62: "MIPI0_SCCB_SCL",
    63: "GND", 64: "MIPI0_D0N", 65: "MIPI0_D0P",
    66: "GND", 67: "MIPI0_D1N", 68: "MIPI0_D1P",
    69: "GND", 70: "MIPI0_CLKN", 71: "MIPI0_CLKP",
    72: "GND",
    # MIPI1: same pattern.
    73: "MIPI1_GPIO", 74: "MIPI1_SCCB_SDA", 75: "MIPI1_SCCB_SCL",
    76: "GND", 77: "MIPI1_D0N", 78: "MIPI1_D0P",
    79: "GND", 80: "MIPI1_D1N", 81: "MIPI1_D1P",
    82: "GND", 83: "MIPI1_CLKN", 84: "MIPI1_CLKP",
    85: "GND",
}
# ESP-Hosted's host-driven reset line -- ties straight to the BMC ESP32-S3's
# own EN/RST pin (HOSTED_RESET on the bmc sheet), not a GPIO. Host side must
# drive it open-drain (only pulls low) so it doesn't fight R8's pull-up.
UNIT2[86] = "HOSTED_RESET"
# 87-96: primary GMAC (RGMII, T-series MAC position -- T31/T40 reduced
# 2-bit-per-direction convention per their own GPIO mux tables, not full
# 4-bit RGMII) -- exactly fills what was RESERVED_P87-96, first of the
# pin-breakout superset (docs/UNIVERSAL.md SS8), heads straight to the
# GMAC0 header cluster on the new headers sheet.
GMAC0 = ["GMAC0_MDIO", "GMAC0_MDCK", "GMAC0_TXCLK", "GMAC0_PHYCLK", "GMAC0_TXEN",
         "GMAC0_TXD0", "GMAC0_TXD1", "GMAC0_RXDV", "GMAC0_RXD0", "GMAC0_RXD1"]
for p, sig in zip(range(87, 97), GMAC0):
    UNIT2[p] = sig

for num, spec in UNIT2.items():
    unit_pin(u2x, u2y, 2, num, spec)

# ============ Unit 3 (pins 97-144): UART0/2/3 + 2nd GMAC (A1) + SSI0/1 + PWM ============
# Pin-breakout superset per docs/UNIVERSAL.md SS8 ("break out every signal/GPIO
# socket pin to labeled 0.1in headers... ~180 sig superset"), sourced from the
# real per-SoC GPIO mux tables (T31-H.3 GPIO Specification for UART0/SSI0/SSI1/
# PWM/SMB1; T40 IP Camera GPIO Recommended Allocation Table for UART2/UART3 and
# the GMAC pin set; A1 GPIO recommended allocation table for the 2nd RGMII MAC,
# confirming A1 dual-GMAC is real hardware, not a naming guess). UART4/UART5
# do NOT exist on any T-series/A1 SoC in this family (checked -- only the much
# older JZ47xx application-processor line has them), so despite the earlier
# "UART2-5" cluster name floated before this pass, only UART0/UART2/UART3 are
# populated; no UART4/UART5 signals are invented. DVP, JTAG, SATA, HDMI stay
# interposer-local per SS8/SS10 -- none of those pins appear here.
u3x, u3y = S(180), S(56)
s.place(CONN, "J1", "AH58893-T9B10-3F", u3x, u3y, 0, unit=3,
        ref_at=(u3x, u3y - S(26), 0), value_at=(u3x, u3y + S(26), 0))

UNIT3 = {97: "GND"}
def fill(start, names):
    for i, n in enumerate(names):
        UNIT3[start + i] = n

fill(98, ["UART0_RXD", "UART0_TXD", "UART0_CTS", "UART0_RTS"])
UNIT3[102] = "GND"
fill(103, ["UART2_RXD", "UART2_TXD", "UART2_CTS", "UART2_RTS"])
UNIT3[107] = "GND"
fill(108, ["UART3_RXD", "UART3_TXD", "UART3_CTS", "UART3_RTS"])
UNIT3[112] = "GND"
fill(113, ["GMAC1_MDIO", "GMAC1_MDCK", "GMAC1_TXCLK", "GMAC1_PHYCLK", "GMAC1_TXEN",
           "GMAC1_TXD0", "GMAC1_TXD1", "GMAC1_RXDV", "GMAC1_RXD0", "GMAC1_RXD1"])
UNIT3[123] = "GND"
fill(124, ["SSI0_CLK", "SSI0_DT", "SSI0_DR", "SSI0_CE0", "SSI0_CE1", "SSI0_GPC"])
UNIT3[130] = "GND"
fill(131, ["SSI1_CLK", "SSI1_DT", "SSI1_DR", "SSI1_CE0"])
UNIT3[135] = "GND"
fill(136, [f"PWM{i}" for i in range(8)])
UNIT3[144] = "GND"

for num, spec in UNIT3.items():
    unit_pin(u3x, u3y, 3, num, spec)

# ============ Unit 4 (pins 145-192): SAR-ADC + general SMB/I2C + plain GPIO ============
# SAR_AUX0 matches the T41 reference board's dedicated ADC_AUX0 pin (old/docs/
# t31zx_teacup_pinuse.csv pin 32) -- a single-channel analog input outside the
# GPIO mux tables on every SoC checked, not a multi-channel SADC. SMB0/SMB1 here
# are the carrier's GENERAL system I2C headers -- kept electrically separate
# from I2C_ID_SDA/SCL (unit 1, pins 23/24, the carrier-ID EEPROM bus), same
# isolation principle already used for VGA/HDMI DDC on the A1 interposer (SS10).
# GPIO0-15 are plain unclaimed superset pins for whatever's left after every
# named peripheral above -- deliberately generic, not tied to a specific SoC
# pin identity, since "remaining plain GPIO" is itself one of the user's
# approved header clusters. Pins 170-192 (23 pins), plus all of units 5-6
# below (193-288, 96 pins), were originally left unconnected on the "ground
# is fill, not fixed overhead" theory (SS8) -- superseded by explicit user
# direction: break ALL remaining J1 pins out to headers too, for future use.
# Each becomes a raw SPARE_P<n> global label carrying the literal connector
# pin number (not a guessed function) straight to a spare-header cluster on
# the headers sheet -- these consume no GND-fill budget of their own since
# each spare header's single reference GND pin ties to the board's common
# GND net, not a unique J1 position.
u4x, u4y = S(250), S(56)
s.place(CONN, "J1", "AH58893-T9B10-3F", u4x, u4y, 0, unit=4,
        ref_at=(u4x, u4y - S(26), 0), value_at=(u4x, u4y + S(26), 0))

UNIT4 = {145: "GND", 146: "SAR_AUX0", 147: "GND"}
fill_u4_start = 148
UNIT4[148] = "SMB0_SDA"
UNIT4[149] = "SMB0_SCK"
UNIT4[150] = "SMB1_SDA"
UNIT4[151] = "SMB1_SCK"
UNIT4[152] = "GND"
for i in range(16):
    UNIT4[153 + i] = f"GPIO{i}"
UNIT4[169] = "GND"
for p in range(170, 193):
    UNIT4[p] = f"SPARE_P{p}"

for num, spec in UNIT4.items():
    unit_pin(u4x, u4y, 4, num, spec)

# ============ Units 5-6 (pins 193-288): spare breakout, all SPARE_P<n> ============
positions = [(S(110), S(130)), (S(180), S(130))]
for i, (ux, uy) in enumerate(positions, start=5):
    s.place(CONN, "J1", "AH58893-T9B10-3F", ux, uy, 0, unit=i,
            ref_at=(ux, uy - S(26), 0), value_at=(ux, uy + S(26), 0))
    lo = 193 + (i - 5) * 48
    for p in range(lo, lo + 48):
        unit_pin(ux, uy, i, p, f"SPARE_P{p}")

out = s.render("DDR4 UDIMM-288 Connector", str(uuid.uuid4()), "/016abe51-c097-4611-854e-0af763646499", "3", paper="A3")
open("/home/administrator/projects/teacup-neo/hw/sheets/connector.kicad_sch", "w").write(out)
print("wrote connector.kicad_sch,", len(out), "bytes")
