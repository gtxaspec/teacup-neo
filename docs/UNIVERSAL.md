# Teacup Universal — modular Ingenic dev platform

A two-board architecture that lets one baseboard host **any** Ingenic T-series /
A1 SoC by swapping a small per-SoC module. Package (QFN88 / QFN96 / BGA232 / …)
stops mattering — each SoC's package-specific fanout is absorbed by its module,
which presents a standard edge to a common socket.

- **Interposer** — the per-SoC module: SoC + package fanout + decoupling + clock
  + (optional) local power + (optional) NOR + straps, presented on a card edge (SO-DIMM-260, §1).
- **Carrier** — the universal baseboard: card-edge socket + all peripherals + full
  pin breakout + 5V input + adjustable SoC power.

Terminology note: "interposer" = SoC module; "carrier" = baseboard. (Reversed
from some earlier notes — this doc is canonical.)

---

## 1. Connector: 0.5 mm card edge (DDR4 SO-DIMM-260 primary, MXM3-314 backup premium)

A **card-edge** connector: module side = gold fingers (a fab option, $0 parts),
socket on the carrier. Chosen over Socket 370 (module needs machined pins — cost
on the part you build most) and mezzanine stacks (delicate for bench swapping).
Fingers escape perpendicular on their own layer; single row per face, so no
pad-to-pad routing. We use it **mechanically only** — the pinout is ours (§8).
4-layer carrier suffices (no PCIe/DDR crossing the edge).

**Two viable sockets, same 0.5 mm edge; the interposer mates either** (design the
carrier footprint for one, the card is universal):

| | **DDR4 SO-DIMM — 260-pin (primary)** | **MXM 3.0 — 314-pin (backup premium)** |
|---|---|---|
| Contacts | 260 | 314 |
| Pitch | 0.5 mm | 0.5 mm |
| Card thickness | **1.0 mm** | 1.2 mm |
| Cost | **~$0.83–1.67** | ~$10.69–17 |
| LCSC / JLCPCB | **deep multi-SKU stock → auto-placeable, sustained** | last 25 of a discontinued part → hand-solder |
| In-stock parts | **Foxconn ASAA821-E8SB0-7H** (C2925427, 183 stock, ~$1); Foxconn ASAA821-EARB0-7H (C225725); LOTES ADDR0075-P001C (C2926865) | Amphenol 10151114-001TLF (5.0 mm, first-tier); ATTEND 125B-78C00 (~1.1k @ DigiKey) |
| Headroom | ~65 ground after full superset | ~119 ground |

**Why SO-DIMM is primary:** ~10× cheaper (~$1 vs ~$15), **deep multi-SKU LCSC
stock** (JLCPCB-assemblable, *sustained* — DDR4 laptop-RAM market is enormous),
first-tier makers (Foxconn/LOTES), and its 260 pins are **enough** (§8: ~180 sig +
15 pwr + 65 gnd). **MXM3-314 is the backup premium** — a fading laptop-GPU part
(JAE discontinued, ACES 0-stock, only 25 units on LCSC), kept only for the case
where you want the ~54 spare grounds and don't mind hand-soldering an Amphenol
socket. Same 0.5 mm edge either way; only the card thickness (1.0 vs 1.2 mm) and
carrier footprint differ, so a design can be re-spun between them.

**Footprints / links:**
- **DDR4 SO-DIMM Foxconn ASAA821-E8SB0-7H** (183 stock, EasyEDA footprint on LCSC): <https://lcsc.com/product-detail/Memory-Connector-DDR_FOXCONN-ASAA821-E8SB0-7H_C2925427.html>
- MXM3 Amphenol 10151114-001TLF footprint+symbol: <https://www.snapeda.com/search/?q=10151114-001TLF&search-type=parts>
- MXM3 JAE MM70-314B1-2-R300 on LCSC (last 25): <https://www.lcsc.com/product-detail/C4818180.html>
- Pick the SO-DIMM socket **orientation** (right-angle = card lies flat, standard,
  low-profile) and **stack height** (~4.0 / 5.2 / 8.0 mm) to match the interposer
  standoff — same mechanical decision you'd make for MXM3.

**Interposer mechanical:**
- **PCB thickness = 1.0 mm ±0.1** (the SO-DIMM card-edge spec; MXM3 = 1.2 mm).
  Hard requirement — too thick won't seat / spreads the contacts, too thin =
  intermittent. It's a standard JLCPCB/PCBWay thickness (4-layer at 1.0 mm is fine).
- **Edge geometry is fixed by the socket:** the gold-finger row (~130/face at
  0.5 mm ≈ 65 mm span → ~68 mm card width), the DDR4 **key notch** at the JEDEC
  position, and the two **side latch cut-outs** so the socket grips + latches.
  Copy these from the SO-DIMM mechanical drawing.
- **Depth + component layout are ours** — the card only needs to be as deep
  (~20–30 mm) as fits the SoC island. Put the SoC + tall parts (NOR SOIC ~1.75 mm,
  buck inductor ~1.2 mm, crystal ~0.8 mm) on the **top** face; keep the bottom
  (toward the carrier) low-profile. The socket floats the card above the carrier
  at its stack height, so ~1.75 mm tall parts clear easily.

---

## 2. Power architecture

The SoC core and DDR voltages are **SoC-specific** (section 3); everything else
(1.8 V, 3.3 V) is universal. That single fact drives the whole power design.

Two build modes, supported by **one connector** via bidirectional VCORE/VDDR:

| Mode | Interposer holds | Carrier holds | Result |
|---|---|---|---|
| **A — self-contained** | SoC, clock, decap, **own bucks**, straps, (NOR) | 5V, peripherals, breakout | boots on any carrier or bare on the bench |
| **B — minimal** | SoC, clock, decap, straps | **adjustable VCORE+VDDR**, peripherals | dead-simple module, needs its carrier to boot |

**The contract:** VCORE and VDDR are bidirectional connector nets. Exactly **one
driver per rail per build** — either the interposer's buck *or* the carrier's
adjustable buck, never both. Stuffing decides. 1.8 V / 3.3 V are always carrier-
sourced (universal). This lets cheap dumb interposers and premium self-contained
ones share the same baseboard.

Hard SI rules (why the interposer can't just draw everything across the edge):
- **Decoupling is mandatory on the interposer**, within mm of the SoC balls,
  vias straight to plane. A cap behind the connector's per-pin inductance is
  useless above a few MHz.
- **Clock stays on the interposer.** EXCLK_XIN/XOUT are high-Z oscillator nodes;
  routing them through fingers + socket kills 24 MHz startup margin. RTC 32.768k
  crystal too, where used.
- In mode B, the carrier buck should **Kelvin-sense** at the connector and the
  interposer must carry strong local decoupling to cover connector inductance on
  the fast core transient.

---

## 3. SoC input-rail reference (T10 → A1)

Nominal voltages from each SoC's `*_BOARD_DESIGN_GUIDE` / datasheet in
`~/projects/thingino/ingenic-docs`. Core/DDR vary; 1.8/3.3 are universal.

| Rail | T10/T20 | T21 | T23 | T30 | T31 | T32 | T33 | T40 | T41 | A1 |
|---|---|---|---|---|---|---|---|---|---|---|
| **VDD core** | 1.1 | 1.0 | 0.8 | 1.0 | 0.8 | 0.8 | 0.9 | 0.9 | 0.8 | 0.9 |
| **DDR** (VDDMEM/DDRVDD) | 1.8 | 1.8/1.5 | 1.8/1.5 | 1.8 | 1.8/1.5/1.35 | 1.5/1.35 | 1.35/1.5/1.8 | 1.35 | 1.35/1.5/1.8 | 1.8 |
| **+1.8 V** analog/IO | DVP only† | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 |
| **+3.3 V** IO | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 |
| **+0.9 V** analog (PLL_VDD/USB_09/CSI_09) | 1.1 | 1.0 | 0.8 | 1.0 | 0.8 | 0.8 | 0.9 | 0.9 | int‡ | 0.9 |
| EFUSE (burn only) | **2.5** | 1.5 | 1.8 | **1.5** | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 |

T30 confirmed from `T30 ... Data Sheet.20180416`: core 1.0 V, DDR 1.8 V (DDR2),
1.8 analog, 3.3 IO, RTC 1.0 V, EFUSE 1.5 V.
† **T10/T20 is the outlier** — 65 nm-era: core 1.1 V, analog (ADC/CODEC/PLL-HV) on
**3.3 V** not 1.8, EFUSE 2.5 V. It only uses 1.8 for the DVP sensor.
‡ On **SIP-QFN** parts (T31ZX, T41NQ/XQ) the 0.8–0.9 V analog sub-rails are
internal — not externally supplied. A1 and the older/non-SIP parts expose them.

DDR notes: value depends on the SoC's DDR variant (DDR2 = 1.8, DDR2L/DDR3 = 1.5,
DDR3L / T31A / T40 / T41 = 1.35). All target SoCs except the DDR3 spins are SIP,
so DDRVDD feeds the in-package die — no external DDR bus, but the rail is still
required at the right voltage.

Analog sub-rails (USB_AVD33/18/09, PLL_AVDD, CSI_VCC, CODEC_AVDD, and A1's
VGA/HDMI_AVDD) are the **same voltages** as the main rails but must be
**bead-isolated** (1 kΩ@100 MHz) separate nets — they are their own domains for
test/probe purposes (section 6).

---

## 4. Regulator spec (sized to the worst SoC)

Current minimums are stated in the board design guides (VDDCORE: T40/T41/A1 say
≥2A, T10–T31 say ≥1A; VDDMEM: all say ≥1A). Analog rails spec bead isolation
(tens of mA each) — aggregates below are conservative.

| Rail | Voltage | Max current | Ripple | Regulator |
|---|---|---|---|---|
| **VCORE** | 0.8–1.1 V adj | **2 A** (T40/T41/A1) | ≤60 mVpp | Adjustable buck **≥3 A**, FB-set by interposer (e.g. MP2143/MP2315-class) |
| **VDDR** | 1.35–1.8 V adj | **1 A** | ≤70 mVpp | Adjustable buck **≥1.5 A** (SY8089-class ok) |
| **+1.8 V** | 1.8 V | ~0.5 A | low | buck/LDO ≥1 A |
| **+3.3 V** | 3.3 V | ~0.5 A SoC + peripherals | low | buck **≥2 A** (shared w/ carrier peripherals) |
| **+0.9 V analog** | 0.8–0.9 V | ~0.15 A | low | tiny LDO **on the interposer** (A1/old only; internal on SIP-QFN) |
| EFUSE program | 1.5 / 1.8 / 2.5 V | <50 mA one-shot | — | jumper-fed pad, **not** a continuous reg |
| **+5 V in** | 5 V | ~1.5 A SoC + peripherals → **spec ≥3 A** | — | barrel or USB-C |

**The two that matter on the carrier: an adjustable ≥3 A VCORE buck + an
adjustable ≥1.5 A VDDR buck**, both voltage-programmed by a feedback resistor on
the interposer (plug T41 → 0.8 V, T40 → 0.9 V, T20 → 1.1 V; auto-set). The 2 A
XBurst2 core requirement is what sets the VCORE size — a T41-only board could use
2 A (as teacup-neo does with SY8089), but universal must carry the worst case.

---

## 5. Clock, flash, boot

- **Clock**: 24 MHz crystal + 1 M start + 33 R series on the **interposer**, tight
  to the SoC. RTC 32.768 kHz crystal on the interposer where the SoC has RTC.
- **NOR flash — dual location, optional on the interposer**:
  - 8-pad SPI NOR (W25Q-class) footprint on the interposer = **optional stuff**.
  - Carrier carries its own NOR too.
  - **Only the CS0 device is bootable**, and two flashes can't share CS0. So the
    boot flash owns CS0; the other is disconnected or demoted to a GPIO-CS as
    software-only storage (the Teacup SW2 CS-disconnect switch is the precedent).
  - Populate interposer NOR + flip CS-disconnect → module boots from its own
    flash = **self-contained** (mode A). Leave it empty → boots from carrier NOR
    = **dependent** (works with this carrier). The stuffing *is* the mode choice.
  - SFC bus (CLK + IO0-3 + CS ≈ 6 pins) crosses the connector to reach carrier
    NOR; keep the stub short or series-terminate at speed.
  - Free recovery: bootrom order **SFC → SD → USB**, so no-flash-found drops to
    SD then USB-boot on its own.

---

## 6. Bench test pads (per isolated domain)

For standalone bring-up / external-PSU injection when testing an interposer off
the carrier. Placed on the SoC side of each rail's bead/0R so a domain can be
isolated and injected. Per **isolated domain**, not per voltage — because a
fault in the USB PHY vs the core digital should be distinguishable:

`VCORE · VCORE-analog(0.9) · VDDR · +1.8-digital · +1.8-analog · +3.3-digital ·
+3.3-USB(USB_AVD33) · +5V · GND · EFUSE-program`

~7 rail pads for a fully-isolated interposer; a couple collapse into the chip on
SIP-QFN parts. A1 (USB ×3 + VGA + HDMI islands) is the worst case for pad count.

---

## 7. Carrier ID

A small **I2C EEPROM** (or 3–4 resistor-strapped ID pins) on the interposer so:
- software auto-selects the right DFU / flash / DT profile;
- in mode B, the carrier reads the ID and sets the adjustable VCORE/VDDR (or the
  interposer just FB-sets them directly with a resistor — simpler, no firmware).

---

## 8. Pin breakout & superset pinout

**Break out every signal/GPIO socket pin to labeled 0.1" headers** on the carrier
(skip only 5V/GND). Whatever interposer is plugged in, its live pins are all
accessible — this is the point of a bench board.

**Both 314 and 260 are sufficient.** A1 and T40 are BGA356/381, but balls ≠
connector signals: most balls are power/ground distribution and (on external-DDR
variants) the ~90-ball DDR bus — **none of which cross the connector** (DDR routes
local to the SoC on the interposer). Actual external signal counts: **T40 ~120
GPIO** (PA–PD, from datasheet mux table) + ~30 analog (2× CSI, USB, audio, SADC) ≈
150; T41 BGA232 ~130; A1 adds ~25 unique (HDMI/VGA/DSI). Superset ≈ **~180 sig**.

**Ground is *fill*, not fixed overhead** — only signals (~180) and power (~15,
current-driven) are committed; every remaining pin becomes ground, and
more-is-better. So the budget is: `committed = signals + power`, `ground = total −
committed`:

| | signals | power | committed | ground (fill) | SI (need ≥1 GND/3 sig) |
|---|---|---|---|---|---|
| **SO-DIMM-260**, full superset | ~180 | ~15 | ~195 | **~65** | good (~1 GND/3 sig) |
| SO-DIMM-260, camera-only (no A1) | ~145 | ~15 | ~160 | ~100 | excellent |
| MXM3-314, full superset | ~180 | ~15 | ~195 | ~119 | luxurious (backup) |

So **260 pins clears the *full* superset** (incl. A1 video) with ~65 grounds —
enough for 1.5 Gbps MIPI + 125 MHz RGMII. 314 just buys spare grounds we don't
strictly need. The only thing that would exceed 260 is a 1-GND-per-signal scheme
(overkill at our speeds) or dual-CSI+DVP16 simultaneous (+~36, deferred §9).
**Escape valve:** A1 (video-out) and the T-cameras never share an interposer, so
their mutually-exclusive peripherals can occupy the **same** connector positions
if it ever gets tight. No single
interposer needs every peripheral of every SoC at once.

**Assign geography-first, not by GPIO bank order:** place the carrier floorplan
(connector + peripheral connectors), then assign the 260 positions so nets exit
the socket already pointed at their destination — USB fingers by the USB jacks,
MIPI pairs by the FFC, MSC0 by the SD slot, GPIO banks by their headers. Rules:
- each MIPI pair on **adjacent fingers, same face**, GND finger each side;
- all high-speed on **one contact row** (escapes on one layer);
- power pins **clustered** at one end (5V pour is a blob, not a snake).

---

## 9. Open / deferred / decided

**Open:**
- **Peripheral 3.3/1.8 source**: carrier-local reg off 5V (keeps interposer
  SoC-only) — assumed yes; confirm.
- **VCORE remote-sense** wiring in mode B (transient response).
- Rail table is now **confirmed for the whole family** — T20 via the T10
  datasheet (same silicon), T30 via its own datasheet. Only unstated number left
  is T30's exact core current (no board design guide); assumed ≥1 A per the
  XBurst1 norm and covered by the ≥3 A universal VCORE spec regardless.

**Deferred (decide later):**
- Whether to break out **dual 4-lane CSI + DVP16 simultaneously** — the one
  requirement that could push the pinout past 260. Single CSI block fits with
  headroom; revisit if multi-sensor (T40/T41) becomes a target use case.

**Decided:**
- This is an **independent design** — the pinout is ours, NOT constrained to be
  mateable with Ingenic's TOMCAT / vendor core-board convention. MXM3 is used
  mechanically only.

---

## References

All in `~/projects/thingino/ingenic-docs`: per-SoC `HDK/*_BOARD_DESIGN_GUIDE`,
`HDK/*Hardware Design Checklist`, and `Datasheets/*` (source of the rail table).
`MARK_C90_MAIN_V2_0_QFN96` informed teacup-neo's T41 power tree. teacup-neo (this
repo) is the first single-SoC (T41) proof; the interposer is its SoC section
lifted onto a SO-DIMM-260 card edge.
