"""Pin-breakout header sheet -- carrier-side labeled 0.1in headers for the
per-SoC GPIO/peripheral superset assigned to J1 pins 87-96 (unit 2 tail) and
97-192 (units 3-4) in build_connector.py. Same system as the approved power/
connector/bmc/io sheets: no wires, global labels matching the connector's
net names carry connectivity across sheets, 50mil grid throughout.

Clustering is a silkscreen/likely-use convenience only (per explicit user
direction) -- these are plain 0.1" pin headers, not a protocol-specific
connector, so a user is free to wire them however they want regardless of
which cluster a signal was grouped into. Each header gets one GND pin (pin 1,
top) for a local scope-ground reference; the header's own net names are
carried in the label text next to each pin, not just the multi-function
silkscreen legend, so both the schematic and the fab silkscreen agree.
"""
import sys, uuid
sys.path.insert(0, '.')
from schgen import Sheet, GRID

GEN = "/usr/share/kicad/symbols/Connector_Generic.kicad_sym"
PWR = "/usr/share/kicad/symbols/power.kicad_sym"

def S(n):
    return round(n * GRID, 2)

s = Sheet()
s.ensure_symbol(PWR, "GND", "power:GND")

LABEL_ANGLE = {"right": 0, "left": 180, "up": 90, "down": 270}

# All J1 net names from build_connector.py's units 2-4 superset assignment --
# every one of these MUST match exactly or the header pin dangles unconnected.
CLUSTERS = [
    # Titles are kept terse (matches the rest of this sheet's style) -- alt-
    # function detail lives in this comment and docs/UNIVERSAL.md SS8, not on
    # the silkscreen: SSI0 pins double as UART0/UART2/SMB1 on some SoCs;
    # PWM0-3 double as SSI1/SMB1/DMIC; SSI1 doubles as PWM0-3/SMB1/DMIC;
    # UART2 doubles as MSC1/DVP on some SoCs; SMB0/SMB1 here are the
    # carrier's GENERAL I2C, kept isolated from the I2C_ID carrier-ID bus.
    ("J20", "GMAC0 (RGMII0)", ["GMAC0_MDIO", "GMAC0_MDCK", "GMAC0_TXCLK", "GMAC0_PHYCLK",
        "GMAC0_TXEN", "GMAC0_TXD0", "GMAC0_TXD1", "GMAC0_RXDV", "GMAC0_RXD0", "GMAC0_RXD1"]),
    ("J21", "GMAC1 (RGMII1, A1 2nd MAC)", ["GMAC1_MDIO", "GMAC1_MDCK", "GMAC1_TXCLK", "GMAC1_PHYCLK",
        "GMAC1_TXEN", "GMAC1_TXD0", "GMAC1_TXD1", "GMAC1_RXDV", "GMAC1_RXD0", "GMAC1_RXD1"]),
    ("J25", "SSI0 (SPI master)", ["SSI0_CLK", "SSI0_DT", "SSI0_DR", "SSI0_CE0", "SSI0_CE1", "SSI0_GPC"]),
    ("J27", "PWM0-7", [f"PWM{i}" for i in range(8)]),
    ("J30", "GPIO0-15 (plain)", [f"GPIO{i}" for i in range(16)]),
    ("J22", "UART0", ["UART0_RXD", "UART0_TXD", "UART0_CTS", "UART0_RTS"]),
    ("J23", "UART2", ["UART2_RXD", "UART2_TXD", "UART2_CTS", "UART2_RTS"]),
    ("J24", "UART3", ["UART3_RXD", "UART3_TXD", "UART3_CTS", "UART3_RTS"]),
    # UART1 is the BMC-ESP32<->J1 management/console link (build_bmc.py),
    # previously carrier-internal only with no external monitoring point --
    # broken out here too per explicit user direction so it can be probed
    # externally, same as UART0/2/3. TX/RX only (no CTS/RTS exist on this
    # link -- it's a plain 2-wire console UART, not flow-controlled).
    ("J36", "UART1 (BMC console)", ["UART1_RX", "UART1_TX"]),
    ("J26", "SSI1", ["SSI1_CLK", "SSI1_DT", "SSI1_DR", "SSI1_CE0"]),
    ("J28", "SAR-ADC", ["SAR_AUX0"]),
    ("J29", "SMB0/SMB1 (general I2C)", ["SMB0_SDA", "SMB0_SCK", "SMB1_SDA", "SMB1_SCK"]),
]

# Spare breakout for every J1 pin left over after the named superset
# clusters above -- explicit user direction: all remaining unused J1 pins
# get broken out to headers too, for future use. Raw SPARE_P<n> labels
# (n = the literal J1 connector pin number) carry straight through from
# build_connector.py's unit4 tail (170-192) and units 5-6 (193-288, entirely
# spare) -- grouped by connector unit for traceability, not by any assumed
# function, since these are genuinely undefined-purpose pins.
SPARE_CLUSTERS = [
    # P170-172 claimed for the HPOUTL/MICLP audio pair + its GND bracket
    # (see build_connector.py) -- excluded here same as every other named
    # signal, not left in the spare breakout.
    ("J31", "J1 SPARE (P173-192)", [f"SPARE_P{p}" for p in range(173, 193)]),
    ("J32", "J1 SPARE (P193-216)", [f"SPARE_P{p}" for p in range(193, 217)]),
    ("J33", "J1 SPARE (P217-240)", [f"SPARE_P{p}" for p in range(217, 241)]),
    ("J34", "J1 SPARE (P241-264)", [f"SPARE_P{p}" for p in range(241, 265)]),
    ("J35", "J1 SPARE (P265-288)", [f"SPARE_P{p}" for p in range(265, 289)]),
]

COLA_X = S(40)
COLB_X = S(160)
COLC_X = S(280)
COLD_X = S(400)
COL_X = {"A": COLA_X, "B": COLB_X, "C": COLC_X, "D": COLD_X}
COL_ORDER = {"J20": "A", "J21": "A", "J25": "A", "J27": "A", "J30": "A",
             "J22": "B", "J23": "B", "J24": "B", "J26": "B", "J28": "B", "J29": "B", "J36": "B",
             "J31": "C", "J32": "C", "J33": "C",
             "J34": "D", "J35": "D"}

# Headers converted from single-row to double-row per explicit user
# direction: pin ORDER stays exactly the CLUSTERS/SPARE_CLUSTERS signal
# order (already J1-pin-sequential -- see module docstring), just laid
# into a Conn_02xNN_Odd_Even footprint instead of Conn_01xNN. KiCad's
# Odd_Even numbering (pin1=row1/col1, pin2=row1/col2, pin3=row2/col1, ...)
# means consecutive pin numbers already alternate the two rows one
# height-step at a time, so "assign signals in J1 order to consecutive
# pin numbers" is sufficient to get a physically zigzagged, non-crossing
# breakout -- no separate reordering pass needed.
DOUBLE_ROW = {"J20", "J21", "J25", "J27", "J30", "J31", "J32", "J33", "J34", "J35"}

def header_geometry(ref, signals):
    """Resolve lib_id/footprint/pin-count for ref, loading the symbol (so its
    real pin cache is available) as a side effect. A double-row header needs
    an EVEN total pin count (2 pins per row); when GND+signals is odd, a
    second GND pin is appended at the far end (bottom-right, per explicit
    user direction) rather than leaving a pin unconnected."""
    double = ref in DOUBLE_ROW
    base_n = len(signals) + 1  # +1 GND reference pin at the top
    second_gnd = double and (base_n % 2 == 1)
    n = base_n + 1 if second_gnd else base_n
    if double:
        rows = n // 2
        symname = f"Conn_02x{rows:02d}_Odd_Even"
        fp = f"Connector_PinHeader_2.54mm:PinHeader_2x{rows:02d}_P2.54mm_Vertical"
    else:
        symname = f"Conn_01x{n:02d}"
        fp = f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical"
    lib_id = f"Connector_Generic:{symname}"
    s.ensure_symbol(GEN, symname, lib_id)
    # Real pin-cache extent, not a hand-rolled formula -- a Conn_02xNN
    # symbol's origin isn't always the vertical midpoint of its pin field
    # (true whenever the row count is even), so deriving visual_top/bottom
    # from the actual loaded pins is correct for both 1- and 2-row symbols
    # instead of assuming symmetry. Symbol-space y is up; schematic y is
    # down (unrotated placement), hence the sign flip.
    pins = s.pin_cache[lib_id]
    top_off = -max(p[3] for p in pins)
    bot_off = -min(p[3] for p in pins)
    return lib_id, fp, n, second_gnd, top_off, bot_off

def place_header(ref, title, signals, x, y_center):
    # KiCad schematic Y increases DOWNWARD -- "visual_top" is the SMALLER
    # coordinate, "visual_bottom" the LARGER one. Getting this backwards
    # once already put the cluster title on top of the reference designator
    # (caught by rendering a PDF and looking at it, not by the automated
    # checkers -- check_overlaps.py only knows about labels/properties, not
    # plain (text) elements).
    lib_id, fp, n, second_gnd, top_off, bot_off = header_geometry(ref, signals)
    visual_top = y_center + top_off
    visual_bottom = y_center + bot_off
    s.place(lib_id, ref, f"HDR_{ref}", x, y_center, 0, footprint=fp,
            ref_at=(x + S(3), visual_bottom + S(2), 0),
            value_at=(x + S(3), visual_top - S(2), 0))
    s.text(title, x - S(2), visual_top - S(5), 0, size=1.5, bold=True)
    # pin 1 = GND reference; pins 2..len(signals)+1 = signals, top to bottom;
    # a trailing 2nd GND (if needed to fill out the double-row footprint)
    # lands on the last pin number, which Odd_Even numbering always puts at
    # the opposite (bottom-right) corner from pin 1.
    p1 = s.pin(lib_id, x, y_center, 0, "1")
    d1 = s.pin_dir(lib_id, "1")
    s.flag("GND", p1, ref[1:], d1)
    for i, sig in enumerate(signals):
        p = s.pin(lib_id, x, y_center, 0, str(i + 2))
        d = s.pin_dir(lib_id, str(i + 2))
        s.label(sig, p[0], p[1], LABEL_ANGLE[d], global_=True)
    if second_gnd:
        pn = s.pin(lib_id, x, y_center, 0, str(n))
        dn = s.pin_dir(lib_id, str(n))
        s.flag("GND", pn, ref[1:], dn)

# Stack each column top-to-bottom (in CLUSTERS list order) with a running
# cursor tracking the smallest unused y so far, sized to each header's
# actual pin count so nothing overlaps regardless of cluster size.
TOP_MARGIN = S(25)
cursors = {"A": TOP_MARGIN, "B": TOP_MARGIN, "C": TOP_MARGIN, "D": TOP_MARGIN}
GAP = S(10)
for ref, title, signals in CLUSTERS + SPARE_CLUSTERS:
    col = COL_ORDER[ref]
    x = COL_X[col]
    _, _, _, _, top_off, bot_off = header_geometry(ref, signals)
    top_pad = S(5)  # room for the title text above visual_top
    y_center = cursors[col] + top_pad - top_off  # solves visual_top == cursor + top_pad
    place_header(ref, title, signals, x, y_center)
    cursors[col] = y_center + bot_off + GAP

out = s.render("Pin Breakout Headers", str(uuid.uuid4()), "/2a3f9c11-6b4d-4e5a-9c3e-headers000001", "6", paper="A2")
open("/home/administrator/projects/teacup-neo/hw/sheets/headers.kicad_sch", "w").write(out)
print("wrote headers.kicad_sch,", len(out), "bytes")
