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

## 1. Connector: DDR4 card-edge socket (SO-DIMM-260 primary; UDIMM-288 / MXM3-314 options)

A **card-edge** connector: module side = gold fingers (a fab option, $0 parts),
socket on the carrier. Chosen over Socket 370 (module needs machined pins — cost
on the part you build most) and mezzanine stacks (delicate for bench swapping).
Fingers escape perpendicular on their own layer; single row per face, so no
pad-to-pad routing. We use it **mechanically only** — the pinout is ours (§8).
4-layer carrier suffices (no PCIe/DDR crossing the edge).

**Three viable sockets, all card-edge; the interposer mates whichever the carrier
footprint targets** (the card is otherwise universal):

| | **DDR4 SO-DIMM-260 (primary)** | **DDR4 UDIMM-288 desktop (option)** | **MXM3-314 (backup premium)** |
|---|---|---|---|
| Contacts | 260 | 288 | 314 |
| Pitch | 0.5 mm | **0.85 mm** (coarsest) | 0.5 mm |
| Socket length | ~68 mm | **~133 mm** (longest) | ~90 mm |
| Card thickness | 1.0 mm | ~1.0 mm | 1.2 mm |
| Cost | ~$0.83–1.67 | **~$0.5–1.5** | ~$10.69–17 |
| LCSC / JLCPCB | deep, sustained | deep, sustained | last 25, discontinued |
| Ground headroom | ~65 | ~93 | ~119 |
| Trade | compact, cheap | coarse pitch + rugged, **big board** | fine pitch, **scarce** |

**Why SO-DIMM-260 is primary:** compact (~68 mm), ~$1, **deep sustained LCSC stock**
(JLCPCB-assemblable — DDR4 laptop-RAM market is enormous), and its 260 pins are
**enough** (§8: ~180 sig + 15 pwr + 65 gnd).

**DDR4 UDIMM-288 (desktop) — the "coarse-pitch / rugged / max-pins" option.** Real
upsides: **0.85 mm pitch** (easiest, most forgiving edge fingers + most robust
contacts), 288 pins (~93 grounds), a heavy-duty high-cycle socket, and it's as
cheap and LCSC-stocked as SO-DIMM (Foxconn/LOTES 288-pin DDR4 DIMM sockets,
right-angle *or* vertical). The one cost: **~133 mm long** — the socket *and* the
full-width card can't be shortened (latches at both ends), so the carrier and
interposer both roughly double in size vs SO-DIMM. Pick this if you'd rather have a
larger, rugged benchtop rig with the friendliest fingers than a compact board.

**MXM3-314 — backup premium.** A fading laptop-GPU part (JAE discontinued, ACES
0-stock, only 25 on LCSC), kept for when you want max grounds and don't mind
hand-soldering an Amphenol socket. Fine 0.5 mm pitch, ~90 mm.

All three share the gold-finger edge; only pitch, length, card thickness, and the
carrier footprint differ — a design can be re-spun between them.

**Footprints / links:**
- **DDR4 SO-DIMM Foxconn ASAA821-E8SB0-7H** (183 stock, EasyEDA footprint on LCSC): <https://lcsc.com/product-detail/Memory-Connector-DDR_FOXCONN-ASAA821-E8SB0-7H_C2925427.html>
- **DDR4 UDIMM-288 desktop** sockets: LCSC "Memory Connector (DDR)" category (Foxconn/LOTES, right-angle + vertical) — exact PN is a quick LCSC filter (DDR4 / DIMM / 288P).
- MXM3 Amphenol 10151114-001TLF footprint+symbol: <https://www.snapeda.com/search/?q=10151114-001TLF&search-type=parts>
- MXM3 JAE MM70-314B1-2-R300 on LCSC (last 25): <https://www.lcsc.com/product-detail/C4818180.html>
- Pick socket **orientation** (right-angle = card lies flat, low-profile) and
  **stack height** to match the interposer standoff.

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
- **Sensor MIPI defaults to the interposer — but it *can* cross the socket** (this
  is a preference, not a hard rule; don't conflate it with the clock below). D-PHY
  here is 1.5 Gbps/lane (T33/T40) to 2 Gbps/lane (T41), and **both candidate sockets
  are qualified well past that** — DDR4 SO-DIMM passes DDR4-3200 (~1.6 GHz
  differential DQS + 3.2 GT/s DQ); MXM3 carries 8 GT/s PCIe Gen3. Crossing is fine
  with flanking-ground pairs + length match. We still default the camera FFC to the
  interposer for three non-physics reasons: **(1)** zero carrier pins — a dual 2-lane
  sensor is 12 hs signals + grounds, the single biggest pin draw (§10); **(2)** it
  avoids inserting socket discontinuities into the channel; **(3)** the sensor
  topology is SoC-specific (dual-MIPI vs MIPI+DVP vs single). A **carrier-side single
  2-lane MIPI FFC** — the common denominator every SoC has — is a valid option if
  baseboard-mounted cameras are wanted.
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
mode B, digitize each buck's FB divider with a **dual non-volatile I²C digipot**
(**MCP4661**, 257 taps ≈ ~1 mV/step over the core span; LCSC C145605/C637131 —
*stock thin, confirm at BOM or sub any dual-NV I²C pot*). The **ESP32 BMC** (§9)
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
| UDIMM-288 (desktop), full superset | ~180 | ~15 | ~195 | ~93 | very good (option) |
| MXM3-314, full superset | ~180 | ~15 | ~195 | ~119 | luxurious (backup) |

So **260 pins clears the *full* superset** (incl. A1 video) with ~65 grounds —
enough for 1.5 Gbps MIPI + 125 MHz RGMII. 314 just buys spare grounds we don't
strictly need. The only thing that would exceed 260 is a 1-GND-per-signal scheme
(overkill at our speeds) or dual-CSI+DVP16 simultaneous (+~36, deferred §10).
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
~$3.41, ~8.7k in stock, **JLCPCB-assemblable**). Pre-certified: integrates
antenna / RF match / 40 MHz crystal / **16 MB flash / 2 MB PSRAM** — no RF layout
or cert.

**Quad PSRAM (R2), not octal (R8), on purpose:** octal PSRAM consumes GPIO33–37,
and the BMC is GPIO-hungry. Quad PSRAM shares the flash bus and frees those pins →
**~34 usable GPIOs** vs ~29 on R8. The BMC needs ~24 (USB ×2, BOOTSEL, reset /
PPRST_ / VBUS-EN, flash SPI ×6, 3× UART, I²C ×2), so R2 leaves comfortable
headroom. 2 MB PSRAM is plenty — stream flash images in chunks, no need to buffer a
whole 16 MB NOR. Route native-USB **GPIO19 (D−) / GPIO20 (D+)** to the BMC USB-C.
Variants: `-1U` (C3013945, U.FL antenna for metal enclosures/range); `-N8R2` (8 MB
flash) to shave cost; **ESP32-S3-MINI-1** if space-tight.

**Control plane** (agent-facing API over USB-CDC *and/or* WiFi REST/MQTT/telnet):

| Function | Mechanism | Silicon |
|---|---|---|
| **Reset** | power-cycle the **switched SoC 5 V domain** (drops *every* SoC rail — mode-A local bucks and mode-B carrier VCORE/VDDR/3.3/1.8 — for a true POR; BMC is on the always-on domain, so it survives). **Universal**: T41 QFN96 is **POR-only** (System-Control table = just POR_CTL @ pin 60, no PPRST_ → no reset pin). Optional **PPRST_** GPIO on parts that *have* one (T31 QFN88, all BGA) for a warm reset | **load-switch IC** (TPS22918-class) on the SoC-5V domain; PPRST_ = GPIO where present |
| **BOOTSEL** (SFC / SD / USB boot) | drive the strap at POR | ESP32 GPIO + 1 K series R |
| **Flash sharing** (SoC ↔ ESP32) | SoC powered + **BOOTSEL-diverted → SFC is high-Z** ("Hi-Z-rst"); ESP32 owns the shared SPI bus, each master tristates when idle | **just GPIO** (CS + BOOTSEL); a ~6-ch **bus switch is optional** — only to program a fully-*off* SoC |
| **Flash select** (DIP8 ↔ SOP8) | pick the active CS | ESP32 GPIO |
| **Console** | UART1 ↔ WiFi and/or USB-CDC | ESP32 UART |
| USB VBUS (if SoC host mode) | current-limited switch | USB power switch (TPS2051-class) |

Added switching silicon: **one load switch + a couple of GPIOs** (bus switch only
for the fully-off-SoC flash case) — all 3.3 V logic, driven straight off the ESP32.
No relays/SSRs (wrong tool for on-board DC/logic).

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

**Management lines across the connector:** BOOTSEL, reset/power-EN, the SFC flash
bus (CS/CLK/IO0-3), and UART1 run from the carrier BMC to the interposer — a
handful of the 260 positions, already part of the SoC signal set (§8).

---

## 10. Open / deferred / decided

**Open:** none outstanding — the two prior items are resolved (below).

**Deferred (decide later):** none outstanding.

**Decided:**
- **Multi-sensor is family-wide; camera FFC defaults to the interposer (was
  deferred).** Datasheet-verified MIPI-RX D-PHY per SoC:
  - **T32** — 4 data + **2 clock** lanes (CLKP0+CLKP1) = **dual 2-lane** (or one
    4-lane) **+ DVP** (muxed onto the CSI pins). Dual-MIPI *or* MIPI+DVP.
  - **T33** — 4 data + **2 clock** lanes, 1.5 Gbps = **dual 2-lane** (or 4-lane);
    **DVP removed vs T32** (per the T32/T33 differences doc). Dual-MIPI only.
  - **T40** — 4 data + **2 clock** lanes, 1.5 Gbps = **dual 2-lane** (or 4-lane) +
    separate DVP.
  - **T41** — **single** 2-lane MIPI (one clock lane), 2 Gbps; DVP is **BGA-only**
    and the **QFN96 has none** → our teacup-neo T41 is single-sensor by silicon, and
    T41's "dual" is MIPI+DVP on BGA only. T41 is the *weakest* multi-sensor part here.

  Two consequences: (a) the interface varies too much to hardwire one carrier
  superset (dual-MIPI vs MIPI+DVP vs single), and (b) a dual 2-lane sensor is ~12
  high-speed signals + flanking grounds — the pin draw that flagged "past 260." So
  the camera FFC(s) **default to the interposer** = per-module stuffing (dual-sensor
  module = 2 FFC) at **zero carrier-pin cost**. This is a *preference, not physics*:
  the sockets pass 1.5–2 Gbps D-PHY fine (§2), so a **carrier-side single 2-lane MIPI
  FFC** (the 2-lane subset every SoC has) remains an available option. Carrier supplies
  sensor power (budgeted 3.3/1.8) + SCCB = plain I²C; §8's breakout also exposes the
  raw 2-lane MIPI for a carrier-side jumper.
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
