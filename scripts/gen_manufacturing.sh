#!/bin/bash
# Generate manufacturing outputs for teacup-t41 (run after routing + DRC).
set -e
cd "$(dirname "$0")/.."
PCB=hw/teacup-t41.kicad_pcb
OUT=hw/Manufacturing
mkdir -p "$OUT"

echo "=== DRC ==="
kicad-cli pcb drc --exit-code-violations --severity-error -o "$OUT/drc.rpt" "$PCB" 2>&1 | tail -2 || true

echo "=== Gerbers + drill ==="
kicad-cli pcb export gerbers -o "$OUT/gerber/" "$PCB" 2>&1 | tail -1
kicad-cli pcb export drill -o "$OUT/gerber/" "$PCB" 2>&1 | tail -1

echo "=== Position (centroid) file ==="
kicad-cli pcb export pos --format csv --units mm -o "$OUT/teacup-t41-pos.csv" "$PCB" 2>&1 | tail -1

echo "=== BOM ==="
kicad-cli sch export bom \
  --fields 'Reference,Value,Footprint,${QUANTITY},${DNP}' \
  --group-by 'Value,Footprint' \
  -o "$OUT/teacup-t41-bom.csv" hw/teacup-t41.kicad_sch 2>&1 | tail -1

echo "=== render top+bottom ==="
kicad-cli pcb export svg --layers F.Cu,F.Silkscreen,F.Mask,Edge.Cuts --page-size-mode 2 -o "$OUT/top.svg" "$PCB" 2>/dev/null | tail -1
kicad-cli pcb export svg --layers B.Cu,B.Silkscreen,B.Mask,Edge.Cuts --page-size-mode 2 --mirror -o "$OUT/bottom.svg" "$PCB" 2>/dev/null | tail -1

ls -la "$OUT"
