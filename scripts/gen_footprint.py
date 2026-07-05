#!/usr/bin/env python3
"""Generate QFN96 10x10 0.35mm footprint for T41NQ/XQ/LQ.

Dims from T41NQ_ds_v1.6 Table 4-1 (JEDEC MO-220):
  body 10x10 BSC, pitch 0.35 BSC, lead b=0.17 nom (0.12-0.22), L=0.4 (0.3-0.5),
  EP D2xE2 = 7.6 x 7.2 nom.
Land pattern follows the proven Teacup QFN88 construction (pad 0.85 radial,
pad centerline 0.05 inside body edge), scaled to 10x10 / 24-per-side.
Thermal pad uses a 3x3 windowed paste array (~65% coverage).
"""
import uuid

PITCH = 0.35
NSIDE = 24
BODY = 10.0
HALF = BODY / 2                      # 5.0
PAD_CTR = HALF - 0.05                # 4.95 pad centerline (matches T31 inset)
PAD_W = 0.18                         # perpendicular to pitch (gap 0.17)
PAD_L = 0.85                         # radial solderable length
EP_X, EP_Y = 7.4, 7.0               # copper EP (slightly under nominal 7.6x7.2)
CRTYD = HALF + 0.625                 # 5.625 (matches T31 courtyard inset)
SILK = HALF - 0.0                    # silk box near body edge
FAB = HALF

def u():
    return str(uuid.uuid4())

# 24 centered positions along an edge: span (24-1)*0.35 = 8.05, -4.025..+4.025
span0 = -(NSIDE - 1) * PITCH / 2      # -4.025
pos = [round(span0 + i * PITCH, 4) for i in range(NSIDE)]

pads = []
def pad(n, x, y, rot):
    # size given as (across-pitch, radial); rot 90 swaps so radial lands on X
    if rot == 90:
        size = f"{PAD_L} {PAD_W}"
    else:
        size = f"{PAD_W} {PAD_L}"
    pads.append(f'  (pad "{n}" smd roundrect (at {x} {y}) (size {size}) '
                f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (tstamp {u()}))')

n = 1
# Left edge: pins 1-24, x=-PAD_CTR, y top->bottom
for i in range(NSIDE):
    pad(n, -PAD_CTR, pos[i], 90); n += 1
# Bottom edge: pins 25-48, y=+PAD_CTR, x left->right
for i in range(NSIDE):
    pad(n, pos[i], PAD_CTR, 0); n += 1
# Right edge: pins 49-72, x=+PAD_CTR, y bottom->top
for i in range(NSIDE):
    pad(n, PAD_CTR, pos[NSIDE - 1 - i], 90); n += 1
# Top edge: pins 73-96, y=-PAD_CTR, x right->left
for i in range(NSIDE):
    pad(n, pos[NSIDE - 1 - i], -PAD_CTR, 0); n += 1
assert n == 97

# Thermal pad 97: copper+mask (no paste on main), plus 3x3 paste windows
ep = []
ep.append(f'  (pad "97" smd rect (at 0 0) (size {EP_X} {EP_Y}) '
          f'(layers "F.Cu" "F.Mask") (tstamp {u()}))')
ap_w, ap_h = 2.0, 1.9
offs_x = [-2.35, 0.0, 2.35]
offs_y = [-2.3, 0.0, 2.3]
for oy in offs_y:
    for ox in offs_x:
        ep.append(f'  (pad "97" smd rect (at {ox} {oy}) (size {ap_w} {ap_h}) '
                  f'(layers "F.Paste") (tstamp {u()}))')

def line(x1, y1, x2, y2, layer, w):
    return (f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) '
            f'(stroke (width {w}) (type solid)) (layer "{layer}") (tstamp {u()}))')

gfx = []
# Silk box (broken at pin-1 corner), Fab box, courtyard
for layer, half, w in [("F.SilkS", SILK, 0.12), ("F.Fab", FAB, 0.1)]:
    gfx += [
        line(-half + 0.5, -half, half, -half, layer, w),   # top (gap at TL)
        line(half, -half, half, half, layer, w),
        line(half, half, -half, half, layer, w),
        line(-half, half, -half, -half + 0.5, layer, w),
        line(-half, -half + 0.5, -half + 0.5, -half, layer, w),  # chamfer TL
    ]
gfx.append(f'  (fp_circle (center {-PAD_CTR-0.55} {pos[0]}) (end {-PAD_CTR-0.45} {pos[0]}) '
           f'(stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS") (tstamp {u()}))')
for (x1,y1,x2,y2) in [(-CRTYD,-CRTYD,CRTYD,-CRTYD),(CRTYD,-CRTYD,CRTYD,CRTYD),
                      (CRTYD,CRTYD,-CRTYD,CRTYD),(-CRTYD,CRTYD,-CRTYD,-CRTYD)]:
    gfx.append(line(x1,y1,x2,y2,"F.CrtYd",0.05))

body = f'''(footprint "QFN96_10x10_P0.35_EP7.6x7.2_T41" (version 20221018) (generator gen_footprint.py)
  (layer "F.Cu")
  (descr "Ingenic T41NQ/XQ/LQ QFN-96 10x10mm 0.35mm pitch, EP 7.6x7.2 (JEDEC MO-220). Land pattern derived from Teacup QFN88.")
  (tags "Ingenic T41 QFN96 SIP")
  (property "Datasheet" "T41NQ_ds_v1.6")
  (property "ki_description" "Ingenic T41 QFN-96 10x10mm 0.35 pitch SIP DDR3")
  (attr smd)
  (fp_text reference "IC1" (at 0 {-CRTYD-0.6}) (layer "F.SilkS")
      (effects (font (size 1 1) (thickness 0.15))) (tstamp {u()}))
  (fp_text value "T41NQ" (at 0 {CRTYD+0.6}) (layer "F.Fab")
      (effects (font (size 1 1) (thickness 0.15))) (tstamp {u()}))
  (fp_text user "${{REFERENCE}}" (at 0 0) (layer "F.Fab")
      (effects (font (size 1 1) (thickness 0.15))) (tstamp {u()}))
{chr(10).join(gfx)}
{chr(10).join(pads)}
{chr(10).join(ep)}
)
'''

out = "/home/turismo/projects/teacup-t41/hw/teacup.pretty/QFN96_10x10_P0.35_EP7.6x7.2_T41.kicad_mod"
open(out, "w").write(body)
print(f"wrote {out}")
print(f"pads: {len(pads)} perimeter + 1 EP cu + {len(ep)-1} paste windows")
print(f"pin1 @ ({-PAD_CTR}, {pos[0]}); pin24 @ ({-PAD_CTR}, {pos[-1]}); pitch {PITCH}")
