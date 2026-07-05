#!/usr/bin/env python3
"""Add T41-specific passives + fixes to the schematic (label-connected):
  - DDR ZQ:  R26 240R DDR_ZQ->GND, R27 240R RZQ->GND
  - POR:     R28 1K POR_CTL->+3V3 (internal-POR strap)
  - MICNL:   C47 100nF MICNL->GND (AC ref for neg mic input; full bias TBD)
  - NOR quad: label U4.3=NOR_WP, U4.7=NOR_HOLD -> connect T41 SFC IO2/IO3
  - VREF:    retarget divider top R10.1 from +1V8 to +1V35 (=1.35/2=0.675V)
"""
import re, uuid
SCH="/home/turismo/projects/teacup-t41/hw/teacup-t41.kicad_sch"
PROJECT="teacup-t41"; SHEET="6e7ef4e6-2026-4726-8de0-60238113f775"
def U(): return str(uuid.uuid4())
sch=open(SCH).read()

# --- 1. VREF retarget: the power:+1V8 at R10.1 (177.8,121.92) -> teacup:+1V35 ---
def swap(m):
    blk=m.group(0)
    at=re.search(r'\(at ([-\d.]+) ([-\d.]+)',blk)
    if abs(float(at.group(1))-177.8)<0.05 and abs(float(at.group(2))-121.92)<0.05:
        swap.done+=1
        return blk.replace('"power:+1V8"','"teacup:+1V35"').replace('"+1V8"','"+1V35"')
    return blk
swap.done=0
sch=re.sub(r'  \(symbol \(lib_id "power:\+1V8"\) \(at [-\d.]+ [-\d.]+ \d+\).*?\n  \)\n', swap, sch, flags=re.S)
assert swap.done==1, f"VREF retarget matched {swap.done}"

# --- helpers ---
RAILSYM={"+3V3":"power:+3V3","GND":"power:GND","+1V35":"teacup:+1V35"}
pwrnums=[int(x) for x in re.findall(r'"#PWR0*(\d+)"',sch)]; pwr_n=max(pwrnums)+1
adds=[]
def label_at(name,x,y):
    adds.append(f'  (label "{name}" (at {x} {y} 0)\n    (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {U()}))\n')
def pwr_at(rail,x,y,ang=0):
    global pwr_n
    ref=f"#PWR{pwr_n:03d}"; pwr_n+=1
    adds.append(f'''  (symbol (lib_id "{RAILSYM[rail]}") (at {x} {y} {ang}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {U()})
    (property "Reference" "{ref}" (at {x} {y-2.54} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "{rail}" (at {x} {y+2.54} 0) (effects (font (size 1.27 1.27))))
    (pin "1" (uuid {U()}))
    (instances (project "{PROJECT}" (path "/{SHEET}" (reference "{ref}") (unit 1)))))
''')
def passive(ref,lib,val,fp,x,y,net_top,net_bot):
    # vertical part: pin1(top)=(x,y-3.81), pin2(bot)=(x,y+3.81)
    adds.append(f'''  (symbol (lib_id "{lib}") (at {x} {y} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {U()})
    (property "Reference" "{ref}" (at {x+2.54} {y-1.27} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{val}" (at {x+2.54} {y+1.27} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid {U()})) (pin "2" (uuid {U()}))
    (instances (project "{PROJECT}" (path "/{SHEET}" (reference "{ref}") (unit 1)))))
''')
    # top pin -> net_top, bottom pin -> net_bot
    for (nx,ny),net in [((x,y-3.81),net_top), ((x,y+3.81),net_bot)]:
        if net in RAILSYM: pwr_at(net,nx,ny)
        else: label_at(net.lstrip("/"),nx,ny)

R="Device:R"; C="Device:C"
RF="R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"; CF="C_0402_1005Metric"
# place new parts in an open area (bottom-right); connectivity is by name
passive("R26",R,"240R",RF, 300,250, "/DDR_ZQ","GND")
passive("R27",R,"240R",RF, 312,250, "/RZQ","GND")
passive("R28",R,"1K",  RF, 324,250, "/POR_CTL","+3V3")
passive("C47",C,"100nF",CF,336,250, "/MICNL","GND")
# NOR quad: name the flash IO2/IO3 nets at U4 pins
label_at("NOR_WP",   365.76, 186.69)   # U4.3
label_at("NOR_HOLD", 365.76, 189.23)   # U4.7

sch=sch.replace("\n  (sheet_instances","\n"+"".join(adds)+"\n  (sheet_instances",1)
open(SCH,"w").write(sch)
print(f"added 4 passives + NOR labels + VREF retarget; {len(adds)} elements")
