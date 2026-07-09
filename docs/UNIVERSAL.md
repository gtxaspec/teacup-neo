# Teacup Universal — modular Ingenic dev platform

A two-board architecture that lets one baseboard host **any** Ingenic T-series /
A1 SoC by swapping a small per-SoC module. Package (QFN88 / QFN96 / BGA232 / …)
stops mattering — each SoC's package-specific fanout is absorbed by its module,
which presents a standard edge to a common socket.

- **Interposer** — the per-SoC module: SoC + package fanout + decoupling + clock
  + (optional) local power + (optional) NOR + straps, presented on an MXM3 edge.
- **Carrier** — the universal baseboard: MXM3 socket + all peripherals + full
  pin breakout + 5V input + adjustable SoC power.

Terminology note: "interposer" = SoC module; "carrier" = baseboard. (Reversed
from some earlier notes — this doc is canonical.)

---

## 1. Connector: MXM 3.0 (314-pin, 0.5 mm card edge)

Chosen over Socket 370 (module needs machined pins — cost lands on the part you
build most), mezzanine stacks (delicate for bench swapping), and SODIMM (fewer
pins). MXM3 gives the pin count of a big PGA with the module side costing
**nothing** — gold fingers, not connectors.

| Property | Value |
|---|---|
| Contacts | 314 (157/face, odd-even split across faces) |
| Pitch | 0.5 mm, single row per face (no pad-to-pad routing needed) |
| Module PCB | **1.2 mm** thick, edge fingers hard-gold (Ni/Au) + 20° bevel |
| Socket | latching, SMT, ~$3–8 (Foxconn/ACES on LCSC) |
| Signalling headroom | PCIe Gen3 rated → our worst case (MIPI ~1.5 Gbps, RGMII 125 MHz) is trivial |

We use MXM3 **mechanically only** — the electrical pinout is ours to define
(section 8). Fingers escape perpendicular on their own layer; vias stagger back
1–2 mm in 2–3 ranks. 4-layer carrier suffices (no PCIe/DDR crossing the edge).

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

| Rail | T10/T20 | T21 | T23 | T30* | T31 | T32 | T33 | T40 | T41 | A1 |
|---|---|---|---|---|---|---|---|---|---|---|
| **VDD core** | 1.1 | 1.0 | 0.8 | ~1.0 | 0.8 | 0.8 | 0.9 | 0.9 | 0.8 | 0.9 |
| **DDR** (VDDMEM/DDRVDD) | 1.8 | 1.8/1.5 | 1.8/1.5 | 1.8/1.5 | 1.8/1.5/1.35 | 1.5/1.35 | 1.35/1.5/1.8 | 1.35 | 1.35/1.5/1.8 | 1.8 |
| **+1.8 V** analog/IO | DVP only† | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 |
| **+3.3 V** IO | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 | 3.3 |
| **+0.9 V** analog (PLL_VDD/USB_09/CSI_09) | 1.1 | 1.0 | 0.8 | ~1.0 | 0.8 | 0.8 | 0.9 | 0.9 | int‡ | 0.9 |
| EFUSE (burn only) | **2.5** | 1.5 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 | 1.8 |

\* T30 = envelope estimate (datasheet didn't extract cleanly; sits between T23/T31).
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

Superset = union across the biggest package (BGA232): ~PA×32 + PB×32 + PC×~21
≈ 100 GPIO, + analog block (2× CSI 4-lane for T40/T41 dual-sensor, USB, audio,
SADC), + straps, + power/GND (generous — 30-40 GND for returns). ≈ 160–190
signals → fits 314 with headroom. (Dual 4-lane CSI *and* full DVP16
simultaneously would push ~240 and argue for MXM3-314's full width.)

**Assign geography-first, not by GPIO bank order:** place the carrier floorplan
(connector + peripheral connectors), then assign the 314 positions so nets exit
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
- Exact **T30** rails + currents (datasheet didn't extract; envelope only, sits
  between T23/T31). **T20 is confirmed** — based on the **T10 datasheet** (same
  silicon: core 1.1 V, DDR 1.8 V, analog on 3.3 V, EFUSE 2.5 V, VDDCORE/VDDMEM
  ≥1 A), per the table above.

**Deferred (decide later):**
- Whether to break out **dual 4-lane CSI + DVP16 simultaneously** — the one
  requirement that could push the pinout past 314. Single CSI block fits with
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
lifted onto an MXM3 edge.
