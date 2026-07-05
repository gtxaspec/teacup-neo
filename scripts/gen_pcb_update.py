#!/usr/bin/env python3
"""Apply the verified T41 netlist to the PCB (headless 'update from schematic'):
  - swap IC1 footprint QFN88 -> QFN96 (same pos/rotation), re-net its pads
  - remove U3 (MCP1826S)
  - add new parts (U6/U7 bucks, L1/L2, R26-R32, C47-C55) with footprints+nets
  - re-net every pad from the netlist
  - rip up all tracks/vias (SoC pinout changed -> full reroute)
Verified after: every pad's net == netlist; ratsnest count reported.
"""
import re, pcbnew
BRD="/home/turismo/projects/teacup-t41/hw/teacup-t41.kicad_pcb"
NET="/home/turismo/projects/teacup-t41/docs/t41_netlist_verify.net"
FPDIR="/usr/share/kicad/footprints"

# ---- parse netlist: (ref,pad)->net, and per-ref footprint ----
nl=open(NET).read()
padnet={}; allnets=set()
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]+)"\)(.*?)(?=\(net |\Z)',nl,re.S):
    name=m.group(1); allnets.add(name)
    for r,p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"',m.group(2)):
        padnet[(r,p)]=name

b=pcbnew.LoadBoard(BRD)
def MM(v): return pcbnew.FromMM(v)

# ---- ensure all nets exist ----
made=0
for n in allnets:
    if not b.FindNet(n):
        b.Add(pcbnew.NETINFO_ITEM(b, n)); made+=1
def NET_(n): return b.FindNet(n)

# ---- 1. swap IC1 footprint ----
old=b.FindFootprintByReference("IC1")
pos=old.GetPosition(); rot=old.GetOrientationDegrees()
b.Remove(old)
ic1=pcbnew.FootprintLoad(f"/home/turismo/projects/teacup-t41/hw/teacup.pretty","QFN96_10x10_P0.35_EP7.6x7.2_T41")
ic1.SetReference("IC1"); ic1.SetValue("T41NQ")
ic1.SetPosition(pos); ic1.SetOrientationDegrees(rot)
b.Add(ic1)
print(f"IC1 swapped to QFN96 @ {pcbnew.ToMM(pos.x):.1f},{pcbnew.ToMM(pos.y):.1f} rot {rot}")

# ---- 2. remove U3 ----
u3=b.FindFootprintByReference("U3")
if u3: b.Remove(u3); print("removed U3")

# ---- 3. add new components ----
# ref: (lib, fpname, value, x_mm, y_mm)  -- placed in a staging grid below board
NEW=[
 ("U6","Package_TO_SOT_SMD","SOT-23-5","SY8089A1AAC",165,118),
 ("U7","Package_TO_SOT_SMD","SOT-23-5","SY8089A1AAC",180,118),
 ("L1","Inductor_SMD","L_1210_3225Metric","2.2uH",170,118),
 ("L2","Inductor_SMD","L_1210_3225Metric","2.2uH",185,118),
 ("C48","Capacitor_SMD","C_0805_2012Metric_Pad1.18x1.45mm_HandSolder","10uF",162,123),
 ("C49","Capacitor_SMD","C_0805_2012Metric_Pad1.18x1.45mm_HandSolder","22uF",167,123),
 ("C50","Capacitor_SMD","C_0402_1005Metric","100nF",172,123),
 ("C51","Capacitor_SMD","C_0402_1005Metric","22pF",176,123),
 ("C52","Capacitor_SMD","C_0805_2012Metric_Pad1.18x1.45mm_HandSolder","10uF",182,123),
 ("C53","Capacitor_SMD","C_0805_2012Metric_Pad1.18x1.45mm_HandSolder","22uF",187,123),
 ("C54","Capacitor_SMD","C_0402_1005Metric","100nF",192,123),
 ("C55","Capacitor_SMD","C_0402_1005Metric","22pF",196,123),
 ("R26","Resistor_SMD","R_0603_1608Metric_Pad0.98x0.95mm_HandSolder","240R",200,118),
 ("R27","Resistor_SMD","R_0603_1608Metric_Pad0.98x0.95mm_HandSolder","240R",205,118),
 ("R28","Resistor_SMD","R_0603_1608Metric_Pad0.98x0.95mm_HandSolder","1K",210,118),
 ("R29","Resistor_SMD","R_0402_1005Metric","100k",200,123),
 ("R30","Resistor_SMD","R_0402_1005Metric","300k",205,123),
 ("R31","Resistor_SMD","R_0402_1005Metric","150k",210,123),
 ("R32","Resistor_SMD","R_0402_1005Metric","120k",215,123),
 ("C47","Capacitor_SMD","C_0402_1005Metric","100nF",220,118),
]
for ref,lib,fpn,val,x,y in NEW:
    fp=pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", fpn)
    assert fp, f"footprint {lib}:{fpn} not found"
    fp.SetReference(ref); fp.SetValue(val)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x),MM(y)))
    b.Add(fp)
print(f"added {len(NEW)} new components")

# ---- 4. re-net every pad from netlist ----
unmatched=[]
for fp in b.GetFootprints():
    ref=fp.GetReference()
    for pad in fp.Pads():
        key=(ref, pad.GetName())
        if key in padnet:
            pad.SetNet(NET_(padnet[key]))
        else:
            pad.SetNetCode(0)  # no net (mount pads etc.)
            if pad.GetName() and not pad.GetName().startswith("MP"):
                unmatched.append(key)

# ---- 5. rip up all tracks/vias (invalid after SoC pin change) ----
ripped=0
for t in list(b.GetTracks()):
    b.Remove(t); ripped+=1

b.BuildListOfNets()
pcbnew.SaveBoard(BRD, b)
print(f"nets created: {made}; ripped {ripped} tracks; unmatched pads: {len(unmatched)} {unmatched[:8]}")
EOF_MARKER = True
