"""BMC section -- connectivity by label per BUILD.md, same system as the
approved power sheet: every pin carries a net label or a power flag placed
directly on it (flags rotated parallel to the pin), no wires, everything
on the 50mil grid. Pin exit directions come from the symbol's own pin
angles via s.pin_dir(), not hand-guessed."""
import sys, uuid
sys.path.insert(0, '.')
from schgen import Sheet, GRID

TC = "/home/administrator/projects/teacup-neo/hw/teacup-carrier.kicad_sym"
DEV = "/usr/share/kicad/symbols/Device.kicad_sym"
PWR = "/usr/share/kicad/symbols/power.kicad_sym"

def S(n):
    return round(n * GRID, 2)

s = Sheet()
s.ensure_symbol(TC, "ESP32-S3-WROOM-1", "teacup-carrier:ESP32-S3-WROOM-1")
s.ensure_symbol(TC, "TPS2053BDR", "teacup-carrier:TPS2053BDR")
s.ensure_symbol(TC, "TS5A3166DBVR", "teacup-carrier:TS5A3166DBVR")
s.ensure_symbol(TC, "SSSS711403", "teacup-carrier:SSSS711403")
s.ensure_symbol(TC, "DIP8_NOR_SOCKET", "teacup-carrier:DIP8_NOR_SOCKET")
s.ensure_symbol(TC, "W25Q32JVSS", "teacup-carrier:W25Q32JVSS")
s.ensure_symbol(TC, "TCA9555PWR", "teacup-carrier:TCA9555PWR")
s.ensure_symbol(DEV, "R", "Device:R")
s.ensure_symbol(DEV, "C", "Device:C")
s.ensure_symbol(PWR, "GND", "power:GND")
s.ensure_symbol(PWR, "+3V3", "power:+3V3")

LABEL_ANGLE = {"right": 0, "left": 180, "up": 90, "down": 270}
# nets that stay local to this sheet (everything else is global). U8_EN is
# now HOSTED_RESET and crosses to J1 -- the interposer SoC needs to be able
# to hard-reset the co-processor per ESP-Hosted's own reference wiring
# (its "Reset" signal ties straight to the co-processor's EN/RST pin, not
# a GPIO), so it can no longer stay local.
LOCAL_NETS = {"U8_BOOT", "ESP32_CONSOLE_RX", "ESP32_CONSOLE_TX", "EXP_INT"}

def pin_net(pin_xy, net, direction):
    s.label(net, pin_xy[0], pin_xy[1], LABEL_ANGLE[direction],
            global_=net not in LOCAL_NETS)

def ic_pin(lib_id, x, y, num, spec):
    """Label or flag a pin of an unrotated IC, direction taken from the
    symbol's own pin geometry. spec: net name, ("flag", kind), or None."""
    if spec is None:
        return
    p = s.pin(lib_id, x, y, 0, str(num))
    d = s.pin_dir(lib_id, str(num))
    if isinstance(spec, tuple):
        s.flag(spec[1], p, "B", d)
    else:
        pin_net(p, spec, d)

def vert2(lib, ref, val, x, y, top, bottom, fp):
    s.place(lib, ref, val, x, y, 0, footprint=fp,
            ref_at=(x + S(4), y - S(1), 0), value_at=(x + S(4), y + S(1), 0))
    for pn, spec, d in (("1", top, "up"), ("2", bottom, "down")):
        p = s.pin(lib, x, y, 0, pn)
        if isinstance(spec, tuple):
            s.flag(spec[1], p, "B", d)
        else:
            pin_net(p, spec, d)

GNDF = ("flag", "GND")
P3V3F = ("flag", "+3V3")

# ============ ESP32-S3-WROOM-1 (U8) ============
U8 = "teacup-carrier:ESP32-S3-WROOM-1"
u8x, u8y = S(60), S(46)
# ref goes beside the top-left corner, not centered above -- the top-center
# pin (3V3_ALWAYS, pin 2) carries an upward label there.
s.place(U8, "U8", "ESP32-S3-WROOM-1-N16R2", u8x, u8y, 0,
        footprint="teacup-carrier:ESP32-S3-WROOM-1",
        ref_at=(u8x - S(24), u8y - S(34), 0), value_at=(u8x, u8y + S(34), 0))

U8_PINS = {
    1: GNDF, 40: None, 41: None,    # pins 1/40/41 share one point; one flag covers all three
    2: "+3V3_ALWAYS",               # top pin, exits up
    3: "HOSTED_RESET",              # EN -- R8 pull-up AND ESP-Hosted's host-driven
                                     # reset line (must be open-drain on the SoC side)
    4: "I2C_PWR_SDA", 5: "I2C_PWR_SCL",
    6: "I2C_ID_SDA", 7: "I2C_ID_SCL",
    8: "HOSTED_SPI_CLK", 9: "HOSTED_SPI_MOSI",     # ESP-Hosted full-duplex SPI to interposer
    10: "UART1_TX", 11: "UART1_RX",
    12: "BOOTSEL",
    13: "BMC_USB_DM", 14: "BMC_USB_DP",   # now via dedicated J9, not J2
    15: "RESET_EN",
    16: "SW5V_EN_ALT",               # GPIO select: alt-branch load switch (U14) -- native, margin testing
    17: "SFC_IO3", 18: "SFC_CS", 19: "SFC_IO0",
    20: "SFC_CLK", 21: "SFC_IO1", 22: "SFC_IO2",
    23: "HOSTED_SPI_MISO", 24: "HOSTED_SPI_CS",    # ESP-Hosted full-duplex SPI to interposer
    25: "HOSTED_HANDSHAKE",          # ESP-Hosted: co-processor -> host, data-ready-to-send
    26: "HOSTED_DATA_READY",         # ESP-Hosted: co-processor -> host, packet pending
    27: "U8_BOOT",                  # GPIO0/BOOT strap, R9 pull-up
    28: "EXP_INT",                   # U15 (TCA9555) interrupt, active low
    29: None, 35: None,              # spare
    30: "EN_CS_U4", 31: "EN_CS_U5",  # native, margin testing
    32: "USB_OC1", 33: "USB_OC2", 34: "USB_OC3",   # native -- fast overcurrent response
    36: "ESP32_CONSOLE_RX", 37: "ESP32_CONSOLE_TX",
    38: "SW5V_EN_BMC", 39: "VCORE_SNS",   # GPIO select: BMC-branch load switch (U4) -- native, margin testing
}
for num, spec in U8_PINS.items():
    ic_pin(U8, u8x, u8y, num, spec)

# +3V3_ALWAYS decouplers + boot straps as passive islands
vert2("Device:C", "C21", "10uF", S(130), S(20), "+3V3_ALWAYS", GNDF, "Capacitor_SMD:C_0805_2012Metric")
vert2("Device:C", "C22", "100nF", S(139), S(20), "+3V3_ALWAYS", GNDF, "Capacitor_SMD:C_0402_1005Metric")
vert2("Device:R", "R8", "10k", S(148), S(20), P3V3F, "HOSTED_RESET", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R9", "10k", S(157), S(20), P3V3F, "U8_BOOT", "Resistor_SMD:R_0402_1005Metric")

# ============ Dual-NOR CS-select: 2x TS5A3166 analog switch ============
TS = "teacup-carrier:TS5A3166DBVR"
for ref, y, no_net, in_net in (("U9", S(50), "NOR_U4_CE", "EN_CS_U4"),
                               ("U10", S(74), "NOR_U5_CE", "EN_CS_U5")):
    tx = S(140)
    s.place(TS, ref, "TS5A3166", tx, y, 0, footprint="Package_TO_SOT_SMD:SOT-23-5",
            ref_at=(tx, y - S(6), 0), value_at=(tx, y + S(6), 0))
    ic_pin(TS, tx, y, 1, no_net)      # NO
    ic_pin(TS, tx, y, 2, "SFC_CS")    # COM
    ic_pin(TS, tx, y, 3, GNDF)        # GND
    ic_pin(TS, tx, y, 4, in_net)      # IN
    ic_pin(TS, tx, y, 5, P3V3F)       # V+

# ============ Manual override switch (SW1, Alps SSSS711403) ============
SW = "teacup-carrier:SSSS711403"
swx, swy = S(140), S(104)
s.place(SW, "SW1", "SSSS711403", swx, swy, 0,
        footprint="teacup-carrier:SW-TH_SSSS711403",
        ref_at=(swx, swy + S(4), 0), value_at=(swx, swy + S(6), 0))
ic_pin(SW, swx, swy, 1, "SW_SENSE_1")
ic_pin(SW, swx, swy, 3, GNDF)
ic_pin(SW, swx, swy, 4, "SW_SENSE_4")
# pins 2/5/6 deliberately NC per the confirmed datasheet pinout

vert2("Device:R", "R10", "10k", S(160), S(104), P3V3F, "SW_SENSE_1", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R11", "10k", S(169), S(104), P3V3F, "SW_SENSE_4", "Resistor_SMD:R_0402_1005Metric")

# ============ Manual power-override switch (SW2, Alps SSSS711403) ============
# Same structural pattern as SW1: pole (pin 3) is a FIXED rail, the two
# throws are the signals it gets connected to -- not the other way around
# (an earlier version had the pole carrying the signal and one throw tied
# to GND, which collapsed to on-off-off: that throw was electrically
# indistinguishable from center's own pulldown-default-low state whenever
# GPIO wasn't actively fighting it). Now genuinely ON-OFF-ON:
#   throw1 -> EN_SW_BMC : force the BMC branch (U4) on
#   center               : neither forced, GPIO (through its own series
#                           resistor on the power sheet) has full control,
#                           defaults off via pulldown -- same safe idle
#                           state as before
#   throw4 -> EN_SW_ALT : force the ALT branch (U14) on
# Pole sourced from +5V_ALT rather than +3V3_ALWAYS so the ALT-forcing
# throw -- the one that matters most, since it's the only one useful when
# the BMC's own USB-C is unpowered -- works without needing J9 plugged in.
# Trade-off: the BMC-forcing throw is a no-op unless an alt source is also
# present to supply the pole. Accepted -- if BMC power is the only source
# present, forcing it onto +5V_SW is only ever wanted with firmware
# running anyway (you're already talking to the ESP32 to know to do it),
# so it's not a hardware-only scenario the way the ALT case is.
#
# Pole (pin 3) ties straight to +5V_ALT -- no gating jumper. The digipot
# first-power-up overvoltage risk this used to guard against (JP1 + a
# mandatory bring-up checklist, see git history) is now handled by the
# VCORE/VDDR voltage-select jumpers on the power sheet instead: with FB
# routed to a fixed preset divider rather than the digipot, VCORE/VDDR are
# hardware-deterministic regardless of what SW2 does or what's in the
# digipot's NV memory. The user sets those jumpers by hand for whichever
# interposer is seated -- that manual step is what makes it safe to remove
# this gate.
SW2 = "teacup-carrier:SSSS711403"
sw2x, sw2y = S(140), S(220)
s.place(SW2, "SW2", "SSSS711403", sw2x, sw2y, 0,
        footprint="teacup-carrier:SW-TH_SSSS711403",
        ref_at=(sw2x, sw2y + S(4), 0), value_at=(sw2x, sw2y + S(6), 0))
ic_pin(SW2, sw2x, sw2y, 1, "EN_SW_BMC")
ic_pin(SW2, sw2x, sw2y, 3, "+5V_ALT")
ic_pin(SW2, sw2x, sw2y, 4, "EN_SW_ALT")
# pins 2/5/6 deliberately NC per the confirmed datasheet pinout

# ============ Primary NOR flash (U13, soldered SOIC-8 W25Q32JVSS) ============
# Matches the reference teacup-t41 board's U4/U5 pair: both NOR chips share
# the same SFC bus (CLK/DI/DO/IO2/IO3 tied together) with independent CE
# lines, selected via the TS5A3166 GPIO muxes (U9/U10) or SW1's manual
# override -- not multiplexed data, just CS arbitration, same as reference.
SOIC_NOR = "teacup-carrier:W25Q32JVSS"
n4x, n4y = S(140), S(132)
s.place(SOIC_NOR, "U13", "W25Q32JVSS", n4x, n4y, 0,
        footprint="Package_SO:SOIC-8_5.23x5.23mm_P1.27mm",
        ref_at=(n4x - S(10), n4y - S(10), 0), value_at=(n4x - S(10), n4y - S(8), 0))
ic_pin(SOIC_NOR, n4x, n4y, 1, "NOR_U4_CE")  # ~CS
ic_pin(SOIC_NOR, n4x, n4y, 2, "SFC_IO1")    # DO
ic_pin(SOIC_NOR, n4x, n4y, 3, "SFC_IO2")    # IO2
ic_pin(SOIC_NOR, n4x, n4y, 4, GNDF)         # GND (bottom)
ic_pin(SOIC_NOR, n4x, n4y, 5, "SFC_IO0")    # DI
ic_pin(SOIC_NOR, n4x, n4y, 6, "SFC_CLK")    # CLK
ic_pin(SOIC_NOR, n4x, n4y, 7, "SFC_IO3")    # IO3
ic_pin(SOIC_NOR, n4x, n4y, 8, P3V3F)        # VCC (top)
vert2("Device:C", "C24", "100nF", n4x + S(22), n4y, P3V3F, GNDF, "Capacitor_SMD:C_0402_1005Metric")

# ============ Carrier DIP8 NOR socket (U11, recovery/alternate flash) ============
DIP = "teacup-carrier:DIP8_NOR_SOCKET"
dx, dy = S(140), S(160)
s.place(DIP, "U11", "DIP-8 Socket", dx, dy, 0,
        footprint="Package_DIP:DIP-8_W7.62mm_Socket",
        ref_at=(dx - S(10), dy - S(10), 0), value_at=(dx - S(10), dy - S(8), 0))
ic_pin(DIP, dx, dy, 1, "NOR_U5_CE")   # ~CS
ic_pin(DIP, dx, dy, 2, "SFC_IO1")     # DO
ic_pin(DIP, dx, dy, 3, "SFC_IO2")     # IO2
ic_pin(DIP, dx, dy, 4, GNDF)          # GND (bottom)
ic_pin(DIP, dx, dy, 5, "SFC_IO0")     # DI
ic_pin(DIP, dx, dy, 6, "SFC_CLK")     # CLK
ic_pin(DIP, dx, dy, 7, "SFC_IO3")     # IO3
ic_pin(DIP, dx, dy, 8, P3V3F)         # VCC (top)
vert2("Device:C", "C25", "100nF", dx + S(22), dy, P3V3F, GNDF, "Capacitor_SMD:C_0402_1005Metric")

# ============ USB power switch (U12, TPS2053BDR) ============
TPS = "teacup-carrier:TPS2053BDR"
tx, ty = S(140), S(192)
s.place(TPS, "U12", "TPS2053BDR", tx, ty, 0,
        footprint="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        ref_at=(tx, ty - S(9), 0), value_at=(tx, ty + S(9), 0))
U12_PINS = {
    1: GNDF, 5: GNDF,
    2: "+5V_SW", 6: "+5V_SW",   # was dangling (USB1/2_VBUS_IN, tied to nothing) -- real fix
    3: "USB_EN1", 4: "USB_EN2", 7: "USB_EN3",
    11: "USB3_VBUS_OUT", 14: "USB2_VBUS_OUT", 15: "USB1_VBUS_OUT",
    12: "USB_OC3", 13: "USB_OC2", 16: "USB_OC1",
    # 8, 9, 10 NC per datasheet
}
for num, spec in U12_PINS.items():
    ic_pin(TPS, tx, ty, num, spec)

# ============ GPIO expander (U15, TCA9555PWR) ============
# Frees 9 native ESP32 GPIOs (USB_EN1-3, PG_SW5V/VCORE/SW5V_ALT, SW_SENSE_1/4,
# DCJACK_PRESENT) for the ESP-Hosted SPI link -- all slow status/enable
# signals with no real timing requirement, unlike flash chip-select and the
# power-domain switching GPIOs, which stay native for margin testing.
# Shares I2C_PWR (carrier-local, digipot's own bus), not I2C_ID -- putting
# it on the interposer-crossing bus would reintroduce the exact fault-
# coupling the digipot/ID-EEPROM bus split exists to avoid. Address pins
# grounded -> 0x20, doesn't collide with MCP4661's 0x28-range address.
EXP = "teacup-carrier:TCA9555PWR"
ex, ey = S(190), S(140)
s.place(EXP, "U15", "TCA9555PWR", ex, ey, 0,
        footprint="Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm",
        ref_at=(ex - S(16), ey - S(24), 0), value_at=(ex - S(16), ey - S(22), 0))
ic_pin(EXP, ex, ey, 1, "EXP_INT")
ic_pin(EXP, ex, ey, 2, GNDF)     # A1
ic_pin(EXP, ex, ey, 3, GNDF)     # A2
ic_pin(EXP, ex, ey, 4, "USB_EN1")
ic_pin(EXP, ex, ey, 5, "USB_EN2")
ic_pin(EXP, ex, ey, 6, "USB_EN3")
ic_pin(EXP, ex, ey, 7, "PG_SW5V")
ic_pin(EXP, ex, ey, 8, "PG_VCORE")
ic_pin(EXP, ex, ey, 9, "PG_SW5V_ALT")
ic_pin(EXP, ex, ey, 10, "SW_SENSE_1")
ic_pin(EXP, ex, ey, 11, "SW_SENSE_4")
ic_pin(EXP, ex, ey, 12, GNDF)
ic_pin(EXP, ex, ey, 13, "DCJACK_PRESENT")
# pins 14-20 (P11-P17) deliberately NC -- spare I/O for future use
ic_pin(EXP, ex, ey, 21, GNDF)    # A0
ic_pin(EXP, ex, ey, 22, "I2C_PWR_SCL")
ic_pin(EXP, ex, ey, 23, "I2C_PWR_SDA")
ic_pin(EXP, ex, ey, 24, P3V3F)
vert2("Device:C", "C26", "100nF", ex, ey + S(35), P3V3F, GNDF, "Capacitor_SMD:C_0402_1005Metric")

# I2C_ID bus pull-ups (crosses J1 to whichever interposer's own EEPROM is
# seated, SS7 -- master on ESP32 GPIO6/7). Live on the carrier, not the
# interposer, because the carrier side is always populated regardless of
# which (or whether any) interposer is plugged in. 4.7k to +3V3.
vert2("Device:R", "R41", "4.7k", S(166), S(20), P3V3F, "I2C_ID_SDA", "Resistor_SMD:R_0402_1005Metric")
vert2("Device:R", "R42", "4.7k", S(175), S(20), P3V3F, "I2C_ID_SCL", "Resistor_SMD:R_0402_1005Metric")

out = s.render("BMC - ESP32-S3", str(uuid.uuid4()), "/0f27921f-7420-42c8-af54-47a231c1828e", "4", paper="A3")
open("/home/administrator/projects/teacup-neo/hw/sheets/bmc.kicad_sch", "w").write(out)
print("wrote bmc.kicad_sch,", len(out), "bytes")
