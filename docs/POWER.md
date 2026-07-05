# Teacup-T41 power tree

Sources: T41NQ DS v1.6 (6.6.1), T41 Board Design Guide V1.3, T41 HW Checklist
V1.2, MARK_C90_MAIN_V2_0_QFN96 vendor schematic (QFN96 reference board).

## Teacup 3.3 baseline (all-LDO)

5V (USB-C/barrel, D1 TVS) -> AZ1117-3.3 (U1) -> +3V3 -> AZ1117-1.8 (U2) -> +1V8
                                                     -> MCP1826S (U3) -> +0V8
All in/out via 0R links (R2/R3, R6/R7, R8/R9). Fine for T31 (~1W), fatal for
T41: core spec is >= 2A capacity; 3.3->0.8 LDO at 1.5A = 3.75W.

## T41 rail spec (Board Design Guide V1.3)

| Rail | V | Capacity | Ripple | Consumers (QFN96) |
|------|---|----------|--------|-------------------|
| VDD core | 0.8 (0.8-0.88) | >= 2A | <= 60mVpp | pins 8,14,32,41,59,66,81,88 |
| DDRVDD | 1.35 (DDR3L) | >= 1A | <= 70mVpp | 82,87 (+VREF divider) |
| 1.8V | 1.8 | ~0.3A | - | VDDIO18 (17,50), DDRPLL_VCCA(85), CSI_VCCA18(22), CODEC_USB_AVDD(31), SADC_VREFP_AVDD(52), EFUSE(93, tied GND here) |
| 3.3V | 3.3 | ~1A w/ headers | - | VDDIO1 (40,65), VDDIO2 (9), USB_AVD33 (37), NOR, SD, ePHY hdr, PiCam 3.3V |

No 0.8V analog sub-rails on QFN96 (MIPI/USB/DDRPLL cores internal). No 2.8V
needed (PiCam modules regulate on-module from 3.3V; Teacup has no 2V8 rail).

## New tree

```
5V ── AZ1117-1.8 (U2, keep, re-feed from 5V) ──> +1V8          (first up)
5V ── buck1 1.35V/1.5A  EN<-+1V8   ──────────> +1V35 (DDRVDD)  (second)
5V ── buck2 0.8V/2A     EN<-+1V35 RC ────────> +0V8  (core)    (third)
5V ── buck3 3.3V/2A     EN<-+0V8  RC ────────> +3V3            (last)
```

- DS 6.6.1 order: VDDIO18 -> DDRVDD -> VDD08 -> VDDIO33, sum < 5ms. All min
  delays are 0; vendor board (LN5058 x4) uses plain EN pullups, no strict
  chain. EN cascade above gets the order right for ~free.
- Buck: SY8089A1AAC (2A, SOT23-5, 0.6V ref, 1.5MHz) or vendor's
  LN5058/ETA3409/ETA3486 (same 0.6V ref math). 2.2uH/2016 or 2520 inductor,
  10uF+100nF in/out per vendor values.
- FB dividers (0.6V ref): 3.3V=150K/33.2K, 0.8V=100K/300K, 1.35V=150K/120K.
- **T41LQ stuffing option**: DDR FB alt values for 1.8V (e.g. 200K/100K):
  DNP-swap pair on the divider.
- U1 (AZ1117-3.3) + U3 (MCP1826S) deleted. U2 keeps Teacup's SOT-223 spot.

## Strap / misc circuits (vendor-confirmed)

| Item | Treatment |
|------|-----------|
| POR_CTL (60) | 1K to +3V3 (MARK_C90: R31 1K to SOC_3V3) = internal POR |
| BOOT_SEL0 (80) | keep S1 slide: 3V3=SFC boot (default), GND=SD boot; USB loader = fallthrough. 1K series for ESD per checklist |
| PPRST_/S2/J9 | deleted (QFN96 has no reset pin) |
| DDR_ZQ (83), RZQ (84) | 240R 1% each to GND, tight to pins |
| DDR_VREF (86) | 100K/100K 1% off DDRVDD + 100nF (reuse R10/R11/C19 pattern) |
| Crystal | keep 24MHz + 2x12pF + 1M; ADD 33R series (checklist) |
| SFC_CLK | ADD 33R series at SoC |
| UART1 RX | ADD 10K pullup to 3.3V + 33R series both signals (garble/ESD) |
| Analog rails | 1K@100MHz beads off +1V8 to: CSI_VCCA18, DDRPLL_VCCA, CODEC_USB_AVDD, SADC_VREFP_AVDD; bead off +3V3 to USB_AVD33. Local 10uF+100nF each |
| VCM (33) | keep 4.7uF, ADD 100nF (checklist wants both) |
| MICPL/MICNL (29/30) | 100nF series each at chip; 2.2K bias at mic; MICNL to mic ground reference (pseudo-diff) |
| USB ID | n/a on QFN96; host/device fixed in FW (or GPIO-simulated) |
| EFUSE_AVDD (93) | tied GND (programming off), keep Teacup behavior |

## Flash

- U4 W25Q32JVSS (4MB) -> suggest W25Q128JVS (16MB) for thingino.
- Wire SFC0_WP_IO2 (42) -> U4.3, SFC0_HOLD_IO3 (45) -> U4.7; keep 100K
  pullups (R13/R14) -> quad-SPI capable.
- Keep SW2 CS-disconnect switch + J16 header (USB-boot recovery trick).

## Thermal

QFN96 epad: full via farm to inner GND + bottom copper. T41 dissipates
~1.5-2W under NPU load; vendor thermal AN applies.
