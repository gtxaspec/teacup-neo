#!/usr/bin/env python3
"""Import the FreeRouting SES session back into the board, refill zones, save."""
import sys, pcbnew
BRD="/home/turismo/projects/teacup-t41/hw/teacup-t41.kicad_pcb"
SES="/tmp/claude-1000/-home-turismo/234cdb75-c1bc-43ed-9181-5561545407e2/scratchpad/t41.ses"
b=pcbnew.LoadBoard(BRD)
ok=pcbnew.ImportSpecctraSES(b, SES)
print("SES import:", ok)
# refill copper zones
fill=pcbnew.ZONE_FILLER(b); fill.Fill(b.Zones())
b.BuildConnectivity()
pcbnew.SaveBoard(BRD, b)
tracks=len(b.GetTracks())
vias=sum(1 for t in b.GetTracks() if t.Type()==pcbnew.PCB_VIA_T)
print(f"tracks: {tracks} (vias: {vias})")
