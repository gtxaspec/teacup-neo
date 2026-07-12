# Teacup Universal — modular Ingenic dev platform

A two-board architecture that lets one baseboard host **any** Ingenic T-series /
A1 SoC by swapping a small per-SoC module. Package (QFN88 / QFN96 / BGA232 / …)
stops mattering — each SoC's package-specific fanout is absorbed by its module,
which presents a standard edge to a common socket.

- **Interposer** — the per-SoC module: SoC + package fanout + decoupling + clock
  + (optional) local power + (optional) NOR + straps, presented on a card edge (DDR4 UDIMM-288, §1).
- **Carrier** — the universal baseboard: card-edge socket + all peripherals + full
  pin breakout + 5V input + adjustable SoC power.

Terminology note: "interposer" = SoC module; "carrier" = baseboard. (Reversed
from some earlier notes — this doc is canonical.)

---

## 1. Connector: DDR4 UDIMM-288 card-edge socket (in use for this build)

A **card-edge** connector: module side = gold fingers (a fab option, $0 parts),
socket on the carrier. Chosen over Socket 370 (module needs machined pins — cost
on the part you build most) and mezzanine stacks (delicate for bench swapping).
Fingers escape perpendicular on their own layer; single row per face, so no
pad-to-pad routing. We use it **mechanically only** — the pinout is ours (§8).
4-layer carrier suffices (no PCIe/DDR crossing the edge).

**This build uses the DDR4 UDIMM-288 desktop socket.** §1a below keeps the
SO-DIMM-260 / MXM3-314 comparison and part numbers on file — the card-edge
approach is shared across all three, so re-spinning to a different socket later
(e.g. a compact camera-only build on SO-DIMM-260) reuses everything in this
section except the connector footprint and edge geometry.

**Part: Foxconn AH58893-T9B10-3F** (LCSC **C42403003**, SMD vertical, 288-position,
0.85 mm pitch). Verified on LCSC 2026-07-10: **738 in stock**, $1.93 (1+) down to
$1.26 (100+), EasyEDA footprint + symbol available for conversion to KiCad. Premium
alt if this part ever dries up: Amphenol FCI **DDR4288V0213TF** (Mouser
523-DDR4288V0213TF) — pin-compatible DDR4 UDIMM-288 socket, drop-in mechanical
substitute.

**Why UDIMM-288:** most capable and most forgiving option for a do-everything
bench that must host **A1 + SATA**. **0.85 mm pitch** (coarsest of the three
options in §1a) makes the edge fingers easiest to fab and the contacts most
robust. **288 pins → ~93 grounds**, the headroom that keeps A1's SATA (3 Gbps) +
HDMI TMDS and dual 2-lane MIPI cleanly flanked. A **heavy-duty high-cycle socket**
built for constant re-insertion, and the bigger card gives the BGA parts (A1
BGA356, T40) room to fan out. **JLCPCB-assemblable with real, verified stock** —
the deciding factor over the fine-pitch MXM3-314 (JAE discontinued, effectively
unsourceable) and the more compact SO-DIMM-260 (still viable — kept on file in
§1a for a future compact re-spin, but 288 already clears the full superset with
margin, so there's no reason to carry two connector footprints through this
build). Trade-off accepted: **~133 mm socket length**, full-width card latch at
both ends, can't be shortened — the carrier and interposer run large. That size
is the price of the margin.

**Footprint / symbol:**
- **Foxconn AH58893-T9B10-3F**: <https://www.lcsc.com/product-detail/C42403003.html> — pull the EasyEDA footprint + symbol from this page and convert to KiCad (same workflow as the QFN96 and FFC footprints built for the T41 board — see `old/hw/teacup.pretty/`).
- Premium alt **Amphenol FCI DDR4288V0213TF**: <https://www.mouser.com/ProductDetail/523-DDR4288V0213TF>
- Socket **orientation: vertical** (card stands up, desktop-RAM style — matches "interposer plugs into carrier like a DIMM"). **Stack height** TBD once the carrier floorplan sets component clearance underneath.

**Interposer mechanical:**
- **PCB thickness = 1.0 mm ±0.1** (DDR4 UDIMM card-edge spec). Hard requirement —
  too thick won't seat / spreads the contacts, too thin = intermittent. Standard
  JLCPCB/PCBWay thickness; 4–6 layer at 1.0 mm is fine.
- **Edge geometry is fixed by the socket:** gold-finger row (144/face at 0.85 mm ≈
  122 mm span → ~133 mm card width), the DDR4 **UDIMM key notch** at its JEDEC
  position, and the **side latch cut-outs**. Copy from the DDR4 UDIMM mechanical
  drawing.
- **Depth + component layout are ours** — the card only needs to be as deep
  (~20–30 mm) as fits the SoC island. Put the SoC + tall parts (NOR SOIC ~1.75 mm,
  buck inductor ~1.2 mm, crystal ~0.8 mm) on the **top** face; keep the bottom
  (toward the carrier) low-profile. The socket floats the card above the carrier
  at its stack height, so ~1.75 mm tall parts clear easily.

### 1a. Other connector options (reference only — not used in this build)

Kept on file in case a future variant re-spins away from UDIMM-288 (e.g. a
compact camera-only build with no A1/SATA target). All three share the
gold-finger card-edge approach; only pitch, length, card thickness, and the
carrier footprint differ.

| | **DDR4 UDIMM-288 desktop (in use)** | **DDR4 SO-DIMM-260 (compact option)** | **MXM3-314 (backup premium)** |
|---|---|---|---|
| Contacts | 288 | 260 | 314 |
| Pitch | **0.85 mm** (coarsest, easiest) | 0.5 mm | 0.5 mm |
| Socket length | ~133 mm (longest) | ~68 mm (compact) | ~90 mm |
| Card thickness | 1.0 mm | 1.0 mm | 1.2 mm |
| Cost | ~$1.3–1.9 | ~$0.83–1.67 | ~$10.69–17 |
| LCSC / JLCPCB | **SMD, 738 stock** (verified) | deep, sustained | last 25, discontinued |
| Ground headroom | **~93** | ~65 | ~119 |
| Trade | rugged + coarse + max-ground, **big board** | compact, cheap | fine pitch, **scarce** |

**SO-DIMM-260 — the compact / JLCPCB-friendly option.** ~68 mm, ~$1, and **the
deepest, most sustained LCSC stock of the three** (verified thousands: Foxconn
ASAA821-E8SB0-7H C2925427, AS0A826-H2SB-7H C2761525). Its 260 pins still clear the
full superset (~180 sig + 15 pwr + 65 gnd, §8), so a **camera-only build** (no A1
SATA/HDMI) is ideal on 260 — smaller, cheaper, fully JLCPCB-built. Re-spin to this
when A1 isn't a target.

**MXM3-314 — backup premium.** A fading laptop-GPU part (JAE discontinued, ACES
0-stock, only 25 on LCSC), kept for when you want max grounds and don't mind
hand-soldering an Amphenol socket. Fine 0.5 mm pitch, ~90 mm.

**Footprints / links:**
- **DDR4 SO-DIMM Foxconn ASAA821-E8SB0-7H** (compact build; EasyEDA footprint on LCSC): <https://lcsc.com/product-detail/Memory-Connector-DDR_FOXCONN-ASAA821-E8SB0-7H_C2925427.html> — also AS0A826-H2SB-7H (C2761525, ~2800 stock)
- MXM3 Amphenol 10151114-001TLF footprint+symbol: <https://www.snapeda.com/search/?q=10151114-001TLF&search-type=parts>; JAE MM70-314B1-2-R300 (LCSC C4818180, last 25)

**If re-spinning to SO-DIMM-260:** edge geometry becomes ~130/face at 0.5 mm ≈
65 mm → ~68 mm card width, SO-DIMM key notch (distinct JEDEC position from
UDIMM). Card thickness stays 1.0 mm ±0.1. MXM3-314 uses 1.2 mm card thickness and
its own notch/latch geometry per the Amphenol/JAE mechanical drawing.

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
- **Sensor MIPI crosses the socket to carrier camera FFC(s) — and it's budgeted.**
  §8 already puts **2× CSI (dual 2-lane MIPI) in the 260 superset** on a carrier FFC,
  with ~65 grounds to spare — so cameras on the carrier is the default, not a pin
  problem. It crosses fine: D-PHY here is 1.5 Gbps/lane (T33/T40) to 2 Gbps/lane
  (T41), and **both sockets are qualified well past that** — DDR4 SO-DIMM passes
  DDR4-3200 (~1.6 GHz differential DQS + 3.2 GT/s DQ), MXM3 carries 8 GT/s PCIe Gen3
  — with flanking-ground pairs + length match. An interposer **may also** carry its
  own camera FFC (optional) for a self-contained mode-A module or the shortest
  sensor channel, but — unlike the clock below — it is **not required** to stay local.
  The only config that overflows 260 is dual 2-lane MIPI **plus** a full 16-bit DVP
  broken out simultaneously (+~36 pins) — which no single SoC implements (§10); the
  UDIMM-288 / MXM3-314 options exist for that phantom case.
- **Clock stays on the interposer — this one is a hard rule** (unlike MIPI above).
  EXCLK_XIN/XOUT are **high-Z analog oscillator nodes**; socket stub capacitance
  detunes the crystal loop and kills 24 MHz startup margin. Different mechanism from
  a driven, terminated differential link — a connector that passes 8 GT/s PCIe still
  can't carry a pico-amp oscillator node. RTC 32.768k crystal too, where used.
- **Mode-B VCORE sense — no analog remote-sense across the connector.** Putting the
  buck's feedback loop through the socket's finger inductance invites instability,
  and it costs pins. Instead, a three-part scheme that's DC-accurate *and*
  loop-stable:
  1. The carrier buck **Kelvin-senses at the connector** (carrier side) — kills
     the carrier-trace IR drop, keeps the connector out of the control loop.
  2. **Parallel several VCORE + GND fingers** so the connector's DC resistance is
     tiny (≈4 VCORE fingers → ~10 mV drop at 2 A) — within the ±5 % core margin.
  3. **Strong interposer decoupling** carries the *fast* transient. Above the buck's
     loop bandwidth (~100s of kHz) no sense scheme helps — that energy can only
     come from local C, and the connector inductance is why it must be local.
  4. For the residual DC error and for margining, a high-Z **VCORE_SNS** pin runs
     from the interposer point-of-load back to the **BMC ADC** (§9): the BMC reads
     the *true ball voltage* and trims the digipot (§2 above) to hit target —
     **software remote-sense.** Slow, exact, unconditionally stable, and it's the
     same measurement voltage-margining already needs. One connector pin.

**Digital voltage control (digipot) — software-set VCORE/VDDR + margining.** In
mode B, digitize each buck's FB divider with a **dual non-volatile I²C digipot:
MCP4661-104E/ST** (Microchip, TSSOP-14, **100 kΩ**, 257 taps, 2.7–5.5 V supply).
Confirmed direct from the Microchip datasheet; well-stocked at DigiKey
(1,062 units, verified 2026-07-11) — the LCSC listing for this exact TSSOP-14/
100 kΩ combination is thin-to-absent (only a QFN `-T.../ML` tape-and-reel
variant turns up, C144215), so DigiKey is the primary source for this part;
sub any dual-NV I²C pot if BOM sourcing needs a package change.

**Why 100 kΩ, not a lower value:** the pot's three terminals sit directly
across the FB divider (VOUT-to-GND, wiper to FB), so its `RAB` draws a small
continuous current off the rail it's regulating — at 1.8 V (VDDR) that's
**~18 µA on 100 kΩ** vs. ~180 µA on 10 kΩ or ~360 µA on 5 kΩ (the other two
MCP4661 stock options considered, C637131/10 kΩ and C145605/5 kΩ — both also
thin-to-out-of-stock at LCSC). Buck FB-pin bias current is nanoamp-class on
these parts, so 100 kΩ doesn't hurt divider accuracy — it just cuts the pot's
own quiescent draw by 10–20×, which matters since this current runs
continuously on every powered rail, not just during a margining sweep.
257 taps over 100 kΩ ≈ **~390 Ω/step**, still ≈1 mV/step-class resolution
over the VCORE/VDDR span once folded through the ratiometric divider math
below. The **ESP32 BMC** (§9)
sets it, making the whole power path software-defined and unlocking **voltage
margining**: the agent can sweep VCORE to find a SoC's minimum-stable core voltage,
undervolt headroom, and stability margins — real characterization, LLM-driven.
- **Ratiometric** — use the pot as the divider ratio so its ±20% absolute
  tolerance cancels; only the ratio sets voltage.
- **Loop stability** — the wiper R/C sits on the FB node; keep the feed-forward
  cap and check the buck's compensation.
- **Safe sequencing (critical)** — the BMC **sets the digipot *then* enables the
  rail** (load switch / buck EN), so VCORE is never brought up over-voltage on a
  0.8 V part. The NV pot retains its setting across power cycles; the BMC-gated
  enable covers the very first boot. This is the resolution to mode-B FB safety.

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
VGA/HDMI_AVDD plus **SATA0/1_VCC 0.9 V + SATA0/1_VCCH 1.8 V** with a SATA_RBIAS
2 kΩ 1% ref) are the **same voltages** as the main rails but must be
**bead-isolated** (1 kΩ@100 MHz) separate nets — they are their own domains for
test/probe purposes (section 6). The SATA PHY analog rails live on the **A1
interposer** (like all SoC-specific analog), fed from the carrier 0.9/1.8 through
their own beads.

---

## 4. Regulator spec (sized to the worst SoC)

Current minimums are stated in the board design guides (VDDCORE: T40/T41/A1 say
≥2A, T10–T31 say ≥1A; VDDMEM: all say ≥1A). Analog rails spec bead isolation
(tens of mA each) — aggregates below are conservative.

| Rail | Voltage | Max current | Ripple | Regulator |
|---|---|---|---|---|
| **VCORE** | 0.8–1.1 V adj | **2 A** (T40/T41/A1) | ≤60 mVpp | Adjustable buck **≥3 A**, FB-set by interposer — **AP62600SJ-7** (in use; alternatives on file in §4a) |
| **VDDR** | 1.35–1.8 V adj | **1 A** | ≤70 mVpp | Adjustable buck **≥1.5 A**, FB-set by interposer — **AP62300WU-7** (in use; SY8089-class notes on file in §4b) |
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

**VCORE buck part: AP62600SJ-7** (Diodes Incorporated, VQFN2030-12, LCSC
**C4748917**). **4.5–18 V input**, 0.6 V–adj output (0.6 V ±1% reference, standard
external resistive divider — same ratiometric-digipot scheme as §2), **6 A**,
1.2 MHz, full-feature synchronous buck. Datasheet confirmed direct from
Diodes Inc. (DS42003 Rev. 3); sourceable through DigiKey (2,218 in stock,
verified 2026-07-10) and Mouser — LCSC listing exists (same part number, priced)
but was out of stock at last check, so DigiKey is the primary source for now.

Replaces two earlier candidates (both kept below, §4a) after two problems
surfaced in sequence:
1. **MP2315GJ-Z** (first pick) has a **0.8 V output floor** — exactly the nominal
   VCORE for four target SoCs (T23/T31/T32/T41, §3), leaving **zero undervolt
   headroom** for the voltage margining §2 requires. Disqualifying.
2. **MP2143DJ-LF-Z** (second pick) fixes the floor (0.6 V) but its **2.5–5.5 V
   input range** puts `vSafe5V`'s 5.5 V worst case exactly at the top of its
   *recommended* operating range with no buffer against a real-world
   out-of-spec 5 V source (e.g. an unregulated wall wart sitting at 5.6–5.8 V) —
   not an absolute-max violation (abs-max is ~6 V), but outside the
   manufacturer's guaranteed-performance window, an avoidable risk on a bench
   board meant to accept whatever 5 V supply is on hand.

AP62600 solves both at once: **0.6 V floor** (full margining headroom on every
0.8 V-nominal SoC) and **4.5–18 V input** (~12.5 V of margin above the
`vSafe5V` worst case — any plausible "5 V" source is comfortably inside its
rated continuous range). 6 A capability is well past the ≥3 A spec, with room
to spare. One trade-off worth noting: **VQFN2030-12**, not the TSOT23-8 package
of the other two candidates — the interposer/carrier footprint library will
need this land pattern, not a reuse of the SOT23 one.

### 4a. VCORE buck — earlier candidates (reference only, not used in this build)

Kept on file since both were genuinely considered and each remains a valid
option for a future re-spin with different constraints (e.g. a build that
never needs sub-0.8 V margining, or one with a tightly-regulated, known-clean
5 V input where AP62600's extra input headroom buys nothing).

**MP2315GJ-Z** (Monolithic Power Systems, TSOT23-8, LCSC **C45889**). 4.5–24 V
input, 0.8 V–adj output, **3 A**, 500 kHz, current-mode control. Datasheet
confirmed on LCSC; sourceable through DigiKey/Mouser/LCSC. Originally picked
for its wide 4.5–24 V input margin — a nominal 5 V input sits comfortably
mid-range, better than MP2143's tight ceiling. **Disqualified by its 0.8 V
output floor**: exactly the nominal VCORE for T23/T31/T32/T41 (§3), which
leaves no room for the voltage margining §2 requires on those parts. Still a
fine choice for a build that doesn't need to undervolt-margin an 0.8 V-core SoC.

**MP2143DJ-LF-Z** (Monolithic Power Systems, TSOT23-8). 2.5–5.5 V input, 0.6 V–adj
output, 3 A, 1.2 MHz, constant-on-time (COT) control, 40 µA quiescent current.
Also available in a 10-pin QFN (VFDFN) variant. COT control gives faster
transient response and can ease loop compensation versus current-mode control —
worth revisiting if VCORE ripple/transient performance with AP62600 turns out
marginal in bring-up, or for a build with a lower, tightly-regulated input rail
where the 5.5 V ceiling isn't a practical concern (its 0.6 V output floor is
identical to AP62600's, so margining isn't the issue here — input margin is).
Its 5.5 V top-of-range is genuinely within its *rated continuous* operating
window (not a stress condition) — the concern is zero buffer above that line
if the actual 5 V source runs even slightly hot, not that 5.5 V itself is unsafe.

**VDDR buck part: AP62300WU-7** (Diodes Incorporated, TSOT-23-6/TSOT26, LCSC
**C1880390**). **4.2–18 V input**, 0.8 V–adj output (0.8 V ±1% reference,
external resistive divider), **3 A**, 750 kHz, COT synchronous buck. Datasheet
confirmed direct from Diodes Inc.; well-stocked at both DigiKey (5,941 units,
verified 2026-07-10) and LCSC (2,525+ units, JLCPCB-listed) — better supply
position than AP62600's current LCSC gap.

Same family as the VCORE pick (§4 above) for a consistent vendor/footprint/
FB-divider-and-digipot story across both bucks, but right-sized rather than
reusing AP62600: VDDR only needs ≥1.5 A (spec, §4 table) against a 1 A actual
load, so **AP62300's 3 A is ample headroom without the cost/board-space of a
6 A part**, and its wide **4.2–18 V input** gives the same `vSafe5V`-margin
protection as AP62600, for the same reason (§4 above).

**On the 0.8 V floor — not disqualifying here, unlike VCORE.** AP62300's FB
reference is 0.8 V (not the 0.6 V of the AP62600 chosen for VCORE). For VCORE
that floor was disqualifying because it equals several SoCs' *nominal* core
voltage (§3), leaving zero undervolt headroom. VDDR is different: the lowest
DDR nominal across every target SoC is **1.35 V** (DDR3L, §3), so an 0.8 V
floor still leaves **~550 mV (41%) of undervolt headroom** — far more than any
realistic DDR margining sweep needs. No part change required to keep §2's
margining goal intact on this rail.

### 4b. VDDR buck — earlier note (reference only, not used in this build)

**SY8089A1AAC** (Silergy, SOT-23-5) — the part the single-SoC T41 board
(teacup-neo's predecessor / `old/`) used for its VCORE/VDDR supplies at 2 A,
referenced above (§4) for context on why a T41-only board could get away with
a smaller part than the universal platform's worst-case sizing requires. Not
carried forward as the VDDR pick here: it's a **fixed small-current-class**
part family sized for a single known SoC, not chosen against the universal
board's ≥1.5 A / wide-input-margin / FB-digipot-margining requirements the way
AP62300 was — kept on file as the historical reference point, not as a
rejected candidate that was evaluated head-to-head against AP62300.

---

## 5. Clock, flash, boot

- **Clock**: 24 MHz crystal + 1 M start + 33 R series on the **interposer**, tight
  to the SoC. RTC 32.768 kHz crystal on the interposer where the SoC has RTC.
  **Part: Seiko SC-32S** (32.768 kHz, **12.5 pF** load cap, ±20 ppm, SMD3215-2P,
  **0.75 mm** tall, LCSC **C97606**). Datasheet-confirmed spec; LCSC shows
  31,865 in stock (verified 2026-07-11, ~$0.13–0.23/unit). 12.5 pF is the
  de facto standard RTC crystal load cap this family's SoCs are designed
  around (T41's board design guide calls out an external 32.768 kHz clock
  without stating a different value, and 12.5 pF is standard across the
  industry absent a SoC-specific override) — confirm per-SoC if a future
  datasheet specifies otherwise. 0.75 mm height matches the crystal budget
  already assumed in §1's interposer stack-height note. A smaller sibling,
  **Seiko SC-20S** (SMD2012-2P, 0.6 mm, LCSC C97607, 5,045 in stock), is a
  drop-in if a future interposer is tight enough on board space to need it —
  same electrical spec, smaller footprint, just less deep stock.
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
  - **The carrier's own NOR is itself dual — soldered primary + socketed
    alternate — matching the single-board Teacup's U4/U5 precedent exactly,
    not a single fixed chip.** Carrier stuffs a soldered SOIC-8 **W25Q32JVSS**
    (primary, always populated) *and* a DIP-8 socket (alternate/recovery,
    user-populated) on the **same shared SFC bus** (CLK/IO0-3 tied together),
    each with its own independent CE line. CE arbitration is **two
    TS5A3166DBVR** analog switches gated from ESP32 GPIO (§9's flash-select
    row). A 3-position manual switch (**SSSS711403**, same part as the
    reference board's manual CS switch) sits alongside as a *sense* input the
    ESP32 reads to decide which switch to enable — so, unlike the power-source
    override switch below (§9), this selection currently still requires BMC
    firmware to be running; it is not a direct hardware override.

---

## 6. Test points — interposer MVP + carrier instrumentation

**Directive (CaptainRon):** the interposer should carry the minimum to be a
**self-contained testable system off the carrier** — just test pads for a minimum
viable system. Baseline set:
- **USB pads** — the SoC USB (D+/D−/VBUS/GND), for **DFU flashing + USB gadget**
  standalone. The primary bring-up interface: Ingenic parts load firmware via
  bootrom **USB boot / DFU**, so this is how you flash a bare interposer with no
  carrier. Short stub off the USB line (the same USB also crosses the connector to
  the carrier's USB-C); keep the tap short for HS integrity, or castellated pads /
  a micro-USB for convenience.
- **UART pad** — debug console (UART1), to watch boot alongside the USB flash.
- **Flash chip pads** — the 8-pad SPI NOR footprint (boot + direct program).
- **Voltage pads** — power-in / probe for each rail (below).
- **Clock** — the 24 MHz crystal (already local per §5).

With USB + UART + power + NOR, a bare interposer is fully bring-up-able: power it,
**DFU-flash over USB**, watch the console over UART — the complete standalone loop.

Power it, console it, flash it **on the bench with no carrier at all.** This *is*
the self-contained interposer (mode A) — the pads just make bring-up + fault-find
possible before the carrier exists.

**Voltage pads — fuller version (per isolated domain).** For fault-isolation
granularity, place a pad on the SoC side of each rail's bead/0R so a domain can be
isolated and injected — per **isolated domain**, not per voltage:

`VCORE · VCORE-analog(0.9) · VDDR · +1.8-digital · +1.8-analog · +3.3-digital ·
+3.3-USB(USB_AVD33) · +5V · GND · EFUSE-program`

~7 rail pads for a fully-isolated interposer; a couple collapse into the chip on
SIP-QFN parts. A1 (USB ×3 + VGA + HDMI islands) is the worst case for pad count.
For the MVP, the coarse set (VCORE, VDDR, +1.8, +3.3, +5V, GND) is enough.

**Carrier instrumentation (test points throughout).** Beyond the full signal
breakout (§8 — every SoC pin at a labeled header, which doubles as a test point):
- **Power rails** — a labeled probe pad on each carrier rail: +5V, +3.3, +1.8,
  VCORE, VDDR.
- **Buck debug** — bring each buck's **SW (LX) node** and **FB node** to a pad, to
  scope switching ripple / loop behavior during power bring-up.
- **BMC control lines** — BOOTSEL, reset-EN, flash-select, PPRST_ — pads to observe
  or manually override the ESP32.
- **I²C** (digipot + ID EEPROM) — SDA/SCL pads to sniff / bit-bang.
- **Boot straps** — POR_CTL, BOOT_SEL0 pads on both sides.
- **Ground everywhere (the one that matters most)** — scatter **GND probe points
  next to every functional block** (each buck, the SoC/connector, USB, the MIPI
  FFC, the BMC). A scope's ground lead must be short — long leads ruin high-speed
  measurements. Cheap and load-bearing.

**Convention:** every test pad **silkscreen-labeled**, one consistent footprint
(1.0 mm round or a TP part), kept clear of connectors/tall parts so a probe or clip
reaches it. A well-instrumented board debugs in minutes; a bare one costs hours.

---

## 7. Carrier ID

A small **I2C EEPROM** (or 3–4 resistor-strapped ID pins) on the interposer so:
- software auto-selects the right DFU / flash / DT profile;
- in mode B, the carrier reads the ID and sets the adjustable VCORE/VDDR (or the
  interposer just FB-sets them directly with a resistor — simpler, no firmware).

**Part: 24AA025E48T-I/SN** (Microchip, SOIC-8, 2 Kbit / 256×8 I²C EEPROM,
1.7–5.5 V, 400 kHz). Datasheet confirmed direct from Microchip; DigiKey has
13,180 in stock (verified 2026-07-11, $0.40/unit) — the base `24AA025E48-I/SN`
part number is the same die, just a different tape/reel packaging suffix, and
was thin at LCSC (32 units) at last check, so DigiKey is the source for now.

**Why this part over a plain 24C02-class EEPROM:** it's **factory-programmed
with a globally unique 48-bit EUI-48 node address**, permanently burned in and
read-only — a free, guaranteed-unique serial number per interposer with zero
manufacturing-time programming step. That's a direct fit for §9's autonomous/
fleet-management goal: an agent managing many boards (or many interposers
swapped across one carrier over time) can identify *this exact physical
module* over I²C without ever having to assign or track serial numbers itself.
2 Kbit is far more than the ID needs alone, so the remaining user-writable
space holds the DFU/flash/DT profile data and VCORE/VDDR trim/calibration
values §7 already calls for — one part serves both roles. Standard I²C EEPROM
address pins are present too, though moot here since only one interposer is
ever on the bus at a time (§1's "one module seated" rule, §8).

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
150; T41 BGA232 ~130. **A1 is the NVR outlier** (BGA356, 14 mm): its **display-out
(HDMI 2.0 / VGA / RGB-TFT / BT1120 / DSI) shares the camera-zone** with T-series
camera-*in* (mutually exclusive per interposer — no module is both), so display adds
~0 net. Its genuinely-**unique** adds are **dual SATA 3.0** (SATA0/1 = 4 diff pairs
≈ 8 sig), the **2nd RGMII GMAC** (~12 sig; the 1st shares the T-series MAC position),
and 2 extra USB (~8) ≈ **~28 unique**. Superset ≈ **~180 sig** either way — the
display sharing is what keeps A1 in budget; SATA/GbE are the real adds and they fit.

**Ground is *fill*, not fixed overhead** — only signals (~180) and power (~15,
current-driven) are committed; every remaining pin becomes ground, and
more-is-better. So the budget is: `committed = signals + power`, `ground = total −
committed`:

| | signals | power | committed | ground (fill) | SI (need ≥1 GND/3 sig) |
|---|---|---|---|---|---|
| **UDIMM-288 (primary)**, full superset incl A1+SATA | ~180 | ~15 | ~195 | **~93** | very good |
| SO-DIMM-260, full superset | ~180 | ~15 | ~195 | ~65 | good (~1 GND/3 sig) |
| SO-DIMM-260, camera-only (no A1) | ~145 | ~15 | ~160 | ~100 | excellent |
| MXM3-314, full superset | ~180 | ~15 | ~195 | ~119 | luxurious (backup) |

So the **UDIMM-288 primary clears the full superset** (incl. full A1 with SATA + dual
GbE) with **~93 grounds** — comfortable for the fastest edge-crossing nets, **A1's
dual SATA (3 Gbps) + HDMI TMDS** and dual-2-lane MIPI. Grounds are **per-interposer**
(only one module is ever seated), so those positions flank whichever SoC's high-speed
pairs are present with wide margin. **SO-DIMM-260 also clears it** (~65 grounds — still
~1 GND/3 sig, fine) and is the better pick for a **compact camera-only build** (no A1);
the extra grounds + coarser 0.85 mm pitch are exactly why 288 is primary once A1/SATA
is in scope. The only thing that truly exceeds even 260 is a 1-GND-per-signal scheme
(overkill) or dual-CSI+DVP16 simultaneous (+~36) — a combo no single SoC implements.
**Escape valve:** A1 (video-*out* + SATA/storage) and the T-cameras (video-*in*)
never share an interposer, so their mutually-exclusive peripherals occupy the **same**
connector positions — A1's HDMI/VGA/RGB reuse the T-series camera-zone. No single
interposer needs every peripheral of every SoC at once.

**Assign geography-first, not by GPIO bank order:** place the carrier floorplan
(connector + peripheral connectors), then assign the 260 positions so nets exit
the socket already pointed at their destination — USB fingers by the USB jacks,
MIPI pairs by the FFC, MSC0 by the SD slot, audio by the codec block, GPIO banks by
their headers. Rules:
- each MIPI pair on **adjacent fingers, same face**, GND finger each side;
- all high-speed on **one contact row** (escapes on one layer);
- power pins **clustered** at one end (5V pour is a blob, not a snake).

**MIPI FFC connectors — 2× identical, independently wired (decided).** Part:
**SFW15R-2STE1LF** (Amphenol ICC, 15-pin, 1 mm pitch, ZIF slide-lock,
right-angle SMT, LCSC/JLCPCB **C3167933**). Same part already proven on the
single-SoC T41 board (`old/hw` BOM: `J13`) — carried forward rather than
re-picked. DigiKey confirms 14,946 in stock (verified 2026-07-11,
$0.40–0.66/unit), JLCPCB-assemblable.

15 pins matches the industry-standard 2-lane-MIPI camera FFC pinout (the same
scheme used by RPi-style camera modules): 2 data lanes (`D0P/D0N`, `D1P/D1N`),
1 clock lane (`CLKP/CLKN`), sensor power (3.3 V + 1.8 V), SCCB/I²C (`SDA/SCL`),
a reset/powerdown GPIO, and grounds interleaved for return-path integrity.

**Both carrier FFCs use this same 15-pin footprint, each with its own full,
independent set of 15 connector-edge positions** — not muxed, not sharing
lanes. On any SoC with a genuine second MIPI channel (T32, T33, T40 — dual
2-lane per §10's per-SoC D-PHY audit), both FFCs are live simultaneously with
real, separate D-PHY lanes underneath each, so dual-sensor bring-up is a real
test, not a shared/multiplexed approximation. On single-MIPI SoCs (T41) or
DVP-primary SoCs using their interposer-local DVP connector instead (§10),
the second FFC's socket positions simply go unused — no penalty, since they're
already inside the ~180-signal superset budget (§8) regardless of whether
both are populated.

**Carrier physical I/O — microSD, USB-C, USB-A, DC jack (decided, carried
forward).** All four re-verified against current stock rather than assumed
still good, same rigor as every other part on this list — no replacements
needed, all still active and sourceable:
- **MicroSD: Hirose DM3D-SF** (push-pull ejector, 1.55 mm height, LCSC
  **C719027**). Unchanged from the original board. 1,299 in stock (verified
  2026-07-11), JLCPCB-assemblable, existing custom footprint already built
  (`old/hw/teacup.pretty/`) — reuse it.
- **USB-C ×2: Korean Hroparts TYPE-C-31-M-12** (16-pin single-row, USB 2.0 +
  power only, no SS lanes, right-angle SMD). Unchanged part, now two
  instances: `J2` (alt power input, §9) and `J9` (the BMC's dedicated port,
  §9 — data-only as far as the rest of the carrier is concerned, its VBUS
  never leaves the BMC domain). 116,310 in stock at LCSC (verified
  2026-07-11), extremely common part (also used on e.g. Keebio keyboards) —
  deep, reliable supply.
- **USB-A: TE Connectivity 292303-7** (4-pos, right-angle SMD, USB 2.0 host
  receptacle). Unchanged. 743 in stock at DigiKey (verified 2026-07-11) —
  thinner stock than the others but still active/current, and it's the exact
  part with an existing proven footprint, so not worth switching to a
  cheaper sibling (e.g. 292303-1) just to save cost on a low-volume build.
  **`J3`'s D+/D- share one net pair with `J2`'s** (`USBA_HOST_DP`/
  `USBA_HOST_DM`) — one logical USB host controller on the interposer SoC,
  reachable through either physical connector. This is for peripheral use
  only (a USB WiFi dongle, keyboard, hub, etc.) — `J2`'s data lines carry no
  power semantics of their own; `J2`'s VBUS is a separate, independent net
  (`ALTUSB_VBUS`) feeding the power-OR circuit above, not related to the data
  pair at all. The shared pair crosses the DDR4 connector on `J1` pins 41/42
  (unit 1), the first two of the eight pins previously held as unassigned
  placeholders (`RESERVED_P41`.. `RESERVED_P48`, §8) pending the full
  per-SoC superset pass — chosen adjacent to the pin 36-40 GND run for some
  differential-pair flanking. The remaining six stay reserved.
- **DC jack: Würth Elektronik 694106301002** (WR-DC right-angle THT barrel
  jack, 2.1 mm ID / 5.5 mm OD, 5 A, with an integrated normally-closed
  presence-detect switch). The original BOM listed the family placeholder
  `6941xx301002` without picking a specific pin-diameter variant — resolved
  here to the **06** variant (2.1/5.5 mm), the de facto standard barrel size
  for generic 5 V/12V wall adapters. 33,290 in stock at DigiKey (verified
  2026-07-11). **Wire the NC presence-detect switch to an ESP32 GPIO**, not
  just a generic test point — the BMC is what actually sequences the power
  path (§9: load-switch enable, digipot-then-enable for VCORE/VDDR), so
  knowing whether the barrel jack has a supply seated *before* it drives that
  sequence is directly load-bearing input for the BMC's own logic, not merely
  a passive diagnostic. Same idea as the load switch's power-good line and
  the USB power switch's per-channel FAULT outputs (§9) — another real signal
  the BMC needs for its own decisions, not just something to probe with a
  scope.

**Carrier peripheral blocks (camera-SoC support) — narrowed scope.** §8 breaks
out *every* pin, so everything below is header-reachable regardless of what
gets dedicated hardware. Only **one** thing gets **dedicated carrier
hardware**; everything else that needs a physical connector or driver circuit
is **delegated to whichever interposer needs it** — same principle already
used for clock (§2, must stay local) and the optional camera FFC-on-interposer
(mode A): local to the SoC that actually uses it, not built into the universal
carrier. Full original carrier-hardware plan (audio codec, IR-cut/IR-LED,
RJ45, SATA, HDMI, DVP header, JTAG) kept on file in **§8a** — not used in this
build.

- **Audio — headphone jack only**, matching the original single-SoC board's
  approach (`old/hw` BOM: `J10`, `AudioJack4_Ground`): `HPOUTL` → a 3.5 mm
  jack, direct. **No onboard mic, no speaker amp, no dedicated codec support
  circuit.** `MICPL/MICNL`, `I2S_DAC/ADC_*`, `DMIC` stay plain header pins
  (§8's general breakout) for anyone who wants to wire up their own front end.
- **Ethernet (GMAC) — pin header, not a jack.** Dual RGMII broken out to a
  labeled header, same as the original board — no RJ45 connector, no
  magnetics/PHY support circuit on the carrier.

**Cut from carrier scope entirely** (delegate to the interposer if a target
SoC needs it): **JTAG debug header, IR-cut/IR-LED drivers, a dedicated DVP
camera header, SATA connectors, an HDMI connector.** JTAG (`TCK/TMS/TDI/TDO/
nRST`, standard 2×5) moved here on the same logic as the rest of this list —
it's present on **T40/T31/most parts, NOT on T41 QFN96** (pin-limited), so a
universal carrier header would sit unused on some builds and be pinout-wrong
for others regardless; a JTAG header only gets stuffed on the specific
interposer whose SoC actually has the pins for it. None of these five are
carrier parts anymore — see §8a for the original plan and §10 for the
pin-budget consequence (particularly for A1's SATA/HDMI).

Already covered elsewhere: SFC flash (§5), MSC/SD (above), GMAC/USB (§8/§9),
I²C-SMB (§2 digipot + SCCB), SAR-ADC + eFuse/OTP program pad (§4). SSI/SPI master
(SSI0/1) stays header-only — app-specific.

**Pin-breakout header sheet built (`hw/sheets/headers.kicad_sch`, generated by
`hw/scripts/build_headers.py`).** J1 pins 87–96 (previously `RESERVED_P87`..
`P96`) and 97–169 (previously unconnected) now carry the GPIO/peripheral
superset, function-clustered per-header onto labeled 0.1" pin headers as
decided above — clustering is a silkscreen/likely-use convenience only, not
an electrical constraint, so a user can still wire any header pin however
they want; high-speed-capable signals broken out this way can be
length/impedance-matched at layout time regardless of which cluster they
landed in. 11 headers, 71 signals total: **GMAC0/GMAC1** (RGMII, 10 sig each
— GMAC1 only populated because A1 genuinely has a second MAC, confirmed
against Ingenic's own A1 GPIO allocation table, not assumed), **UART0/UART2/
UART3** (4 sig each — **UART4/UART5 do not exist on any T-series/A1 SoC in
this family**, checked against every HDK GPIO table on file; only the older
JZ47xx application-processor line has them, so despite an earlier "UART2-5"
working name, no UART4/UART5 pins were invented), **SSI0** (6 sig, SPI
master, alt UART0/UART2/SMB1 on some SoCs), **SSI1** (4 sig, alt PWM0-3/
SMB1/DMIC), **PWM0-7** (8 sig), **SAR-ADC** (1 sig, `SAR_AUX0` — single
dedicated analog pin, matches the T41 reference board's `ADC_AUX0`, not a
multi-channel SADC), **SMB0/SMB1** (4 sig, general I²C, kept electrically
isolated from the `I2C_ID_SDA/SCL` carrier-ID EEPROM bus, §7), and 16 plain
unclaimed `GPIO0`-`GPIO15` pins for whatever's left. Verified: 0 layout
overlaps (`check_overlaps.py`), full netlist diff confirms only J1
pins 87–169 and the 11 new header refs changed (nothing on power/BMC/IO/
connector-units-1-2 shifted), ERC error count went *down* (231→158) purely
from previously-NC pins now being driven, and the ERC warning increase is
entirely the same pre-existing "unspecified pin type" class already
tolerated elsewhere on this board (generic connector pins), at the same
proportion as before.

**All remaining J1 pins also broken out (decided, supersedes the "ground is
fill" default above for this connector).** Explicit user direction: every
still-unused J1 pin — the pins-170-192 tail of unit 4 plus all of units 5-6
(193-288), 119 pins total, previously left unconnected — now carries a raw
`SPARE_P<n>` global label (`<n>` = the literal J1 pin number) straight to 5
new spare-breakout headers (`J31`-`J35`, `hw/sheets/headers.kicad_sch`),
grouped by connector unit for traceability rather than any assumed function,
since these are genuinely undefined-purpose pins reserved for whatever a
future interposer or bring-up need turns out to want. Each spare header's
GND reference pin ties to the board's common GND net rather than consuming
a J1 position, so this costs nothing against the SS8 pin/ground budget.
Note this repurposes the pins the "ground is fill" rule (§8, top) would
otherwise have wanted — a deliberate tradeoff of some signal-integrity
headroom for maximum future flexibility on a bring-up/bench board. Verified
the same way as the header sheet above: 0 overlaps, netlist diff shows only
the 119 new J1 net assignments + 5 new header refs added (nothing else
moved), ERC total violation count unchanged (426 before and after — the 118
`pin_not_connected` violations these pins used to carry became the board's
existing `pin_to_pin` "unspecified pin type" warning class instead, no new
categories). Also fixed in this pass: `W25Q32JVSS`/`DIP8_NOR_SOCKET` (added
in the prior BMC PR) carried KiCad-10-only symbol-property fields that made
the schematic fail to load entirely in the KiCad 9.0.8 actually installed
here — stripped in `teacup-carrier.kicad_sym`, confirmed electrically
identical via netlist diff (only UUIDs changed).

### 8a. Carrier peripheral blocks — original dedicated-hardware plan (reference only, not used in this build)

Kept on file in case a future carrier re-spin wants these built in rather than
delegated per-interposer.

- **Audio codec support.** T-series integrate an audio CODEC (T41 QFN96:
  differential mic in `MICPL/MICNL` + `HPOUTL` out + `VCM` ref; other parts
  stereo). Planned carrier hardware: onboard **electret mic → MICPL/MICNL**,
  **HPOUTL → 3.5 mm jack** + a small class-D amp (**PAM8302**-class) for a
  speaker, and **I2S**/**DMIC** broken out to headers for external audio.
  Powered from `CODEC_AVDD` 1.8 V (§3). Mic in is sensitive analog — would
  need its socket-crossing trace kept away from switchers.
- **PWM / IR-cut / IR-LED** (8 PWM channels, PWM0–7). Planned: a PWM-driven
  IR-cut H-bridge (bidirectional solenoid) on a 2-pin connector, a PWM IR-LED
  driver (MOSFET/constant-current) header, spare PWM to a fan/motor header +
  test LEDs.
- **RJ45 jacks.** Dual RGMII GMAC terminated in physical RJ45 connectors
  (with magnetics) on the carrier, rather than a bare pin header.
- **SATA connectors.** A1's SATA0/1 terminated in physical SATA connectors on
  the carrier (2×), crossing the socket to reach them.
- **HDMI connector.** A1's display-out terminated in a physical HDMI
  connector on the carrier, crossing the socket to reach it.
- **DVP header.** A dedicated carrier header for DVP-primary SoCs
  (T10/T20/T21/T23/T30/T31), alongside the MIPI FFC(s), so DVP data crossed
  the connector to a carrier connector rather than staying local to the
  interposer.
- **JTAG debug header on the carrier.** `TCK/TMS/TDI/TDO/nRST` to a standard
  2×5, universal across every interposer. Moved to interposer-only (§8)
  since JTAG isn't present on every SoC in the same place — T40/T31/most
  parts have it, T41 QFN96 doesn't (pin-limited) — so a one-size carrier
  header would be wrong or unused depending on which module is seated.

---

## 9. Management controller (ESP32-S3 BMC) — autonomous / LLM-driven dev

The carrier carries an **ESP32-S3** as an on-board **baseboard management
controller** so an agent (an LLM, CI, or a human) can drive the target **wired
*or* wireless**, hands-off. It's powered independently of the SoC (stays alive to
reset/recover it) and lives on the **carrier** (universal — manages whatever
interposer is plugged in).

**Why ESP32-S3:** native **USB-OTG + USB-Serial-JTAG** (wired console/control to a
host) **and WiFi + BLE** (wireless), dual-core, ample GPIO. ESP32-C3 is the budget
cut (USB-Serial-JTAG + WiFi, fewer pins).

**Part — module, not bare chip: `ESP32-S3-WROOM-1-N16R2`** (LCSC **C2913205**,
**JLCPCB-assemblable**). Re-verified 2026-07-11: 6,361 in stock at LCSC,
$3.42–4.73/unit depending on quantity break (1,300+ hits the low end) — still
healthy, no discontinuation signal, pick stands. Pre-certified: integrates
antenna / RF match / 40 MHz crystal / **16 MB flash / 2 MB PSRAM** — no RF
layout or cert.

**Quad PSRAM (R2), not octal (R8), on purpose:** octal PSRAM consumes GPIO33–37,
and the BMC is GPIO-hungry. Quad PSRAM shares the flash bus and frees those pins.
(A no-PSRAM variant would *not* free anything further — GPIO35-37's pin cost is
specifically an octal-PSRAM/octal-flash thing; quad PSRAM and no PSRAM are
pin-equivalent, confirmed against Espressif's own pin documentation — so R2 is
already the optimum, dropping PSRAM entirely would only cost the buffer space an
ESP-Hosted link wants, for zero pin gain.) 2 MB PSRAM is plenty — stream flash
images in chunks, no need to buffer a whole 16 MB NOR. Route native-USB
**GPIO19 (D−) / GPIO20 (D+)** to the BMC USB-C.

**GPIO budget — fully allocated, by design, via an I²C expander.** All 36
GPIO-capable pins on the module are in use; there is no spare headroom left on
native silicon. Two functions (four pins) are deliberately kept native rather
than moved off-chip, because margin/timing testing depends on driving them
directly rather than through an I²C-mediated expander: **flash chip-select**
(`EN_CS_U4`/`EN_CS_U5`) and **power-domain switching** (`SW5V_EN_BMC`/`SW5V_EN_ALT`).
**USB overcurrent** (`USB_OC1-3`) is also kept native, for fast hardware fault
response rather than polled status. Everything else that's a slow status/enable
signal — `USB_EN1-3`, `PG_SW5V`/`PG_VCORE`/`PG_SW5V_ALT`, `SW_SENSE_1`/`SW_SENSE_4`,
`DCJACK_PRESENT` (9 signals) — moved to **`U15`, a TCA9555PWR** (TI, TSSOP-24,
16-bit I²C/SMBus expander, LCSC **C465732**, 4,690 in stock, $0.817 @ 1+/$0.3736
@ 1,000+, verified 2026-07-12). It shares the **`I2C_PWR`** bus (not `I2C_ID`) —
putting it on the interposer-crossing bus would reintroduce the exact
digipot/carrier-ID-EEPROM fault-coupling this doc already rules out above.
Address pins grounded → `0x20`, which doesn't collide with the digipot's
`0101`-prefixed (`0x28`-range) address regardless of the digipot's own strapping
— confirmed, the two parts' address families can't overlap. `U15`'s own `~INT`
pin (open-drain, active low) is wired to a spare ESP32 GPIO for interrupt-driven
updates rather than pure polling. Net result: 9 pins freed, 6 spent on the
ESP-Hosted link below, **2 pins left genuinely spare.**

**ESP-Hosted: the BMC's WiFi/BLE, exposed to the interposer SoC over SPI, not
SDIO.** [Espressif's ESP-Hosted](https://github.com/espressif/esp_hosted)
framework lets the SoC treat the ESP32-S3 as a wireless co-processor — the SoC
sends RPC calls (associate, open a BLE connection, etc.) over a transport link,
the ESP32-S3 runs the actual 802.11/BLE stack and radio locally and relays
data back; on a Linux host this shows up as a normal network interface via a
kernel driver. **ESP32-S3 has no SDIO slave peripheral at all** (confirmed
against Espressif's own docs: its SD/MMC controller is host-only, unlike
classic ESP32, C6, C5, and C61, which do support SDIO slave) — this was checked
specifically because `MSC1` (a spare SD/MMC controller on some T-series SoCs)
looked like the obvious channel and isn't usable for it regardless of which
MSC number is picked. The transport is **full-duplex SPI** instead: `HOSTED_SPI_CLK`/
`_MOSI`/`_MISO`/`_CS`, plus `HOSTED_HANDSHAKE` and `HOSTED_DATA_READY` (both
co-processor→host, flow-control/data-pending signals), crossing `J1` on pins
43-48 — the last of unit 1's reserved pins. The 7th ESP-Hosted signal, reset,
needs no dedicated GPIO: per Espressif's own reference wiring it ties straight
to the co-processor's own EN/RST pin rather than a GPIO, so `U8`'s `EN` pin
(previously carrier-local, pulled up by `R8`) is now also `HOSTED_RESET`,
crossing `J1` on pin 86 — the SoC-side driver must be configured open-drain so
it only ever pulls low, never fighting `R8`'s pull-up. BLE only on S3 (5.0+,
no classic BT), matching the radio the chip actually has.

**`D1`/`D2`: keeping the BMC alive on ALT-only power.** `+5V_BMC`'s isolation
(above) cuts both ways — it also means the ESP32 has *no* power at all if `J9`
is unplugged and only `+5V_ALT` is present, which breaks the BMC's own
functions (digipot control, ESP-Hosted, telemetry) in exactly the scenario
`SW2`'s force-ALT override exists for. Fixed with a diode-OR scoped narrowly to
the BMC's own regulator, not the whole `+5V_BMC` net: `D1` (anode `+5V_BMC`)
and `D2` (anode `+5V_ALT`) both feed a new node, `U5_VIN`, which only `U5`
(and its input cap `C14`) sit on — `U4` (the BMC-branch load switch feeding
`+5V_SW`) still sources strictly from the real, undiluted `+5V_BMC`, so its
behavior stays unambiguous and this doesn't create a second, redundant path to
`+5V_SW` (`U14`/`+5V_ALT` is already the correct direct one). **Part: PMEG2010ER**
(Nexperia, 1 A Schottky, 340 mV Vf @ 1 A, SOD-123W, LCSC **C82288**, 8,625 in
stock, $0.28 @ 5+/$0.156 @ 6,000+, verified 2026-07-12) — low enough drop to
stay inside the AZ1117-3.3's dropout at the WROOM-1's modest current draw;
worth reconfirming against real load current at bring-up. This closes the
loop with the isolation goal from earlier: the *only* remaining path for a
`J9` session to deliver bulk power to the rest of the board is `U4`, which
requires firmware to explicitly drive `SW5V_EN_BMC` high — confirmed via
netlist, nothing else touches that net. (A sub-mA pull-up bias from `R8`
reaches the interposer automatically via `HOSTED_RESET` whenever `+5V_BMC` is
present, but that's a logic-level bias on a shared control line, the same
category as `BOOTSEL` or any other cross-connector control signal — not power
delivery in the sense either isolation goal is about.)
Variants: `-1U` (C3013945, U.FL antenna for metal enclosures/range); `-N8R2` (8 MB
flash) to shave cost; **ESP32-S3-MINI-1** if space-tight.

**BMC power domain — electrically isolated by construction, not just by
switch logic. Implemented in the schematic** (`hw/sheets/power.kicad_sch`,
`bmc.kicad_sch`, `io.kicad_sch`). The BMC's USB-C above is a **dedicated
connector (`J9`)**, physically separate from the carrier's main power-input
USB-C (`J2`) — so a cable plugged in purely to reach the ESP32 (flashing,
console, JTAG) cannot deliver power to anything else on the board; there is
no shared VBUS conductor to design around in the first place. Three named
5 V domains:
- **`+5V_BMC`** — VBUS from `J9` (the BMC's own dedicated USB-C). Feeds the
  always-on 3.3 V LDO (`U5`, via the `D1`/`D2` diode-OR below) and `U4`'s
  input (the BMC-branch load switch, below) — nothing else. A device plugged
  into `J9` has no electrical path to push power out to anything on `+5V_ALT`
  or `+5V_SW`; the only way `+5V_BMC` reaches `+5V_SW` is `U4` turning on,
  which requires firmware to explicitly drive `SW5V_EN_BMC` high (see
  `D1`/`D2` below for the corresponding gap this left on the *receiving* side
  — the BMC had no power at all on ALT-only input until that fix).
- **`+5V_ALT`** — `J2` (the carrier's main power-input USB-C) plus `J5` (the
  DC barrel jack), OR'd together by `Q1`/`Q2` with **priority given to the DC
  jack**: `Q1` self-enables off `DCJACK_VBUS` (gate pulled to ground through
  `R15`, so it conducts whenever the jack has voltage, independent of the
  other source); `Q2` is gated OFF whenever the DC jack is present (its gate
  is biased toward `DCJACK_VBUS` through the `R16`/`R17` divider, collapsing
  its own Vgs to within a few hundred mV of zero regardless of `ALTUSB_VBUS`'s
  own state). The jack wins deterministically whenever both are connected,
  entirely in hardware — no firmware required for correct behavior. Known
  simplification: this is a resistor-biased priority select, not a true
  ideal-diode controller, so `Q2`'s "off" margin against its ~-0.9 V Vgs(th)
  is workable but not enormous across process/temperature — acceptable for
  this board's scope; a dedicated ideal-diode IC (e.g. LM74610-class) would
  tighten it at the cost of one more BOM line, deliberately not added. The
  barrel jack's built-in mechanical presence-detect contact
  (`DCJACK_PRESENT`, pulled up by `R14`) is separately wired to ESP32 GPIO45
  purely for firmware telemetry; it has no bearing on the OR-ing itself.
- **`+5V_SW`** — the rail every downstream buck (and the interposer, through
  the connector) actually runs from. Fed by a 2:1 select between `+5V_BMC`
  and `+5V_ALT` through **two TPS22990DMLR load switches** (`U4` on the BMC
  branch, `U14` on the ALT branch — reusing the same part already justified
  below rather than adding a second SKU). Each `ON` pin is arbitrated between
  its own ESP32 GPIO (through a 1 kΩ series resistor: GPIO38→`U4`, GPIO16→
  `U14`) and a 100 kΩ pulldown that defaults it off when the GPIO is
  undriven (reset/Hi-Z). A dedicated 3-position switch, `SW2` (separate
  physical instance from the NOR CS-select switch `SW1`, §5, same part
  number for BOM commonality), can override either branch on directly — a
  genuine **ON-OFF-ON**, same structural pattern as `SW1` (pole = a fixed
  rail, the two throws are the signals it connects to when engaged, not the
  reverse): the pole (pin 3) is tied to `+5V_ALT` itself — through `JP1`, a
  provisioning jumper open as shipped, see §10's digipot-safety entry — throw
  1 connects it to `EN_SW_BMC`, throw 4 connects it to `EN_SW_ALT`. **Force BMC**
  (throw 1, forces the BMC branch on), **off / ESP32 control** (center,
  neither throw engaged — both branches default off via their pulldowns,
  same safe idle state as before, and GPIOs retain full control from here),
  **force ALT** (throw 4, forces the ALT branch on). Sourcing the pole from
  `+5V_ALT` rather than `+3V3_ALWAYS` is deliberate: it's what makes the
  force-ALT throw work with `J9` fully unplugged and the BMC branch
  unpowered, which is the scenario this override exists for in the first
  place. Trade-off, and it's a small one: the force-BMC throw is a no-op
  unless an alt source is *also* present to supply the pole — acceptable,
  since forcing BMC power onto `+5V_SW` is only ever wanted with firmware
  already running (you'd be talking to the ESP32 to know to do it), not the
  hardware-only scenario the ALT throw covers. In ESP32-auto mode (switch
  centered), firmware gets the same effective three states via a one-hot
  2-bit GPIO select — the two GPIOs must never both be driven high at once,
  since neither load switch is an ideal-diode part on its output side and
  `+5V_BMC`/`+5V_ALT` would end up fighting on the shared `+5V_SW` node.

**MOSFETs (`Q1`/`Q2`): AO3401A**, 30 V/4 A P-channel, SOT-23, Vgs(th) ≈
-0.9 V — plenty of margin driving off a 5 V rail at this current level.
1,831,820+ listed at LCSC (AOS-branded, **C15127**) but that listing's own
stock-status text read inconsistently when checked; the same part number
from a second manufacturer, **UMW/Youtai Semiconductor, LCSC C347476**, gave
a clean read — 539,740 in stock, ships now, $0.0365 @ 20+ qty (verified
2026-07-12) — cite that listing.

**Control plane** (agent-facing API over USB-CDC *and/or* WiFi REST/MQTT/telnet):

| Function | Mechanism | Silicon |
|---|---|---|
| **Reset** | power-cycle the **switched SoC 5 V domain** (drops *every* SoC rail — mode-A local bucks and mode-B carrier VCORE/VDDR/3.3/1.8 — for a true POR; BMC is on the always-on domain, so it survives). **Universal**: T41 QFN96 is **POR-only** (System-Control table = just POR_CTL @ pin 60, no PPRST_ → no reset pin). Optional **PPRST_** GPIO on parts that *have* one (T31 QFN88, all BGA) for a warm reset | **load-switch IC — TPS22990DMLR** (in use; see note below) on the SoC-5V domain; PPRST_ = GPIO where present |
| **BOOTSEL** (SFC / SD / USB boot) | drive the strap at POR | ESP32 GPIO + 1 K series R |
| **Flash sharing** (SoC ↔ ESP32) | SoC powered + **BOOTSEL-diverted → SFC is high-Z** ("Hi-Z-rst"); ESP32 owns the shared SPI bus, each master tristates when idle | **just GPIO** (CS + BOOTSEL); a ~6-ch **bus switch is optional** — only to program a fully-*off* SoC |
| **Flash select** (DIP8 ↔ SOP8) | pick the active CS | ESP32 GPIO, sense-fed by a 3-position manual switch (§5) |
| **Carrier power source** (BMC-USB ↔ ALT-OR'd supply ↔ off) | GPIO pair (one-hot 2-bit) or 3-position manual override, whichever is engaged | 2× **TPS22990DMLR** + priority P-FET OR (above) |
| **Console** | UART1 ↔ WiFi and/or USB-CDC | ESP32 UART |
| **WiFi/BLE for the SoC** | ESP-Hosted RPC over full-duplex SPI, SoC as host | full-duplex SPI (6 signals + `EN`-tied reset), see above |
| **I/O expansion** (USB EN/PG/switch-sense/DC-jack-sense) | I²C-mediated, off the digipot's own bus | **TCA9555PWR** (16-bit expander, above) |
| USB VBUS (if SoC host mode) | current-limited switch | USB power switch — **TPS2053BDR** (in use; see note below) |

Added switching silicon: **one load switch + a couple of GPIOs** (bus switch only
for the fully-off-SoC flash case) — all 3.3 V logic, driven straight off the ESP32.
No relays/SSRs (wrong tool for on-board DC/logic).

**Load switch part: TPS22990DMLR** (Texas Instruments, WSON-10-EP 2×3, LCSC
**C962990**). **0.6–5.5 V input, 10 A, 3.9 mΩ RON**, adjustable rise time,
integrated power-good output, optional controlled discharge. Datasheet
confirmed direct from TI; well-stocked at LCSC (835 units, verified 2026-07-11,
JLCPCB-assemblable) — DigiKey was out of stock on this SKU at the same check,
so LCSC is the primary source here.

Replaces the earlier **TPS22918-class** placeholder used above: TPS22918 itself
is only rated **2 A continuous** — undersized against the **≥3 A** switched-5V-
domain spec (§4, "+5 V in" row), since this rail feeds *every* downstream SoC
supply (mode-A local bucks and mode-B VCORE/VDDR/3.3/1.8 all at once) behind one
switch. TPS22990's 10 A rating clears that with a wide margin, and its 3.9 mΩ
RON keeps the switch's own IR drop negligible (≈12 mV at 3 A) — important since
every downstream buck's own input-margin budget (§4) starts from whatever
reaches it *after* this switch. The integrated power-good output is a bonus:
it's a free, already-broken-out signal for the BMC to confirm the switched rail
actually came up, fitting §6's carrier-instrumentation philosophy without
adding a part.

(TI's family has other members worth naming for context, not evaluated further
since TPS22990 already clears every requirement: **TPS22919** — 1.5 A, too small,
same problem as TPS22918; **TPS22920** — 4 A but only **0.75–3.6 V input**, which
disqualifies it outright for a 5 V rail regardless of current rating.)

**USB power switch part: TPS2053BDR** (Texas Instruments, SOIC-16, 2.7–5.5 V
input, **3 channels, 500 mA/channel** rated load, **1 A typical current-limit**
trip, 70 mΩ, per-channel deglitched overcurrent FAULT output). Datasheet
confirmed direct from TI; DigiKey has 3,719 in stock (verified 2026-07-11,
9-week lead time noted) — no LCSC listing turned up for this exact part, so
DigiKey is the source for now.

**Why 3 channels, replacing the "TPS2051-class" placeholder:** A1 is the
worst case at **3× USB OTG** (§10) — any of which could be in host mode and
need switched, current-limited VBUS. One TPS2053B covers all three A1 ports
from a single IC; T-series interposers with fewer USB ports simply leave the
extra channel(s) unstuffed/unconnected — same part number across the platform,
no per-SoC BOM variant needed. The 500 mA/channel rating matches standard
USB2.0 port-power spec (not a high-power charging port); the per-channel FAULT
output is a real win for the BMC — a spare-pin-cheap way to let the agent see
"downstream device overcurrent/short" per port, in the same instrumentation
spirit as §6 and the load switch's power-good line above. If a future revision
wants higher-than-spec port current (e.g. powering a USB hub or spinning
drive), a single-channel higher-current part (TPS2065-class, 1 A) could
replace one channel's worth on that specific port without touching this
decision for the rest.

**Beyond switching, the BMC sets the rail voltages** via the **MCP4661 digipot**
(§2): read the carrier ID (§7) → set VCORE/VDDR for that SoC → enable the rails
(voltage *before* enable = safe) → optionally **sweep VCORE for margining**. Ties
adjustable power (§2), ID (§7), and the BMC into one digital flow.

**Autonomous flash loop — no DFU, no host tools:**
1. ESP32 sets **BOOTSEL → USB** and power-cycles → bootrom diverts to USB boot and
   **leaves SFC high-Z** (never drives the flash bus).
2. SoC powered + SFC high-Z → no contention, no ESD back-power → **ESP32 owns the
   shared SPI bus** and programs the NOR (flashrom-style; SOP8 or DIP8), driving CS.
3. ESP32 sets **BOOTSEL → SFC**, tristates its SPI, power-cycles → SoC boots the
   new image.
4. ESP32 streams UART1 back over WiFi/USB → agent reads the result.

Only a fully-*off* SoC (e.g. a bricked part that won't reach USB-boot) needs the
optional bus switch to isolate its SFC; the normal loop is just CS + BOOTSEL.

**Two flashing paths — the ESP32 triggers both:**
- **ESP32 direct SPI** (the loop above) — ESP32 writes the NOR itself, **hostless**,
  agent-over-WiFi. Best for **SPI-NOR** + recovery. It's a raw writer, so NAND is
  dump-only (no ECC / bad-block handling).
- **SoC DFU** (bootrom USB boot / `thingino-dfu`) — ESP32 sets BOOTSEL→USB and
  resets to *enter* DFU; the SoC's own SFC controller then writes via USB from a
  host, handling **NOR *and* NAND** properly (ECC, bad-block, partitions).

Rule of thumb: **NOR → either; NAND → DFU.** Same control API drives both —
`flash_nor_direct(img)` (path 1) vs `enter_dfu()` + host (path 2).

So an agent runs **`flash(image)` → `reset()` → `read_console()`** entirely over
the network — this is what makes "an LLM drives this board" real (same pattern as
the opi-closet relay lab, collapsed onto the carrier).

**Flash arrangement:** the interposer's SOP8 NOR is the module's default boot
(CS0); an optional **DIP8 socket on the carrier** (swappable, on the shared SFC bus
across the connector, CS-selected) holds alternate / recovery images. The ESP32
programs either. Arbitration rule as always: SoC-owns *or* ESP32-owns, never both.

**DIP8 socket part: ZHOURI IC-8P** (2.54 mm pitch, 7.62 mm row spacing,
through-hole, LCSC **C5289485**). 2,780 in stock (verified 2026-07-11,
~$0.02–0.03/unit). Stamped (not machined-pin) contacts — fine for this role:
the socket exists for occasional manual swap-in of a backup/recovery chip, not
a high-cycle production test fixture, so the cheaper stamped-contact
construction is proportionate. If repeated-swap durability ever becomes a
real concern on a given build, a machined/turned-pin DIP-8 socket is a
drop-in upgrade at the same footprint — no other part depends on which
contact type is stuffed here.

**Dual-NOR CS select — ESP32-driven, reusing the Teacup circuit (decided).**
The original single-SoC board's dual-flash CS circuit (`old/hw` schematic:
`U4`/`U5` = the two NOR chips sharing one `CK`/`DR`/`DT` bus; the SoC's single
`SFC_CE0` output is the common pole of a mechanical SPDT switch, `SW2`, whose
two throws route it to `U4.CE` (net `/NOR_CE2`) or `U5.CE` (net `/NOR_CE1`);
whichever flash isn't selected is held deselected by its own 100 kΩ pull-up,
`R12` or `R24`) is carried forward as-is for the SoC side — verified directly
against the netlist, not just the schematic picture. **What's added: the ESP32
can now also select, without becoming a second driver on the SoC's CE0 net.**

The key finding that shaped this: `SW2` was never a second driver — it only
*routes* the SoC's one CE0 output to one of two destinations. Wiring the
ESP32 to drive CE0 directly in parallel with the SoC would reintroduce the
exact bus-contention risk flagged in §9's "Flash sharing" arbitration rule
(two push-pull drivers on one net), unless the SoC's SFC controller is
guaranteed high-Z on that specific pin whenever it's not master — not
something to depend on without per-SoC datasheet confirmation. So the design
keeps the "one driver, routed" topology and makes the *router* electronic
instead of mechanical:

- **2× TS5A3166** (TI, SPST analog switch, single control pin, SOT23-5, LCSC
  **C353035**, 17,285 in stock verified 2026-07-11, ~$0.14–0.36/unit, 0.9 Ω
  Ron). One switch gates `SFC_CE0` → `U4.CE`, the other gates `SFC_CE0` →
  `U5.CE`, each independently enabled by its own ESP32 GPIO. "Neither
  selected" = both GPIOs low, both switches open, both flash CEs sit at their
  existing pull-up (deselected) — the third state the original mechanical
  switch never had. Two independent SPST gates were picked over hunting for a
  single mux-with-enable chip: no encode/decode timing to get wrong, and even
  a firmware mistake that enables both gates at once just fans CE0 out to
  both flashes (a logical no-op / phantom-select bug) rather than an
  electrical contention risk — same failure-mode-tolerant reasoning used
  elsewhere in this doc.
- **Manual control: Alps Alpine SSSS711403** (SSSS7 series, 1-pole/3-position
  slide switch, right-angle SMD, LCSC **C160877**, 1,691 in stock verified
  2026-07-11, ~$0.45–0.83/unit). Revised from an earlier plan to reuse 2×
  on-hand `JS102011SAQN` switches (C&K, same footprint as the original
  board's `SW2`) after direct confirmation that the physical `JS102011SAQN`
  parts on hand have **no real detent at center** — the slider just passes
  through an undetented middle point, which isn't reliable for a bench tool
  that gets bumped/handled; checking C&K's own JS-series datasheet
  independently confirmed that family only offers SPDT(2-pos)/DPDT/DP3T, no
  genuine 3-position variant, so the footprint match wasn't available for
  this role regardless.

  **Confirmed pinout against Alps' own circuit diagram**
  (tech.alpsalpine.com): 4 electrical terminals, numbered **1/2/3/4**. **Pin 3
  is common**; the wiper slides to connect it to **pin 1, pin 2, or pin 4**
  depending on position — three distinct "on" connections, **not** a
  center-off switch (no true open/electrical-off state of its own). Verified
  against the actual footprint (`teacup-carrier.pretty/SW-TH_SSSS711403.kicad_mod`):
  4 SMD pads (1–4) match the diagram's numbering left-to-right, plus 2
  through-hole pads that are purely mechanical anchor legs, not electrical.

  **Wiring — the "neither" state is created by how we wire it, not by the
  switch itself:** pin **3 (common) → GND**, **pin 1 → one ESP32 GPIO input**
  (select U4), **pin 4 → the other** (select U5), and **pin 2 left
  unconnected** — a deliberate dead throw. In the middle position the switch
  connects GND to pin 2, which goes nowhere, so both GPIOs simply stay
  unasserted (pulled high) exactly as if nothing were selected. The ESP32
  reads the two sense GPIOs and drives the two TS5A3166 enables accordingly:
  pin 1 engaged → enable the U4 gate; pin 4 engaged → enable the U5 gate;
  middle position (pin 2, dead) → both gates stay open.
- **Net effect:** the mechanical switch is now purely advisory input to the
  ESP32, not an electrical path to the flash bus at all. The ESP32 is always
  the sole active driver of the actual CE-routing hardware — manual and
  autonomous control share one arbitration point instead of two independent
  electrical paths that could ever disagree.

**Management lines across the connector:** BOOTSEL, reset/power-EN, the SFC flash
bus (CS/CLK/IO0-3), and UART1 run from the carrier BMC to the interposer — a
handful of the 260 positions, already part of the SoC signal set (§8).

---

## 10. Open / deferred / decided

**Open:** none outstanding — the digipot first-power-up gap below is resolved.

**Deferred (decide later):** none outstanding.

**Decided:**
- **Digipot first-power-up safety gap — resolved with a mandatory bring-up
  step plus a hardware gate, not a hope.** §2's safe-sequencing rule (BMC
  sets the digipot, *then* enables the rail) depends on the BMC having run
  at least once to program a safe VCORE/VDDR value into non-volatile
  memory — and `SW2`'s force-ALT override (§9) can bring `+5V_SW` up with
  the ESP32 completely unpowered, since `U1`'s `EN` is pulled straight to
  `+5V_SW` with no BMC gate on the rail itself. Checked whether the
  digipot's factory-default wiper (confirmed from Microchip's own
  datasheet, DS22107A Table 4-2: mid-scale, `0x80` of 256, for the exact
  `-104`/100 kΩ code used here) happens to be safe — it doesn't: on
  `AP62600SJ-7`'s confirmed 0.6 V feedback reference, mid-scale computes to
  **VCORE ≈ 1.2 V**, 9-50% over every T-series target (0.8-1.1 V) depending
  on the part. Ruled out as a fix; it's the failure mode itself. A pure
  hardware gate on "has the digipot actually been programmed" isn't
  possible either — checking requires I²C, which requires the ESP32
  running, which is circular (defeats the point of a firmware-independent
  override). Resolution: **`JP1`, a 2-pin header on `SW2`'s pole**
  (`+5V_ALT` → `JP1` → `SW2_POLE`, gating *both* throws since they share
  the pole) **— open as shipped, so `SW2` is entirely inert until a
  technician bridges it.** Before `JP1` is bridged, `SW2` simply does
  nothing — the board can only be brought up through `J9`, where the BMC is
  guaranteed to be in the loop. This is a one-time manufacturing/bring-up
  step, not a per-use requirement: `JP1`, once bridged, stays bridged for
  the life of the board.

  **Mandatory bring-up checklist (once per board, before `JP1` is ever bridged):**
  - [ ] Leave `JP1` unbridged/unpopulated — this is the as-shipped state;
        don't populate it during assembly.
  - [ ] Power the board via `J9` only (BMC's dedicated USB-C). Do **not**
        connect `+5V_ALT` (`J2`/`J5`) or use `SW2` yet.
  - [ ] Confirm the ESP32 has booted — console over USB-CDC or WiFi reachable.
  - [ ] Have firmware write the correct VCORE/VDDR wiper values for the
        specific interposer/SoC that will ship on this board into the
        digipot's (`U3`) non-volatile memory (not just the volatile
        register — must be the NV write so it survives power cycles).
  - [ ] Read the digipot back over I²C and confirm the NV wiper values match
        what was just written, not the factory mid-scale default (`0x80`).
  - [ ] Power down, then power back up via `J9` alone again, and confirm the
        digipot still reads the programmed (not factory-default) value —
        proves the NV write actually persisted, not just the volatile copy.
  - [ ] Only now, bridge `JP1` (solder a shorting link or install a shunt).
  - [ ] Power-cycle once more and confirm `SW2`'s force-ALT/force-BMC throws
        behave as expected before the board is considered done.

  Skipping straight to bridging `JP1` on an unprogrammed board reintroduces
  the exact overvoltage failure mode this whole mechanism exists to prevent
  — see the calculation above.
- **BMC gets its own dedicated USB-C (`J9`), isolated from the carrier's main
  power input (was an unflagged gap — the BMC's native USB had been sharing
  the main power-input connector, `J2`, so any USB-only debug session would
  also backfeed 5 V toward the rest of the board through the shared VBUS
  pins). Implemented in the schematic.** Split into three named 5 V domains
  (`+5V_BMC`, `+5V_ALT`, `+5V_SW`) with a priority DC-jack-over-USB-C
  hardware OR (`Q1`/`Q2`, no firmware needed) and a 2:1 GPIO/manual-switch
  select (`U4`/`U14`/`SW2`) feeding the switched rail — see §9.
- **`SW2` corrected to a genuine ON-OFF-ON** (was a real bug, not just a
  style nit: the original wiring had the switch's pole carrying the signal
  with one throw tied to GND, which was electrically indistinguishable from
  center's own pulldown-default-low state whenever GPIO wasn't actively
  fighting it — effectively on-off-off). Now pole = `+5V_ALT` (fixed rail),
  throw 1 = `EN_SW_BMC`, throw 4 = `EN_SW_ALT` — see §9.
- **GPIO expander added (`U15`, TCA9555PWR) and 9 slow status/enable
  signals moved onto it**, freeing native ESP32 GPIOs for an ESP-Hosted SPI
  link — while deliberately keeping flash chip-select and power-domain
  switching native, for margin/timing testing. See §9.
- **ESP-Hosted full-duplex SPI link added**, exposing the BMC's WiFi/BLE to
  the interposer SoC as a co-processor (RPC over SPI, SoC as host) — crosses
  `J1` on the last of unit 1's reserved pins (43-48) plus pin 86 for the
  EN-tied reset. Confirmed ESP32-S3 has no SDIO slave peripheral (checked
  specifically because `MSC1` looked like the obvious channel and isn't
  usable for it), so SPI is the only viable transport on this part. See §9.
- **`D1`/`D2` diode-OR added** so the BMC stays powered on ALT-only input
  (was a real gap the `J9`/`+5V_BMC` isolation left behind: unplugging `J9`
  left the ESP32 fully dead even with `+5V_ALT` present, breaking `SW2`'s
  own force-ALT override's assumption that *something* on the BMC side might
  need power too). Scoped to `U5`'s own input only, not the shared
  `+5V_BMC` net `U4` depends on — see §9.
- **`J2` (alt power USB-C) and `J3` (USB-A) share one host data pair to the
  interposer** (`USBA_HOST_DP`/`USBA_HOST_DM`, crossing `J1` on the two
  previously-reserved pins 41/42) — one logical USB host controller, two
  physical connectors, for peripheral use (WiFi dongle, keyboard, hub);
  `J2`'s VBUS stays on its own separate net and plays no part in this. Was
  ambiguous until confirmed: `J3`'s data-line labels had been present on the
  schematic since the earlier I/O rebuild but never actually routed across
  the connector — a loose end now closed.
- **Carrier NOR confirmed dual, matching the reference single-board Teacup's
  U4 (soldered SOIC-8) / U5 (DIP-8 socket) precedent exactly** — the CS-select
  silicon (§9's TS5A3166 switches + manual override switch) was already
  designed for two chips, but the soldered primary flash chip itself had been
  left off the schematic; added (**W25Q32JVSS**), see §5.
- **Multi-sensor is family-wide; cameras live on the carrier and fit in 260 (was
  deferred).** Datasheet-verified MIPI-RX D-PHY per SoC:
  - **T32** — 4 data + **2 clock** lanes (CLKP0+CLKP1) = **dual 2-lane** (or one
    4-lane) **+ DVP** (muxed onto the CSI pins — verified against the T32 GPIO
    table: `DVP_D0`–`DVP_D11` sit on the same physical analog pads as both
    MIPI lane pairs, "Analog IO, Mipi DVP multiplexing relationship"). Dual-MIPI
    *or* MIPI+DVP, never simultaneously — same restriction as T23/T30/T31/T41.
  - **T33** — 4 data + **2 clock** lanes, 1.5 Gbps = **dual 2-lane** (or 4-lane);
    **DVP removed vs T32** (per the T32/T33 differences doc). Dual-MIPI only.
  - **T40** — 4 data + **2 clock** lanes, 1.5 Gbps = **dual 2-lane** (or 4-lane) +
    separate DVP.
  - **T41** — **single** 2-lane MIPI (one clock lane), 2 Gbps; DVP is **BGA-only**
    and the **QFN96 has none** → our teacup-neo T41 is single-sensor by silicon, and
    T41's "dual" is MIPI+DVP on BGA only. T41 is the *weakest* multi-sensor part here.

  And the **older XBurst1 parts are DVP-primary** — DVP is *mandatory*, not optional:
  - **T10 / T20 / T21** — **12-bit DVP, no MIPI at all.** DVP is their only camera path.
  - **T23** — 2-lane MIPI **+ 8-bit DVP, but they're mutually exclusive on
    silicon, not just a documentation nuance.** Verified against the T23 GPIO
    Recommended Allocation Table: `DVP_D0`–`DVP_D5` are the **same physical
    analog-IO pads** as `MIPI_DATAP0/N0`, `DATAP1/N1`, `CLKP/N` — "MIPI DVP
    multiplexing relationship" per the table itself, not separate pins with a
    shared name. Only `DVP_D6/D7` (PA06/PA07) and the sync lines
    `PCLK/MCLK/HSYNC/VSYNC` (PA14–PA17) are ordinary GPIO. So a T23 interposer
    can wire up MIPI *or* DVP, never both at once — same restriction as T32/T41
    below, contrary to how this looked before verification.
  - **T30 / T31** — 2-lane MIPI **+ 12-bit DVP, same mutual-exclusivity.**
    Verified against the T31 GPIO Recommended Allocation Table: `DVP_D0`–`DVP_D5`
    are the same analog pads as `MIPI_DATAP1/N1`, `CLKP/N`, `DATAP0/N0` — 
    identical pattern to T23. (T30 adds LVDS; no T30-specific GPIO table exists
    in `ingenic-docs` to independently verify, but T30/T31 share the rail table
    and are treated as the same silicon family elsewhere in this doc — §3 — so
    the same pad-sharing is assumed, not independently confirmed for T30.)

  **Revised — no carrier DVP header (§8).** The carrier routes its camera-zone
  to **MIPI FFCs only** (2×, §8's "2nd FFC" pursuit). A SoC that's DVP-primary
  (T10/T20/T21/T23/T30/T31) gets its DVP camera connector **on its own
  interposer**, wired local to the SoC — same principle as the optional
  camera-FFC-on-interposer for mode-A, and as clock (§2, must stay local).
  On **T10/T20/T21** (DVP-only, no MIPI to conflict with) every DVP line is
  ordinary GPIO, so it still reaches the carrier's *general* pin-header
  breakout (§8's "every pin" rule) same as any other SoC pin. On
  **T23/T30/T31** (and T32/T41 above), `DVP_D0`–`D5` **are** the MIPI D-PHY
  pads (previous point) — whichever connector the interposer actually stuffs
  (MIPI FFC or DVP) is what those specific pads go to locally; they don't
  separately also appear at the carrier's generic header breakout the way an
  ordinary GPIO pin would, since it's the same physical pad either way. Only
  `D6`+ and the sync lines are true GPIO on those parts and cross normally.
  What's gone either way is only the **dedicated carrier DVP connector** a
  camera ribbon would plug into; a DVP-primary build now needs that connector
  on the interposer instead. This
  also removes the old dual-MIPI-vs-DVP pin-sharing concern below as a
  carrier-connector question (it was never a *signal-count* problem, §8a).

  **Why a DVP-committed interposer can't just add a header alongside its MIPI
  FFC, for the pad-shared SoCs (T23/T30/T31/T32/T41):** it's not a stuffing-
  option problem, it's a signal-integrity one. `DVP_D0`–`D5` and the MIPI
  D-PHY pads are the *same net*, so routing that net to both a MIPI FFC and a
  separate DVP header creates a stub — and MIPI D-PHY high-speed mode has
  edge rates around 100–200 ps, where even a few mm of unused branch reflects
  real energy back into the link. The stub exists in copper whether or not
  the second connector is populated, so **a MIPI-committed and a
  DVP-committed interposer for the same SoC have to be genuinely separate PCB
  layouts** on that shared pin group, decided at layout time — not two
  footprints on one board with only one stuffed. **T40 is the only SoC here
  where one interposer can carry both live at once**, since its DVP pins
  never share a net with MIPI at all.

  **DVP connector guidance for whoever designs that interposer:** DVP's
  pixel clock is tens-of-MHz, far more forgiving than MIPI's differential
  transmission-line requirements — but a square wave at even 24 MHz still
  carries real harmonic energy into the hundreds of MHz at its edges, so it's
  not a "just use jumper wires" situation either. Plain 0.1" headers are fine
  for a short, local, rigid connection (sensor board stacked right at the
  interposer, grounds interspersed among the data/sync lines). For an actual
  cable run to a separate camera module, the better match is **the same
  mechanical form factor as the MIPI FFC** (a small FFC/FPC, ground-referenced,
  short) **without needing MIPI's differential-impedance engineering** — not
  loose unshielded wire, which invites crosstalk between the 8–12 parallel
  data lines plus clock/sync on anything longer than a few cm.

  **Verified the project's own reference sensor doesn't even need any of
  this:** pulled the primary Sony `IMX327LQR-C` datasheet directly (WebFetch
  couldn't parse the PDF, so downloaded and ran `pdftotext` locally). The
  sensor's `OMODE` pin selects between exactly two output modes — **CSI-2
  serial** (MIPI, 2/4-lane, RAW10/12) or **Sony's proprietary low-voltage LVDS
  serial** (2ch/4ch DDR) — both differential/serial. **There is no parallel/DVP
  output mode on the IMX327 at all.** Matches the local bring-up notes
  (`old/reference/README.md`: confirmed working over a 15-pin MIPI/PiCam-style
  module). So DVP only matters here for someone attaching a *different*
  sensor to a DVP-capable SoC, not for the project's own standard sensor.

  **Not resolved now, by design:** the exact DVP connector part, pin count
  (8/10/12-bit), and interposer layout are deferred to whenever a specific
  DVP-needing interposer actually gets designed — this is guidance for that
  future work, not a part decision belonging to the current carrier-focused
  parts list.

  **Pin budget (§8):** dual 2-lane MIPI = 2× CSI is **already in the ~180-signal
  superset**, routed to carrier FFC(s), and 260 clears it with ~65 grounds. So *all
  the cameras any single SoC can actually run at once* (2 sensors) fit on the carrier
  in 260 — cameras-on-carrier is the default and MIPI crosses the socket fine (§2).
  An interposer may *also* host a camera FFC (optional, for a self-contained mode-A
  module). Carrier supplies sensor power (budgeted 3.3/1.8) + SCCB = plain I²C.
  With DVP now interposer-local rather than needing a carrier connector, the old
  "dual-MIPI + full DVP16 simultaneously" overflow case (§8a) no longer applies to
  carrier connector budgeting — a DVP-using interposer simply doesn't touch the
  carrier's MIPI FFCs at all.
- **Peripheral 3.3/1.8 + power domains (was open):** carrier-local off the single
  5 V input — the interposer stays SoC-only. Two 5 V domains: an **always-on** rail
  (BMC + its own 3.3 LDO, upstream of the reset gate) and a **switched SoC-5 V** rail
  behind one load switch feeding *every* SoC rail — carrier 3.3 (buck ≥2 A) + 1.8
  (LDO off 3.3, quiet, ~1.5 W at 1 A) + mode-B VCORE/VDDR bucks + the connector 5 V
  for mode-A interposer bucks. Everything that touches a SoC pin sits on the switched
  domain, so it all drops together (no ESD back-power into an off SoC) and one gate =
  a clean POR (§9).
- **Mode-B VCORE sense (was open):** no analog remote-sense across the connector
  (finger inductance in the control loop → instability). Kelvin-sense at the connector
  + paralleled VCORE/GND fingers for DC + mandatory interposer decoupling for the fast
  transient + a high-Z **VCORE_SNS** pin to the BMC ADC for **software** remote-sense &
  margining (§2). DC-accurate, unconditionally stable, one connector pin.
- **Rail table complete (§3)** — every SoC's core/DDR/IO voltages are confirmed
  from datasheets (T20 via the T10 datasheet, same silicon; T30 via its own). The
  one number no datasheet states is T30's exact core *current*, but the ≥3 A
  universal VCORE spec covers it with margin regardless. Nothing left to resolve.
- **A1 = full support; GMAC over headers, SATA/HDMI moved to the interposer
  (decided, revised).** A1 is an NVR processor, not a camera — no MIPI/DVP
  sensor input; it ingests video over Ethernet. Supported set: boot
  (NAND/SD/eMMC/USB), 3× UART, 3× USB OTG, **dual RGMII GMAC → carrier pin
  header** (no RJ45 jack, §8), and display-out (HDMI 2.0/VGA/RGB-TFT/BT1120) +
  **dual SATA 3.0** — both **cut from carrier hardware** (§8); an A1 build
  that wants them puts the SATA/HDMI connectors **on the A1 interposer
  itself**, local to the SoC, so those signals **never cross the connector**
  at all (same principle as clock, §2). Unique connector-crossing cost is now
  **≈20 sig** (2nd MAC ~12 + extra USB ~8) — down from the ~28 assumed when
  SATA/HDMI were carrier-hosted and had to cross the socket to reach a
  connector. Use the **A1 SIP-DDR variant** (built-in DDR3L) for a clean small
  interposer; external-DDR A1 puts DRAM on the interposer.

  **Connector rationale reopened, then reconfirmed (§1).** UDIMM-288 was
  justified partly by needing ~93 grounds to safely carry A1's SATA (3 Gbps)
  + HDMI TMDS *across the socket* (§1, §8). With SATA/HDMI now
  interposer-local and never crossing the connector for any build, that
  specific justification no longer holds — A1's remaining unique
  connector-crossing load (2nd MAC + extra USB, ~20 sig) is far lighter than
  before. **Decided (§1): UDIMM-288 stays regardless**, on physical/mechanical
  grounds independent of that pin-budget math — the bigger card and coarser
  0.85 mm pitch are easier to work with by hand than the finer-pitch
  alternatives.

  **VGA/HDMI DDC, for whoever builds that interposer:** verified against
  Ingenic's own A1 reference schematic (`RD_A1_GORILLA_V1.0`, `ingenic-docs`).
  A1 exposes **two separate hardware SMBus/I²C instances**: **SMB0**
  (`PB24`=SDA/`PB25`=SCL), which the reference design dedicates to **display
  DDC** — fanned out via 0Ω link resistors + ESD clamps + a MOSFET level
  shifter (3.3 V SoC side ↔ 5 V DDC side) to both the VGA and HDMI connectors
  — and **SMB1** (`PB10`=SDA/`PB11`=SCL), the reference board's general system
  I²C (audio codec + RTC there). Real, functional I²C on both — not a stub.
  **Implication for an A1 interposer:** use SMB0 for VGA/HDMI DDC, kept
  electrically separate from whatever bus carries the carrier-ID EEPROM (§7)
  or any other interposer I²C traffic — same isolation principle as the
  digipot/DDC separation reasoning already applied elsewhere, and it's what
  Ingenic's own reference design does. Entirely interposer-local; doesn't
  touch carrier I²C planning at all since VGA/HDMI no longer cross the socket.
- **Connector = DDR4 UDIMM-288 desktop, in use for this build (decided, and
  reconfirmed).** Foxconn AH58893-T9B10-3F (LCSC C42403003, SMD vertical, 738
  stock) or Amphenol FCI DDR4288V0213TF — 0.85 mm pitch. Originally justified
  partly by ~93 grounds for A1's SATA/HDMI crossing the socket; that specific
  justification weakened once SATA/HDMI moved to interposer-local (above,
  never crossing the socket at all). Flagged as worth revisiting — **decision:
  stays UDIMM-288 regardless**, on physical/mechanical grounds independent of
  that pin-budget math: the bigger card and coarser 0.85 mm pitch are
  genuinely easier to work with by hand (fab, rework, hand-soldering
  headers/connectors on the interposer) than the finer-pitch alternatives.
  **SO-DIMM-260** (Foxconn ASAA821, deep stock) remains the **compact
  camera-only** re-spin option; **MXM3-314** the max-ground backup — both kept
  on file in §1a, same gold-finger card, re-spun per connector (§1).
- **Camera-SoC peripheral coverage audited (decided, revised — narrowed
  scope).** Every T-series interface is header-reachable (§8 breaks out all
  pins). Only **one** thing gets dedicated carrier hardware now (§8): a plain
  **3.5 mm headphone jack** (`HPOUTL`, no mic/amp). **JTAG, IR-cut/IR-LED
  driving, and anything needing its own connector (SATA/HDMI/DVP), are all
  delegated to whichever interposer needs them** — JTAG specifically because
  it isn't in the same place on every SoC (T40/T31/most have it, T41 QFN96
  doesn't), so it only makes sense stuffed on the interposer whose SoC
  actually has those pins. §8a keeps the original all-on-carrier plan (JTAG
  included) on file. All muxed pins stay in the ~180 superset regardless of
  where the driver hardware lives — no pin-budget cost either way. SSI/SPI
  master = header-only.
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
