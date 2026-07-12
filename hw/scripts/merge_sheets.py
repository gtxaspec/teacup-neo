import re

SHEETS_DIR = "/home/administrator/projects/teacup-neo/hw/sheets"
OUT = "/home/administrator/projects/teacup-neo/hw/teacup-carrier.kicad_sch"

def S(n):
    """Grid steps (50mil / 1.27mm) -> mm, so offsets can't break alignment."""
    return round(n * 1.27, 2)

# (filename, x_offset, y_offset, display title)
# Offsets below match the user's manual GUI rearrangement of 2026-07-13 (each
# quadrant dragged as one block; recovered by diffing symbol (at ...)
# positions in the committed teacup-carrier.kicad_sch against a fresh rebuild
# and confirming a single uniform delta per sheet). Do NOT reset these to
# "recomputed" values without re-diffing against the live file first -- doing
# so silently discards the user's placement on the next rebuild, which is
# exactly what this comment exists to prevent.
SHEETS = [
    ("power", S(4), S(20), "POWER"),
    ("connector", S(0), S(247), "DDR4 UDIMM-288 CONNECTOR"),
    ("bmc", S(243), S(14), "BMC - ESP32-S3"),
    ("io", S(480), S(23), "CARRIER PHYSICAL I/O"),
    ("headers", S(292), S(254), "PIN BREAKOUT HEADERS"),
]

def split_lib_symbols_and_body(text):
    lib_start = text.find("(lib_symbols")
    depth = 0; i = lib_start; instr = False
    while i < len(text):
        c = text[i]
        if c == '"' and text[i-1] != '\\':
            instr = not instr
        elif not instr:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    break
        i += 1
    lib_block = text[lib_start:i+1]
    # body = everything after lib_symbols block, up to (but not including) sheet_instances
    rest = text[i+1:]
    si = rest.find("(sheet_instances")
    body = rest[:si]
    return lib_block, body

def extract_top_symbols(lib_block):
    """Return dict of {top-level symbol name: full block text} for dedup.
    Only extracts DIRECT children of (lib_symbols ...) -- must not also match
    nested sub-unit symbols like "R_0_1", or every part ends up duplicated
    (confirmed: this was a real bug, produced a file that failed to load)."""
    out = {}
    # lib_block starts with "(lib_symbols" -- scan its direct children only
    assert lib_block.startswith("(lib_symbols")
    i = len("(lib_symbols")
    n = len(lib_block)
    while i < n:
        # skip whitespace
        while i < n and lib_block[i] in " \t\n\r":
            i += 1
        if i >= n or lib_block[i] != '(':
            break
        # this is a direct child -- find its name if it's a (symbol "...") form
        child_start = i
        depth = 0; instr = False; j = i
        while j < n:
            c = lib_block[j]
            if c == '"' and lib_block[j-1] != '\\':
                instr = not instr
            elif not instr:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        break
            j += 1
        child = lib_block[child_start:j+1]
        m = re.match(r'\(symbol "([^"]+)"', child)
        if m:
            out[m.group(1)] = child
        i = j + 1
    return out

def shift_coords(body, dx, dy):
    def at_repl(m):
        x, y, rest = float(m.group(1)), float(m.group(2)), m.group(3) or ""
        return f'(at {x+dx:g} {y+dy:g}{rest})'
    body = re.sub(r'\(at ([-\d.]+) ([-\d.]+)((?: [-\d.]+)?)\)', at_repl, body)

    def xy_repl(m):
        x, y = float(m.group(1)), float(m.group(2))
        return f'(xy {x+dx:g} {y+dy:g})'
    body = re.sub(r'\(xy ([-\d.]+) ([-\d.]+)\)', xy_repl, body)
    return body

def bbox(body):
    xs, ys = [], []
    for m in re.finditer(r'\(at ([-\d.]+) ([-\d.]+)(?: [-\d.]+)?\)', body):
        xs.append(float(m.group(1))); ys.append(float(m.group(2)))
    for m in re.finditer(r'\(xy ([-\d.]+) ([-\d.]+)\)', body):
        xs.append(float(m.group(1))); ys.append(float(m.group(2)))
    return min(xs), min(ys), max(xs), max(ys)

MARGIN = 15
TITLE_GAP = 8
PAGE_W, PAGE_H = 1189, 841
SAFE_EDGE = 10

all_symbols = {}
all_bodies = []
frames = []

for name, dx, dy, title in SHEETS:
    text = open(f"{SHEETS_DIR}/{name}.kicad_sch").read()
    lib_block, body = split_lib_symbols_and_body(text)
    syms = extract_top_symbols(lib_block)
    for k, v in syms.items():
        if k in all_symbols and all_symbols[k] != v:
            print(f"WARNING: symbol '{k}' differs between sheets, keeping first occurrence")
        all_symbols.setdefault(k, v)

    x0, y0, x1, y1 = bbox(body)
    rx0, ry0, rx1, ry1 = x0 - MARGIN + dx, y0 - MARGIN + dy, x1 + MARGIN + dx, y1 + MARGIN + dy
    # clamp to the page so the frame/title never hangs off the edge itself --
    # the exact complaint this pass is fixing, so the fix can't recreate it.
    rx0 = max(rx0, SAFE_EDGE)
    ry0 = max(ry0, SAFE_EDGE + TITLE_GAP)
    rx1 = min(rx1, PAGE_W - SAFE_EDGE)
    ry1 = min(ry1, PAGE_H - SAFE_EDGE)
    frames.append(
        f'\t(rectangle (start {rx0:g} {ry0:g}) (end {rx1:g} {ry1:g})\n'
        f'\t\t(stroke (width 0.3) (type dash))\n'
        f'\t\t(fill (type none))\n'
        f'\t\t(uuid "{__import__("uuid").uuid4()}")\n'
        f'\t)\n'
        f'\t(text "{title}" (at {rx0:g} {ry0 - TITLE_GAP:g} 0)\n'
        f'\t\t(effects (font (size 3 3) bold) (justify left bottom))\n'
        f'\t\t(uuid "{__import__("uuid").uuid4()}")\n'
        f'\t)\n'
    )

    shifted = shift_coords(body, dx, dy)
    all_bodies.append(shifted)

lib_syms_text = "\n".join(all_symbols.values())
body_text = "\n".join(all_bodies)
frames_text = "\n".join(frames)

out = f'''(kicad_sch
\t(version 20250114)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "a1b2c3d4-0001-4000-8000-000000000001")
\t(paper "A0")
\t(title_block
\t\t(title "Teacup Universal - Carrier Board")
\t\t(date "2026-07-11")
\t\t(rev "A")
\t\t(company "Teacup Universal")
\t)
\t(lib_symbols
{lib_syms_text}
\t)
{frames_text}
{body_text}
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
)
'''
open(OUT, "w").write(out)
print("wrote", OUT, len(out), "bytes")
print("symbol count:", len(all_symbols))
