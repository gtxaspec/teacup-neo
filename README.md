# Teacup-T41

T41 (QFN96) adaptation of the [Teacup Rev-C](https://github.com/CapnRon/Teacup) T31 development board.

Targets **T41NQ (128MB)**, **T41XQ (256MB)**, and **T41LQ (64MB)** — all three are
pin-identical in the QFN96 package, so one layout serves all three as a stuffing
option (LQ needs the DDR rail set to 1.8V instead of 1.35V via the FB divider).

## Status

| Stage | State |
|-------|-------|
| Pin map / power design | complete, verified against 3 datasheets |
| QFN96 footprint + T41NQ symbol | KiCad-validated |
| Schematic | **netlist-verified** — all 97 SoC pins on intended nets, 0 peripheral connections lost |
| PCB netlist applied | 479 pads re-netted, 0 mismatch |
| Routing | **~83% auto-routed** (FreeRouting); 78 nets + placement + 3 shorts need GUI finishing |
| Manufacturing outputs | BOM/pos complete; Gerbers are a **draft** (board not yet fab-ready) |

**This board is NOT fab-ready.** The design (schematic + netlist) is complete and
fully verified, but the PCB was auto-routed headlessly with best-effort blind
placement. Before fabrication it needs, in the KiCad GUI:
- placement de-overlap of the bottom-side power section (7 courtyard overlaps)
- the 78 remaining ratsnest connections routed
- 3 shorts / clearance violations resolved
- **MIPI CSI routed as 100 ohm impedance-controlled differential pairs** (an
  autorouter does not do controlled impedance)
- SFC/DDR length + return-path review per the T41 Hardware Design Guide

## Power tree

2x SY8089A1AAC buck (core 0.8V/2A EN<-1.35V, DDR 1.35V EN<-1.8V) + kept AZ1117
LDOs (3.3V, 1.8V). EN cascade gives the datasheet power-on order. See `docs/POWER.md`.

## Layout

- `hw/` — KiCad project (based on TeaCup(C)3.3)
- `hw/Manufacturing/` — draft Gerbers, drill, BOM, position, DRC report
- `docs/` — pin maps, power design, netlist verification
- `scripts/` — the headless generators (footprint, symbol, schematic, PCB, routing)
- `reference/` — upstream 3.3 artifacts

Built headlessly with KiCad 9.0.2 (kicad-cli + pcbnew) + FreeRouting 1.9.0.

License: GPL-3.0 (inherited from upstream).
