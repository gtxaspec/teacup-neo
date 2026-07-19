"""Minimal helper for programmatically building a KiCad 10 .kicad_sch body.

Hard design rules enforced by this module (per explicit user requirement):
  1. Every coordinate must land on the 50mil (1.27mm) schematic grid. This is
     asserted at generation time, not checked afterward -- a bad coordinate
     is a crash, not a rendering surprise.
  2. Power-rail pins (GND, +3V3, etc.) get their flag placed DIRECTLY at the
     pin -- no stub wire needed, since two things at the exact same point
     are electrically connected without a drawn wire. Sheet.flag() is the
     one function that should be used for this; it also handles the "fan
     out" case (bus consecutive same-net pins on a tight pitch to a single
     flag placed clear of everything) when a direct placement would collide
     with a neighboring row.
"""
import re, uuid, math

GRID = 1.27  # 50 mil, per explicit user requirement

# Fixed, arbitrary namespace for deriving deterministic per-symbol UUIDs (see
# Sheet.place()) -- symbol UUIDs used to be uuid.uuid4() (fresh, random,
# different on every regeneration), which meant PCB footprints could never
# stay linked to their schematic symbol across a rebuild: KiCad's "Update PCB
# from Schematic" matches by that UUID (via the footprint's (path ...)
# field), so every regeneration silently orphaned every existing footprint
# and offered to place a full duplicate set instead. Reference designators
# are unique across this whole (flat, single-sheet) schematic by
# construction, so hashing the ref into a stable UUID keeps the same symbol
# identity across rebuilds without changing anything else.
UUID_NAMESPACE = uuid.UUID("a1b2c3d4-1111-4000-8000-000000000000")

def stable_uuid(ref):
    return str(uuid.uuid5(UUID_NAMESPACE, ref))

def snap(v):
    return round(round(v / GRID) * GRID, 3)

def assert_grid(v, ctx=""):
    s = snap(v)
    if abs(v - s) > 1e-3:
        raise ValueError(f"{ctx}: {v} is not on the {GRID}mm (50mil) grid (nearest: {s})")

def assert_grid_xy(x, y, ctx=""):
    assert_grid(x, ctx + " (x)")
    assert_grid(y, ctx + " (y)")

def paren_block(text, start):
    depth, inq, j = 0, False, start
    while j < len(text):
        c = text[j]
        if c == '"' and text[j-1] != '\\':
            inq = not inq
        elif not inq:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return text[start:j+1]
        j += 1
    raise ValueError("unterminated")

def load_symbol_def(libfile, symname):
    text = open(libfile).read()
    m = re.search(r'\n?[ \t]*\(symbol "' + re.escape(symname) + r'"', text)
    if not m:
        raise ValueError(f"{symname} not found in {libfile}")
    start = text.find('(symbol', m.start())
    return paren_block(text, start)

def get_pins(symdef):
    """Return list of (name, number, x, y, angle) for all sub-unit pins."""
    pins = []
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', symdef):
        x, y, ang = m.group(1), m.group(2), m.group(3)
        block = paren_block(symdef, m.start())
        nm = re.search(r'\(name "([^"]*)"', block).group(1)
        nu = re.search(r'\(number "([^"]*)"', block).group(1)
        pins.append((nm, nu, float(x), float(y), float(ang)))
    return pins

class Sheet:
    def __init__(self):
        self.symbol_defs = {}   # lib_id -> raw sexpr (renamed to bare name for lib_symbols cache)
        self.instances = []     # rendered (symbol ...) blocks
        self.wires = []
        self.labels = []
        self.junctions = []
        self.texts = []
        self.pin_cache = {}     # lib_id -> pins list
        self._flag_n = {"GND": 0, "+3V3": 0}

    def ensure_symbol(self, libfile, symname, lib_id):
        if lib_id in self.symbol_defs:
            return
        raw = load_symbol_def(libfile, symname)
        # Only the TOP-LEVEL symbol name gets the "libname:" prefix in a cached
        # lib_symbols copy. Nested sub-unit symbols (e.g. "R_0_1", "R_1_1") stay
        # bare/unprefixed -- confirmed against a real working KiCad schematic.
        # BUT: if lib_id renames the part to a genuinely different bare name,
        # the sub-unit names must be renamed to match too, or KiCad rejects
        # the whole file outright.
        old_bare = symname.split(":", 1)[-1]
        new_bare = lib_id.split(":", 1)[-1]
        raw = re.sub(r'^\(symbol "' + re.escape(symname) + r'"', f'(symbol "{lib_id}"', raw, count=1)
        if new_bare != old_bare:
            raw = re.sub(r'\(symbol "' + re.escape(old_bare) + r'(_\d+_\d+)"',
                         lambda m: f'(symbol "{new_bare}{m.group(1)}"', raw)
        self.symbol_defs[lib_id] = raw
        self.pin_cache[lib_id] = get_pins(raw)

    def place(self, lib_id, ref, value, x, y, angle=0, extra_props=None, footprint=None,
              unit=1, mirror=None, hide_ref=False, hide_value=False,
              ref_at=None, value_at=None):
        """ref_at / value_at: optional (x, y, angle) overrides for the
        Reference/Value property text placement. NOTE: KiCad renders a
        property at (symbol angle + property angle), so to force
        horizontal text on a rotated symbol pass angle=(-symbol_angle)%360."""
        assert_grid_xy(x, y, f"place({lib_id} {ref})")
        u = stable_uuid(ref)
        ref_hide = " hide" if hide_ref else ""
        val_hide = " hide" if hide_value else ""
        rx, ry, rang = ref_at if ref_at else (x, y-3, 0)
        vx, vy, vang = value_at if value_at else (x, y+3, 0)
        props = f'\t\t(property "Reference" "{ref}" (at {rx} {ry} {rang}) (effects (font (size 1.27 1.27)){ref_hide}))\n'
        props += f'\t\t(property "Value" "{value}" (at {vx} {vy} {vang}) (effects (font (size 1.27 1.27)){val_hide}))\n'
        if footprint:
            props += f'\t\t(property "Footprint" "{footprint}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        if extra_props:
            for k, v in extra_props.items():
                props += f'\t\t(property "{k}" "{v}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        mirror_s = f" (mirror {mirror})" if mirror else ""
        block = (f'\t(symbol (lib_id "{lib_id}") (at {x} {y} {angle}){mirror_s} (unit {unit})\n'
                  f'\t\t(uuid "{u}")\n' + props + '\t)\n')
        self.instances.append(block)
        return u

    def pin_pos(self, lib_id, ref_x, ref_y, angle, pin_number, mirror=None):
        """Compute the absolute schematic position of a given pin number after placement rotation."""
        pins = self.pin_cache[lib_id]
        for (nm, nu, px, py, pang) in pins:
            if nu == pin_number:
                if mirror == 'x':
                    py = -py
                elif mirror == 'y':
                    px = -px
                rad = math.radians(angle)
                rx = px*math.cos(rad) - py*math.sin(rad)
                ry = px*math.sin(rad) + py*math.cos(rad)
                return round(ref_x+rx, 3), round(ref_y-ry, 3)  # KiCad y-down vs symbol-lib y-up
        raise ValueError(f"pin {pin_number} not found for {lib_id}")

    def decoupler(self, lib_id, ref, val, tap_xy, gnd_dir_xy, cx, cy, angle=0, footprint=None):
        """Place a 2-pin part between a rail tap and its own GND stub, choosing
        automatically which pin is nearer the tap so the connecting wire never
        has to travel PAST the other pin on the same column/row (a real bug:
        KiCad connects a wire to any pin its path crosses, not just endpoints,
        so 'reaching past' a pin silently shorts nets together)."""
        s = self
        s.place(lib_id, ref, val, cx, cy, angle, footprint=footprint)
        p1 = s.pin(lib_id, cx, cy, angle, "1")
        p2 = s.pin(lib_id, cx, cy, angle, "2")
        tx, ty = tap_xy
        def dist(p): return (p[0]-tx)**2 + (p[1]-ty)**2
        near, far = (p1, p2) if dist(p1) <= dist(p2) else (p2, p1)
        if near[0] != tx:
            s.wire(tx, ty, near[0], ty)
        if near[1] != ty:
            s.wire(near[0], ty, near[0], near[1])
        if gnd_dir_xy is not None:
            gx, gy = gnd_dir_xy
            s.wire(far[0], far[1], gx, gy)
        return near, far

    def wire(self, x1, y1, x2, y2):
        assert_grid_xy(x1, y1, "wire start")
        assert_grid_xy(x2, y2, "wire end")
        if x1 == x2 and y1 == y2:
            return  # zero-length wire (e.g. flag placed exactly at a pin) -- nothing to draw
        self.wires.append(f'\t(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uuid.uuid4()}"))\n')

    def label(self, text, x, y, angle=0, global_=False):
        """Net label anchored at (x, y). Justification must follow the
        angle: with (justify left) the text runs in +x/+y FROM the anchor
        regardless of angle, so a 180/270 label anchored on a pin renders
        INTO the component body (confirmed by render); (justify right)
        flips it to extend away from the anchor in the pointing direction."""
        assert_grid_xy(x, y, f"label({text})")
        kind = "global_label" if global_ else "label"
        justify = "left" if angle in (0, 90) else "right"
        self.labels.append(f'\t({kind} "{text}" (at {x} {y} {angle}) (effects (font (size 1.27 1.27)) (justify {justify})) (uuid "{uuid.uuid4()}"))\n')

    def pin(self, lib_id, ref_x, ref_y, angle, pin_number, mirror=None):
        """Shorthand: pin_pos with the component's own placement params."""
        return self.pin_pos(lib_id, ref_x, ref_y, angle, pin_number, mirror)

    # KiCad pin angle -> the direction the pin EXITS the component (i.e.
    # the direction a label/flag at the connection point should extend),
    # for a symbol placed unrotated. A pin's angle says which way it runs
    # from its connection point INTO the body, so the exit direction is
    # the opposite; the y-flip between symbol space (y up) and schematic
    # space (y down) swaps up/down.
    PIN_EXIT = {0: "left", 180: "right", 90: "down", 270: "up"}

    def pin_dir(self, lib_id, pin_number):
        """Exit direction of a pin on an UNROTATED placement, derived from
        the symbol's own pin-angle field rather than guessed per-pin."""
        for (nm, nu, px, py, pang) in self.pin_cache[lib_id]:
            if nu == pin_number:
                return self.PIN_EXIT[int(pang) % 360]
        raise ValueError(f"pin {pin_number} not found for {lib_id}")

    def junction(self, x, y):
        assert_grid_xy(x, y, "junction")
        self.junctions.append(f'\t(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid "{uuid.uuid4()}"))\n')

    # symbol rotation that points the flag's stem/graphic in each direction,
    # determined empirically by rendering all four rotations of each symbol
    # (rottest.png): GND's triangle and +3V3's arrow point opposite ways at
    # the same angle, so each kind needs its own map.
    FLAG_ANGLE = {
        "GND":  {"down": 0, "right": 90, "up": 180, "left": 270},
        "+3V3": {"up": 0, "left": 90, "down": 180, "right": 270},
    }

    def flag(self, kind, pin_xy, ref_prefix, direction, hide_ref=True, text_steps=4):
        """Place a GND/+3V3 power flag DIRECTLY at a pin (no stub -- two
        endpoints at the same coordinates are connected without a drawn
        wire), rotated so the flag is PARALLEL to the pin it connects to:
        `direction` is the direction the pin exits its component, and the
        flag continues straight along it. The value text ("GND"/"+3V3") is
        re-anchored per-direction so it always renders horizontally in the
        pin's own row/column band -- for sideways flags this keeps the text
        within the 2.54mm row pitch instead of running vertically across
        neighboring rows (which is what made rotated flags collide before).
        Reference designator is hidden (standard practice for power flags)."""
        lib_id = f"power:{kind}"
        px, py = pin_xy
        ang = self.FLAG_ANGLE[kind][direction]
        off = text_steps * GRID
        if direction == "down":
            v_at = (px, py + off, (-ang) % 360)
        elif direction == "up":
            v_at = (px, py - off, (-ang) % 360)
        elif direction == "right":
            v_at = (px + off, py, (-ang) % 360)
        else:  # left
            v_at = (px - off, py, (-ang) % 360)
        self._flag_n[kind] += 1
        pfx = "GND" if kind == "GND" else "PWR"
        ref = f"#{ref_prefix}{pfx}{self._flag_n[kind]:03d}"
        self.place(lib_id, ref, kind, px, py, ang, hide_ref=hide_ref,
                   value_at=v_at, ref_at=(px, py, 0))
        return px, py

    def text(self, txt, x, y, angle=0, size=1.5, bold=False):
        """Plain schematic text (section/cluster titles) -- must stay on
        grid like everything else; not electrically meaningful. Anchored
        left/bottom (not KiCad's default center) so the anchor coordinate
        used for bbox/frame-sizing purposes is a real edge of the glyph run,
        not its midpoint -- a centered anchor understates how far long
        titles actually extend and can overflow the auto-drawn sheet frame."""
        assert_grid_xy(x, y, f"text({txt})")
        b = " bold" if bold else ""
        self.texts.append(f'\t(text "{txt}" (at {x} {y} {angle})\n\t\t(effects (font (size {size} {size}){b}) (justify left bottom))\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')

    def render(self, title, uuid_str, sheet_instance_path, sheet_instance_page, paper="A2"):
        lib_syms = "\n".join(self.symbol_defs.values())
        body = "".join(self.instances) + "".join(self.wires) + "".join(self.junctions) + "".join(self.labels) + "".join(self.texts)
        return f'''(kicad_sch
\t(version 20250114)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{uuid_str}")
\t(paper "{paper}")
\t(title_block
\t\t(title "Teacup Universal - {title}")
\t\t(date "2026-07-11")
\t\t(rev "A")
\t\t(company "Teacup Universal")
\t)
\t(lib_symbols
{lib_syms}
\t)
{body}\t(sheet_instances
\t\t(path "{sheet_instance_path}"
\t\t\t(page "{sheet_instance_page}")
\t\t)
\t)
)
'''
