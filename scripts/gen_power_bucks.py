#!/usr/bin/env python3
"""Add the two T41 buck regulators (core 0.8V, DDR 1.35V), keep 3V3/1V8 LDOs.
SY8089A1AAC SOT23-5: 1=EN 2=GND 3=LX 4=IN 5=FB, VOUT=0.6*(1+RH/RL).
  +0V8:  RH=100k RL=300k ; EN<-+1V35 (comes up after DDR)
  +1V35: RH=150k RL=120k ; EN<-+1V8  (comes up after 1V8 LDO)
Removes U3 (MCP1826S, the old insufficient 1A core LDO); its caps remain as
extra decoupling. Connectivity by label / power-symbol name.
"""
import re, uuid
SCH="/home/turismo/projects/teacup-t41/hw/teacup-t41.kicad_sch"
PROJECT="teacup-t41"; SHEET="6e7ef4e6-2026-4726-8de0-60238113f775"
def U(): return str(uuid.uuid4())
sch=open(SCH).read()

# ---------- symbol defs ----------
Rtpl=open("/tmp/claude-1000/-home-turismo/234cdb75-c1bc-43ed-9181-5561545407e2/scratchpad/R_template.txt").read()
Ldef=(Rtpl.replace('"Device:R"','"Device:L"').replace('"R_0_1"','"L_0_1"')
          .replace('"R_1_1"','"L_1_1"').replace('"Resistor"','"Inductor"')
          .replace('property "Value" "R"','property "Value" "L"')
          .replace('property "Reference" "R"','property "Reference" "L"'))

def eff(hide=False):
    return '(effects (font (size 1.27 1.27))'+(' hide' if hide else '')+')'
def pin(et, x, y, a, num, name):
    return (f'        (pin {et} line (at {x} {y} {a}) (length 5.08)\n'
            f'          (name "{name}" {eff()})\n          (number "{num}" {eff()})\n        )')
SY=f'''    (symbol "teacup:SY8089" (pin_names (offset 0.508)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at -10.16 6.985 0) {eff()})
      (property "Value" "SY8089A1AAC" (at 2.54 6.985 0) {eff()})
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23-5" (at 0 0 0) {eff(True)})
      (property "Datasheet" "" (at 0 0 0) {eff(True)})
      (property "ki_description" "2A 1.5MHz synchronous step-down buck, SOT23-5" (at 0 0 0) {eff(True)})
      (symbol "SY8089_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08)
          (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "SY8089_1_1"
{pin("power_in",-10.16,2.54,0,"4","IN")}
{pin("input",-10.16,-2.54,0,"1","EN")}
{pin("power_in",0,-10.16,90,"2","GND")}
{pin("output",10.16,2.54,180,"3","LX")}
{pin("input",10.16,-2.54,180,"5","FB")}
      )
    )
'''
# insert both defs into lib_symbols
sch=sch.replace("\n  (lib_symbols\n","\n  (lib_symbols\n"+Ldef+SY,1)

# ---------- remove U3 (MCP1826S) instance ----------
sch,removed=re.subn(r'  \(symbol \(lib_id "Regulator_Linear:MCP1826S"\).*?\n  \)\n','',sch,flags=re.S)
assert removed==1, f"U3 removal matched {removed}"

# ---------- element emitters ----------
RAILSYM={"+5V":"power:+5V","GND":"power:GND","+0V8":"teacup:+0V8",
         "+1V8":"power:+1V8","+1V35":"teacup:+1V35","+3V3":"power:+3V3"}
pwr_n=max(int(x) for x in re.findall(r'"#PWR0*(\d+)"',sch))+1
adds=[]
def label_at(name,x,y,ang=0):
    adds.append(f'  (label "{name}" (at {x} {y} {ang})\n    (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {U()}))\n')
def pwr_at(rail,x,y,ang=0):
    global pwr_n
    ref=f"#PWR{pwr_n:03d}"; pwr_n+=1
    adds.append(f'''  (symbol (lib_id "{RAILSYM[rail]}") (at {x} {y} {ang}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {U()})
    (property "Reference" "{ref}" (at {x} {y-3.81} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "{rail}" (at {x} {y+3.81} 0) (effects (font (size 1.27 1.27))))
    (pin "1" (uuid {U()}))
    (instances (project "{PROJECT}" (path "/{SHEET}" (reference "{ref}") (unit 1)))))
''')
def node(net,x,y):
    if net in RAILSYM: pwr_at(net,x,y)
    else: label_at(net,x,y)
def passive(ref,lib,val,fp,x,y,net_top,net_bot):
    adds.append(f'''  (symbol (lib_id "{lib}") (at {x} {y} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {U()})
    (property "Reference" "{ref}" (at {x+3.81} {y-1.27} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{val}" (at {x+3.81} {y+1.27} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid {U()})) (pin "2" (uuid {U()}))
    (instances (project "{PROJECT}" (path "/{SHEET}" (reference "{ref}") (unit 1)))))
''')
    node(net_top,x,y-3.81); node(net_bot,x,y+3.81)
def buck(uref, bx, by, en_rail, vout, rh, rl, sw, fb):
    # SY8089 pins abs: IN(-10.16,-2.54off) etc (Y-flip)
    adds.append(f'''  (symbol (lib_id "teacup:SY8089") (at {bx} {by} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {U()})
    (property "Reference" "{uref}" (at {bx-10.16} {by-6.985} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "SY8089A1AAC" (at {bx+2.54} {by-6.985} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_TO_SOT_SMD:SOT-23-5" (at {bx} {by} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid {U()})) (pin "2" (uuid {U()})) (pin "3" (uuid {U()})) (pin "4" (uuid {U()})) (pin "5" (uuid {U()}))
    (instances (project "{PROJECT}" (path "/{SHEET}" (reference "{uref}") (unit 1)))))
''')
    node("+5V",   bx-10.16, by-2.54)   # IN(4)
    node(en_rail, bx-10.16, by+2.54)   # EN(1)
    node("GND",   bx,       by+10.16)  # GND(2)
    label_at(sw,  bx+10.16, by-2.54)   # LX(3)
    label_at(fb,  bx+10.16, by+2.54)   # FB(5)

CF04="C_0402_1005Metric"; CF08="C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
RF="R_0402_1005Metric"; LF="Inductor_SMD:L_1210_3225Metric"
DL="Device:L"; DC="Device:C"; DR="Device:R"

# ---- +0V8 core buck: U6, L1 ----
buck("U6", 170, 250, "+1V35", "+0V8", "R29","R30", "SW_08","FB_08")
passive("L1", DL,"2.2uH",LF, 190,250, "SW_08","+0V8")
passive("C48",DC,"10uF", CF08, 150,258, "+5V","GND")
passive("C49",DC,"22uF", CF08, 200,258, "+0V8","GND")
passive("C50",DC,"100nF",CF04, 208,258, "+0V8","GND")
passive("R29",DR,"100k", RF, 215,244, "+0V8","FB_08")   # RH
passive("R30",DR,"300k", RF, 215,262, "FB_08","GND")    # RL
passive("C51",DC,"22pF", CF04, 222,244, "+0V8","FB_08") # feedforward

# ---- +1V35 DDR buck: U7, L2 ----
buck("U7", 250, 250, "+1V8", "+1V35", "R31","R32", "SW_135","FB_135")
passive("L2", DL,"2.2uH",LF, 270,250, "SW_135","+1V35")
passive("C52",DC,"10uF", CF08, 230,258, "+5V","GND")
passive("C53",DC,"22uF", CF08, 280,258, "+1V35","GND")
passive("C54",DC,"100nF",CF04, 288,258, "+1V35","GND")
passive("R31",DR,"150k", RF, 262,244, "+1V35","FB_135")  # RH
passive("R32",DR,"120k", RF, 262,262, "FB_135","GND")    # RL
passive("C55",DC,"22pF", CF04, 256,244, "+1V35","FB_135")

sch=sch.replace("\n  (sheet_instances","\n"+"".join(adds)+"\n  (sheet_instances",1)
open(SCH,"w").write(sch)
print(f"removed U3; added 2 bucks (U6 +0V8, U7 +1V35) + L1/L2 + {len(adds)} elements")
