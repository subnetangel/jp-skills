# SPDX-License-Identifier: MIT
"""Native PowerPoint builder for decks made from assets/deck-template.html. Library used by build_pptx.py.

Every element becomes a real PowerPoint object: text boxes with the browser's own line breaks, rounded rectangles,
ovals, freeform connectors, native gradients, SVG icons that carry a PNG fallback rendered at 6x. No slide screenshots.

Animation map (HTML -> PowerPoint), driven by the per-record metadata dom_extract.js reads from the live CSS:
  build 0 of a slide            -> entrances that start with the slide (With Previous), same motion as the HTML
  every later HTML build step   -> one click; all its entrances and exits run together, with the HTML's stagger delays
  .b (rise 16 px) / .stag       -> Float In (fade + rise)            .from-l / .from-r / .swap .now -> Fly In (fade + travel)
  .pop                          -> Zoom (fade + scale from 86 %)
  .draw connectors and arrows   -> Wipe in the drawing direction      count-ups -> final value, then a grow-and-shrink emphasis
  state changes (highlight, done, colour) -> the new look fades in over the old; the old disappears underneath
  .trk .mark (moving marker)    -> motion path, written relative to the shape's own position
  .trk .fill (filling bar)      -> Wipe from left
  ambient: .comet -> Spin (repeat until end of slide); .wire .pt flow dots -> looping motion paths with fade in/out;
           the gate ping -> Grow + fade, twice
  slide transitions             -> Fade
"""
import copy
import json
import os
import re
import base64
import urllib.parse
import urllib.request

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

E = 6350  # EMU per CSS px (13.333 in / 1920 px)
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
P, A = "{%s}" % P_NS, "{%s}" % A_NS
FONTS = {"sans": "Arial", "mono": "Consolas"}   # set by build_pptx.py --font-sans / --font-mono


# ---------------------------------------------------------------- drawing helpers
def emu(px):
    return Emu(int(round(px * E)))


def alpha_el(clr, a):
    if a < 0.995:
        etree.SubElement(clr, A + "alpha").set("val", str(int(round(max(a, 0) * 100000))))


def srgb(parent, hexv, a=1.0):
    c = etree.SubElement(parent, A + "srgbClr"); c.set("val", hexv); alpha_el(c, a); return c


def strip_style(shape):
    st = shape._element.find(qn("p:style"))
    if st is not None:
        shape._element.remove(st)


def set_fill(shape, fill):
    if fill is None:
        shape.fill.background(); return
    shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string(fill["hex"])
    clr = shape._element.spPr.find(f"{A}solidFill/{A}srgbClr")
    if clr is not None:
        alpha_el(clr, fill["a"])


def set_line(shape, stroke):
    if not stroke or stroke["w"] <= 0:
        shape.line.fill.background(); return
    shape.line.color.rgb = RGBColor.from_string(stroke["hex"])
    shape.line.width = emu(stroke["w"])
    ln = shape._element.spPr.find(A + "ln")
    clr = ln.find(f"{A}solidFill/{A}srgbClr")
    if clr is not None:
        alpha_el(clr, stroke["a"])
    dash = stroke.get("dash")
    if dash:
        on, off = (dash + dash)[:2] if isinstance(dash, list) else (6, 7)
        if isinstance(dash, list) and len(dash) == 1:
            on, off = dash[0], dash[0]
        if not isinstance(dash, list):
            on, off = 6, 7
        cd = etree.SubElement(ln, A + "custDash"); ds = etree.SubElement(cd, A + "ds")
        ds.set("d", str(int(round(on / stroke["w"] * 100000)))); ds.set("sp", str(int(round(off / stroke["w"] * 100000))))
    etree.SubElement(ln, A + "round")
    ln.set("cap", "rnd" if stroke.get("cap") == "round" else "flat")


def effect_list(shape):
    sp = shape._element.spPr
    eff = sp.find(A + "effectLst")
    if eff is None:
        eff = etree.SubElement(sp, A + "effectLst")
    return eff


def drop_shadow(shape, sh, w, h):
    """CSS 'x y blur spread color' drop shadow -> outerShdw (spread becomes a scale about the centre)."""
    sx = max(w + 2 * sh["spread"], 1) / max(w, 1); sy = max(h + 2 * sh["spread"], 1) / max(h, 1)
    el = etree.SubElement(effect_list(shape), A + "outerShdw", blurRad=str(int(sh["blur"] * E)), dist=str(int(abs(sh["y"]) * E)),
                          dir="5400000" if sh["y"] >= 0 else "16200000", sx=str(int(sx * 100000)), sy=str(int(sy * 100000)), algn="ctr", rotWithShape="0")
    srgb(el, sh["color"]["hex"], sh["color"]["a"])


def parse_rgba(txt):
    mm = re.match(r"rgba?\(([^)]+)\)", txt.strip())
    v = [float(t) for t in re.split(r"[\s,/]+", mm.group(1).strip()) if t]
    return "%02X%02X%02X" % (int(v[0]), int(v[1]), int(v[2])), (v[3] if len(v) > 3 else 1.0)


def split_top(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [t.strip() for t in out]


def parse_stops(parts):
    stops = []
    for p in parts:
        col = re.match(r"(rgba?\([^)]+\))\s*(.*)", p); hexv, a = parse_rgba(col.group(1))
        poss = re.findall(r"(-?[\d.]+)(%|px)", col.group(2))
        if not poss:
            stops.append((None, hexv, a))
        for v, unit in poss:
            stops.append((float(v) if unit == "%" else 0.0, hexv, a))
    return stops


def parse_gradients(css):
    """CSS gradient list -> records, in CSS order (first is on top)."""
    out = []
    for g in split_top(css):
        mm = re.match(r"(radial|linear)-gradient\((.*)\)\s*$", g, re.S)
        if not mm:
            continue
        kind, parts = mm.group(1), split_top(mm.group(2))
        if kind == "radial":
            head = parts[0]; rx, ry = [float(v) for v in re.findall(r"([\d.]+)px", head)[:2]]
            cx, cy = [float(v) for v in re.findall(r"at\s+(-?[\d.]+)%\s+(-?[\d.]+)%", head)[0]]
            rec = {"kind": "radial", "rx": rx, "ry": ry, "cx": cx / 100, "cy": cy / 100, "stops": parse_stops(parts[1:])}
        else:
            if parts[0].startswith("rgb"):
                ang, stp = 180.0, parts
            elif "deg" in parts[0]:
                ang, stp = float(re.findall(r"(-?[\d.]+)deg", parts[0])[0]), parts[1:]
            else:
                ang = {"to right": 90.0, "to left": 270.0, "to bottom": 180.0, "to top": 0.0}.get(parts[0], 180.0); stp = parts[1:]
            rec = {"kind": "linear", "angle": ang, "stops": parse_stops(stp)}
        st = rec["stops"]
        if st[0][0] is None: st[0] = (0.0,) + st[0][1:]
        if st[-1][0] is None: st[-1] = (100.0,) + st[-1][1:]
        for i in range(1, len(st) - 1):  # evenly spread unpositioned middle stops
            if st[i][0] is None:
                st[i] = ((st[i - 1][0] + 100.0) / 2,) + st[i][1:]
        hue = next((hexv for _, hexv, a in st if a > 0.01), None)
        st[:] = [(pos, hue if (a <= 0.01 and hue) else hexv, a) for pos, hexv, a in st]
        if kind == "radial":  # OOXML 'circle' path reaches 100 % at the bounding-box corners
            st[:] = [(pos * 0.7071, hexv, a) for pos, hexv, a in st]
            if st[-1][0] < 100.0:
                st.append((100.0, st[-1][1], 0.0))
        out.append(rec)
    return out


def grad_fill_xml(stops, path=None, angle_deg=None):
    gf = etree.Element(A + "gradFill"); gf.set("rotWithShape", "1")
    gs = etree.SubElement(gf, A + "gsLst")
    for pos, hexv, a in stops:
        g = etree.SubElement(gs, A + "gs"); g.set("pos", str(int(round(min(max(pos, 0), 100) * 1000)))); srgb(g, hexv, a)
    if path:
        pth = etree.SubElement(gf, A + "path"); pth.set("path", path)
        ftr = etree.SubElement(pth, A + "fillToRect")
        for k in ("l", "t", "r", "b"):
            ftr.set(k, "50000")
    else:
        ooxml = int(round(((angle_deg - 90) % 360) * 60000))  # CSS 90deg (to right) = OOXML 0
        lin = etree.SubElement(gf, A + "lin"); lin.set("ang", str(ooxml)); lin.set("scaled", "0")
    return gf


def apply_grad(shape, gf):
    sp = shape._element.spPr
    for tag in ("noFill", "solidFill", "gradFill", "blipFill", "pattFill"):
        for el in sp.findall(A + tag):
            sp.remove(el)
    geom = sp.find(A + "prstGeom")
    if geom is None:
        geom = sp.find(A + "custGeom")
    geom.addnext(gf)


def bg_gradients(shapes, css, box=(0, 0, 1920, 1080)):
    """Full-box CSS gradients (the slide glow overlay) as native gradient shapes, bottom layer first."""
    x0, y0, bw, bh = box; made = []
    for g in reversed(parse_gradients(css)):
        if g["kind"] == "radial":
            cx, cy = x0 + g["cx"] * bw, y0 + g["cy"] * bh
            shp = shapes.add_shape(MSO_SHAPE.OVAL, emu(cx - g["rx"]), emu(cy - g["ry"]), emu(2 * g["rx"]), emu(2 * g["ry"]))
            strip_style(shp); shp.line.fill.background(); apply_grad(shp, grad_fill_xml(g["stops"], path="circle"))
            shp.name = "background tint (radial gradient)"
        else:
            shp = shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(x0), emu(y0), emu(bw), emu(bh))
            strip_style(shp); shp.line.fill.background(); apply_grad(shp, grad_fill_xml(g["stops"], angle_deg=g["angle"]))
            shp.name = "background (linear gradient)"
        made.append(shp)
    return made


def glow_oval(shapes, x, y, w, h, sh):
    """CSS '0 0 blur spread color' glow -> soft radial-gradient oval behind the element."""
    r_in = max(w, h) / 2 + sh["spread"]; R = r_in + sh["blur"]
    cx, cy = x + w / 2, y + h / 2
    shp = shapes.add_shape(MSO_SHAPE.OVAL, emu(cx - R), emu(cy - R), emu(2 * R), emu(2 * R))
    strip_style(shp); shp.line.fill.background()
    c, a = sh["color"]["hex"], sh["color"]["a"]
    k = r_in / R * 70.71
    apply_grad(shp, grad_fill_xml([(0, c, a), (k * 0.75, c, a), (k + (70.71 - k) * 0.45, c, a * 0.25), (70.71, c, 0), (100, c, 0)], path="circle"))
    shp.name = "glow (box-shadow)"
    return shp


def halo_ring(shapes, s, sh):
    """CSS '0 0 0 spread color' ring -> outline-only shape spread/2 outside the box, line width = spread."""
    sp = sh["spread"]; x, y, w, h = s["x"] - sp / 2, s["y"] - sp / 2, s["w"] + sp, s["h"] + sp
    if s["kind"] == "ellipse":
        shp = shapes.add_shape(MSO_SHAPE.OVAL, emu(x), emu(y), emu(w), emu(h))
    else:
        shp = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, emu(x), emu(y), emu(w), emu(h))
        shp.adjustments[0] = min(0.5, (s.get("rx", 0) + sp / 2) / max(min(w, h), 0.01))
    strip_style(shp); shp.fill.background()
    set_line(shp, {"hex": sh["color"]["hex"], "a": sh["color"]["a"], "w": sp})
    shp.name = "halo ring (box-shadow spread)"
    return shp


def add_box(shapes, s):
    """rect / ellipse / polyline record -> [glow, halo, ..., main] autoshapes in paint order."""
    if s["kind"] == "polyline":
        pts = s["points"]
        fb = shapes.build_freeform(emu(pts[0][0]), emu(pts[0][1]), scale=1.0)
        fb.add_line_segments([(emu(x), emu(y)) for x, y in pts[1:]], close=False)
        shp = fb.convert_to_shape()
        strip_style(shp); shp.fill.background(); set_line(shp, s.get("stroke")); shp.name = "line " + s.get("tag", "")
        return [shp]
    x, y, w, h = s["x"], s["y"], s["w"], s["h"]
    out = []
    shadows = s.get("shadows") or []
    for sh in reversed(shadows):  # CSS: first shadow on top
        if sh["inset"]:
            continue
        if sh["x"] == 0 and sh["y"] == 0 and sh["blur"] > 0:
            out.append(glow_oval(shapes, x, y, w, h, sh))
        elif sh["x"] == 0 and sh["y"] == 0 and sh["blur"] == 0 and sh["spread"] > 0:
            out.append(halo_ring(shapes, s, sh))
    if s["kind"] == "ellipse":
        shp = shapes.add_shape(MSO_SHAPE.OVAL, emu(x), emu(y), emu(w), emu(h))
    elif s.get("rx", 0) > 0.5:
        shp = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, emu(x), emu(y), emu(w), emu(h))
        shp.adjustments[0] = min(0.5, s["rx"] / max(min(w, h), 0.01))
    else:
        shp = shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(x), emu(y), emu(w), emu(h))
    strip_style(shp)
    set_fill(shp, s.get("fill"))
    stroke = s.get("stroke")
    inset = next((sh for sh in shadows if sh["inset"] and sh["spread"] > 0 and sh["blur"] == 0), None)
    if not stroke and inset:  # an inset 0 0 0 1px ring -> a hairline outline
        stroke = {"hex": inset["color"]["hex"], "a": inset["color"]["a"], "w": inset["spread"]}
    set_line(shp, stroke)
    if s.get("grad"):
        gl = parse_gradients(s["grad"])
        if gl and gl[0]["kind"] == "linear":
            stops = gl[0]["stops"]
            if s.get("fill"):  # gradient over a solid colour: keep both by stacking a solid shape underneath
                base = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if s.get("rx", 0) > 0.5 else MSO_SHAPE.RECTANGLE, emu(x), emu(y), emu(w), emu(h))
                strip_style(base); set_fill(base, s["fill"]); base.line.fill.background(); out.append(base)
            apply_grad(shp, grad_fill_xml(stops, angle_deg=gl[0]["angle"]))
    for sh in shadows:
        if not sh["inset"] and (sh["y"] != 0 or sh["x"] != 0):
            drop_shadow(shp, sh, w, h); break
    if s.get("rot"):
        shp.rotation = s["rot"] % 360
    shp.name = s["kind"] + " " + s.get("tag", "")
    out.append(shp)
    return out


def typeface(family, weight):
    """CSS font stack -> one PowerPoint typeface. Mono stacks map to FONTS['mono'], everything else to FONTS['sans']."""
    fam = family.lower()
    first = fam.split(",")[0].strip().strip("\"'")
    mono = "mono" in first or first in ("menlo", "consolas", "monaco", "courier", "courier new")
    return (FONTS["mono"] if mono else FONTS["sans"]), weight >= 600


def add_text_block(shapes, blk):
    """One text box per HTML text element; line breaks are the browser's, so the box gets extra width instead of re-wrapping:
    left-aligned boxes grow to the right, centred ones on both sides, right-aligned ones to the left."""
    pad = max(12.0, blk["w"] * 0.08)
    x, w = blk["x"], blk["w"]
    if blk["align"] == "l":
        x, w = x - 1, w + pad
    elif blk["align"] == "c":
        x, w = x - pad / 2, w + pad
    else:
        x, w = x - pad, w + pad + 1
    tb = shapes.add_textbox(emu(x), emu(blk["y"]), emu(w), emu(blk["h"] + 2))
    tb.name = "text " + blk.get("tag", "")
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, 0)
    para = tf.paragraphs[0]
    para.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[blk["align"]]
    para.line_spacing = Pt(blk["lineHeight"] * 0.5)
    for r in blk["runs"]:
        for li, line in enumerate(r["text"].split("\n")):
            if li > 0:
                para.add_line_break()
            if not line:
                continue
            run = para.add_run(); run.text = line
            f = run.font
            face, bold = typeface(r["family"], r["weight"])
            f.name = face; f.size = Pt(max(r["size"] * 0.5, 4)); f.bold = bold; f.italic = bool(r["italic"])
            f.color.rgb = RGBColor.from_string(r["color"])
            rPr = run._r.get_or_add_rPr()
            clr = rPr.find(f".//{A}srgbClr")
            if clr is not None:
                alpha_el(clr, r.get("alpha", 1))
            if r.get("spacing"):
                rPr.set("spc", str(int(round(r["spacing"] * 0.5 * 100))))
            if r.get("strike"):
                rPr.set("strike", "sngStrike")
    return [tb]


class IconCache:
    """One SVG media part per icon per presentation; pictures carry PNG + svgBlip."""

    def __init__(self, prs, folder):
        self.prs = prs; self.parts = {}; self.folder = folder

    def part(self, icon_id):
        if icon_id not in self.parts:
            blob = open(f"{self.folder}/icons/{icon_id}.svg", "rb").read()
            self.parts[icon_id] = Part(PackURI(f"/ppt/media/{icon_id}.svg"), "image/svg+xml", self.prs.part.package, blob)
        return self.parts[icon_id]

    def add(self, slide, shapes, ic):
        pic = shapes.add_picture(f"{self.folder}/icons/{ic['id']}.png", emu(ic["x"]), emu(ic["y"]), emu(ic["w"]), emu(ic["h"]))
        pic.name = "icon " + ic["id"] + " (SVG + PNG fallback)"
        rid = slide.part.relate_to(self.part(ic["id"]), RT.IMAGE)
        blip = pic._element.find(f".//{A}blip")
        if ic.get("opacity", 1) < 0.995:
            etree.SubElement(blip, A + "alphaModFix").set("amt", str(int(ic["opacity"] * 100000)))
        ext = etree.SubElement(etree.SubElement(blip, A + "extLst"), A + "ext"); ext.set("uri", "{96DAC541-7B7A-43D3-8B79-37D633B846F1}")
        sb = etree.SubElement(ext, "{%s}svgBlip" % SVG_NS); sb.set("{%s}embed" % R_NS, rid)
        return [pic]




def image_bytes(src):
    """<img> src (data: URI or file://) -> bytes. Remote URLs are refused: the deck must be self-contained."""
    if src.startswith("data:"):
        head, data = src.split(",", 1)
        return base64.b64decode(data) if ";base64" in head else urllib.parse.unquote_to_bytes(data)
    if src.startswith("file://"):
        with urllib.request.urlopen(src) as fh:
            return fh.read()
    raise ValueError(f"image source must be inlined or local, got {src[:60]}")


def add_image(shapes, im):
    import io
    pic = shapes.add_picture(io.BytesIO(image_bytes(im["src"])), emu(im["x"]), emu(im["y"]), emu(im["w"]), emu(im["h"]))
    pic.name = "picture"
    if im.get("opacity", 1) < 0.995:
        blip = pic._element.find(f".//{A}blip"); etree.SubElement(blip, A + "alphaModFix").set("amt", str(int(im["opacity"] * 100000)))
    return [pic]


def comet_shape(shapes, rec, spin):
    """The comet rides a ring: one shape the size of the ring whose custom geometry is only the comet dot, so a Spin
    emphasis turns it about the ring centre. Its glow is a native glow effect that follows the dot."""
    shp = shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(spin["x"]), emu(spin["y"]), emu(spin["w"]), emu(spin["h"]))
    strip_style(shp)
    sp = shp._element.spPr; prst = sp.find(A + "prstGeom")
    W, H = int(spin["w"] * 100), int(spin["h"] * 100)
    cx, cy, r = (rec["x"] - spin["x"] + rec["w"] / 2) * 100, (rec["y"] - spin["y"] + rec["h"] / 2) * 100, rec["w"] / 2 * 100
    cg = etree.Element(A + "custGeom")
    for t in ("avLst", "gdLst", "ahLst", "cxnLst"):
        etree.SubElement(cg, A + t)
    etree.SubElement(cg, A + "rect", l="0", t="0", r="r", b="b")
    pl = etree.SubElement(cg, A + "pathLst"); pth = etree.SubElement(pl, A + "path", w=str(W), h=str(H))
    etree.SubElement(etree.SubElement(pth, A + "moveTo"), A + "pt", x=str(int(cx + r)), y=str(int(cy)))
    etree.SubElement(pth, A + "arcTo", wR=str(int(r)), hR=str(int(r)), stAng="0", swAng="21600000")
    etree.SubElement(pth, A + "close")
    prst.addprevious(cg); sp.remove(prst)
    set_fill(shp, rec["fill"]); shp.line.fill.background()
    gsh = next((x for x in rec.get("shadows", []) if x["blur"] > 0), None)
    if gsh:
        g = etree.SubElement(effect_list(shp), A + "glow", rad=str(int((gsh["blur"] * 0.6 + gsh["spread"]) * E)))
        srgb(g, gsh["color"]["hex"], gsh["color"]["a"])
    shp.name = "comet (custom geometry, spins about the ring centre)"
    return [shp]


# ---------------------------------------------------------------- element model
def key(cat, e):
    z = round(e.get("z", 0), 3)
    if cat == "text":
        return ("text", z, round(e["x"]), round(e["y"]), round(e["w"]), e["align"], tuple((r["text"], r["color"], round(r["alpha"], 2), round(r["size"]), r.get("strike", False)) for r in e["runs"]))
    if cat == "icon":
        return ("icon", z, e["id"], round(e.get("opacity", 1), 2))
    if cat == "image":
        return ("image", z, e["src"], round(e["x"]), round(e["y"]))
    if e["kind"] == "polyline":
        return ("poly", z, tuple((round(x), round(y)) for x, y in e["points"]), json.dumps(e.get("stroke"), sort_keys=True))
    return (e["kind"], z, round(e["x"]), round(e["y"]), round(e["w"]), round(e["h"]), round(e.get("rx", 0)), json.dumps(e.get("fill"), sort_keys=True),
            json.dumps(e.get("stroke"), sort_keys=True), json.dumps(e.get("shadows"), sort_keys=True), e.get("grad"))


def elements(folder, sid):
    d = json.load(open(f"{folder}/{sid}.json")); out = []
    for s in d["shapes"] + d["svgShapes"]: out.append(("shape", key("shape", s), s))
    for im in d["images"]: out.append(("image", key("image", im), im))
    for ic in d["icons"]: out.append(("icon", key("icon", ic), ic))
    for b in d["blocks"]: out.append(("text", key("text", b), b))
    return d, out


def emit(slide, shapes, cat, rec, icons):
    if cat == "shape": return add_box(shapes, rec)
    if cat == "image": return add_image(shapes, rec)
    if cat == "icon": return icons.add(slide, shapes, rec)
    return add_text_block(shapes, rec)


def faded_copy(cat, rec, k):
    r = copy.deepcopy(rec)
    if cat == "text":
        for run in r["runs"]:
            run["alpha"] = run.get("alpha", 1) * k
    else:
        for f in ("fill", "stroke"):
            if r.get(f):
                r[f]["a"] *= k
    return r


def slide_background(slide, d):
    bg = d["slideBg"]
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = RGBColor.from_string(bg["color"]["hex"])
    if bg.get("gradient"):
        bg_gradients(slide.shapes, bg["gradient"])
    if d.get("overlay"):
        bg_gradients(slide.shapes, d["overlay"])


# ---------------------------------------------------------------- timing XML
class Timing:
    """Builds <p:timing> the way PowerPoint writes it: a main sequence of click groups (plus an optional group that
    starts with the slide), every later-entering shape hidden at t=0 and listed in <p:bldLst> when it is a p:sp."""

    def __init__(self, slide):
        self.slide = slide; self.nid = 0; self.grp = {}; self.groups = []; self.hidden = []; self.animated = []

    def cid(self):
        self.nid += 1; return str(self.nid)

    def grp_id(self, spid):
        self.grp[spid] = self.grp.get(spid, -1) + 1; return str(self.grp[spid])

    # behaviours ---------------------------------------------------------
    def _bhvr(self, parent, spid, dur, attrs=(), delay=None, **ctn):
        bh = etree.SubElement(parent, P + "cBhvr", **({"additive": ctn.pop("additive")} if "additive" in ctn else {}))
        c = etree.SubElement(bh, P + "cTn", id=self.cid(), dur=str(dur), fill="hold", **ctn)
        if delay:
            etree.SubElement(etree.SubElement(c, P + "stCondLst"), P + "cond", delay=str(delay))
        etree.SubElement(etree.SubElement(bh, P + "tgtEl"), P + "spTgt", spid=str(spid))
        if attrs:
            al = etree.SubElement(bh, P + "attrNameLst")
            for a in attrs:
                etree.SubElement(al, P + "attrName").text = a
        return bh

    def set_vis(self, parent, spid, value, delay=0):
        s = etree.SubElement(parent, P + "set"); self._bhvr(s, spid, 1, ("style.visibility",), delay=delay)
        etree.SubElement(etree.SubElement(s, P + "to"), P + "strVal", val=value)

    def fade(self, parent, spid, direction, dur, delay=0, **ctn):
        ae = etree.SubElement(parent, P + "animEffect", transition=direction, filter="fade"); self._bhvr(ae, spid, dur, delay=delay, **ctn)

    def wipe(self, parent, spid, edge, dur, delay=0):
        ae = etree.SubElement(parent, P + "animEffect", transition="in", filter=f"wipe({edge})"); self._bhvr(ae, spid, dur, delay=delay)

    def prop(self, parent, spid, attr, frm, to, dur, decel=100000):
        an = etree.SubElement(parent, P + "anim", calcmode="lin", valueType="num")
        self._bhvr(an, spid, dur, (attr,), decel=str(decel)) if decel else self._bhvr(an, spid, dur, (attr,))
        tl = etree.SubElement(an, P + "tavLst")
        for tm, v in (("0", frm), ("100000", to)):
            etree.SubElement(etree.SubElement(etree.SubElement(tl, P + "tav", tm=tm), P + "val"), P + "strVal", val=v)

    def motion(self, parent, spid, path, dur, delay=0, accel=None, decel=None):
        am = etree.SubElement(parent, P + "animMotion", origin="layout", path=path, pathEditMode="relative", rAng="0", ptsTypes="")
        kw = {}
        if accel: kw["accel"] = str(accel)
        if decel: kw["decel"] = str(decel)
        self._bhvr(am, spid, dur, ("ppt_x", "ppt_y"), delay=delay, **kw)

    def scale(self, parent, spid, by, dur, delay=0, **ctn):
        an = etree.SubElement(parent, P + "animScale"); self._bhvr(an, spid, dur, delay=delay, **ctn)
        etree.SubElement(an, P + "by", x=str(int(by * 100000)), y=str(int(by * 100000)))

    def rot(self, parent, spid, dur):
        an = etree.SubElement(parent, P + "animRot", by="21600000"); self._bhvr(an, spid, dur, ("r",))

    # effects --------------------------------------------------------------
    def effect(self, group, spid, cls, preset, subtype, delay, build, dur=None, repeat=None):
        """Append one effect container to a group; `build(children)` writes its behaviours."""
        attrs = dict(id=self.cid(), presetID=str(preset), presetClass=cls, presetSubtype=str(subtype), fill="hold", grpId=self.grp_id(spid), nodeType="withEffect")
        if repeat:
            attrs["repeatCount"] = repeat
        if dur:
            attrs["dur"] = str(dur)
        group.append((attrs, delay, build, spid, cls))
        if cls == "entr":
            self.animated.append(spid)

    def new_group(self, auto=False):
        g = []; self.groups.append((auto, g)); return g

    def entrance(self, group, spid, m, delay=0):
        """m: {kind, dx, dy, scale, dur, fade, edge}"""
        kind = m["kind"]; dur = m.get("dur", 500); fd = m.get("fade", dur)
        if kind == "wipe":
            sub = {"left": 8, "right": 2, "up": 1, "down": 4}[m["edge"]]
            self.effect(group, spid, "entr", 22, sub, delay, lambda ch: (self.set_vis(ch, spid, "visible"), self.wipe(ch, spid, m["edge"], dur)))
            return
        if kind == "fade":
            self.effect(group, spid, "entr", 10, 0, delay, lambda ch: (self.set_vis(ch, spid, "visible"), self.fade(ch, spid, "in", fd)))
            return
        dx, dy, sc = m.get("dx", 0), m.get("dy", 0), m.get("scale", 1)

        def b(ch):
            self.set_vis(ch, spid, "visible"); self.fade(ch, spid, "in", fd)
            if sc != 1:
                self.prop(ch, spid, "ppt_w", f"#ppt_w*{sc}", "#ppt_w", dur); self.prop(ch, spid, "ppt_h", f"#ppt_h*{sc}", "#ppt_h", dur)
            if dx:
                self.prop(ch, spid, "ppt_x", f"#ppt_x{dx / 1920:+.5f}", "#ppt_x", dur)
            if dy:
                self.prop(ch, spid, "ppt_y", f"#ppt_y{dy / 1080:+.5f}", "#ppt_y", dur)
        if kind == "zoom":
            preset, sub = 53, 16
        elif kind == "float":
            preset, sub = 42, 0
        else:
            preset, sub = 2, (8 if dx < 0 else 2 if dx > 0 else 4 if dy > 0 else 1)
        self.effect(group, spid, "entr", preset, sub, delay, b)

    def exit(self, group, spid, kind, dur, delay=0):
        if kind == "fade":
            self.effect(group, spid, "exit", 10, 0, delay, lambda ch: (self.fade(ch, spid, "out", dur), self.set_vis(ch, spid, "hidden", delay=dur)))
        else:
            self.effect(group, spid, "exit", 1, 0, delay, lambda ch: self.set_vis(ch, spid, "hidden"))

    # write -----------------------------------------------------------------
    def write(self):
        if not any(g for _, g in self.groups):
            return
        timing = etree.Element(P + "timing"); tnLst = etree.SubElement(timing, P + "tnLst")
        root = etree.SubElement(etree.SubElement(tnLst, P + "par"), P + "cTn", id=self.cid(), dur="indefinite", restart="never", nodeType="tmRoot")
        rch = etree.SubElement(root, P + "childTnLst")
        hidden = list(dict.fromkeys(self.animated))
        if hidden:
            pre = etree.SubElement(etree.SubElement(rch, P + "par"), P + "cTn", id=self.cid(), fill="hold")
            etree.SubElement(etree.SubElement(pre, P + "stCondLst"), P + "cond", delay="0")
            pch = etree.SubElement(pre, P + "childTnLst")
            for spid in hidden:
                self.set_vis(pch, spid, "hidden")
        seq = etree.SubElement(rch, P + "seq", concurrent="1", nextAc="seek")
        main_id = self.cid()
        main = etree.SubElement(seq, P + "cTn", id=main_id, dur="indefinite", nodeType="mainSeq")
        mc = etree.SubElement(main, P + "childTnLst")
        for auto, effects in self.groups:
            if not effects:
                continue
            click = etree.SubElement(etree.SubElement(mc, P + "par"), P + "cTn", id=self.cid(), fill="hold")
            sc = etree.SubElement(click, P + "stCondLst"); etree.SubElement(sc, P + "cond", delay="indefinite")
            if auto:
                c = etree.SubElement(sc, P + "cond", evt="onBegin", delay="0"); etree.SubElement(c, P + "tn", val=main_id)
            grp = etree.SubElement(etree.SubElement(etree.SubElement(click, P + "childTnLst"), P + "par"), P + "cTn", id=self.cid(), fill="hold")
            etree.SubElement(etree.SubElement(grp, P + "stCondLst"), P + "cond", delay="0")
            gch = etree.SubElement(grp, P + "childTnLst")
            for i, (attrs, delay, build, spid, cls) in enumerate(effects):
                if i == 0 and not auto:
                    attrs["nodeType"] = "clickEffect"
                ctn = etree.SubElement(etree.SubElement(gch, P + "par"), P + "cTn", **attrs)
                etree.SubElement(etree.SubElement(ctn, P + "stCondLst"), P + "cond", delay=str(int(delay)))
                build(etree.SubElement(ctn, P + "childTnLst"))
        for lst, evt in (("prevCondLst", "onPrev"), ("nextCondLst", "onNext")):
            c = etree.SubElement(etree.SubElement(seq, P + lst), P + "cond", evt=evt, delay="0"); etree.SubElement(etree.SubElement(c, P + "tgtEl"), P + "sldTgt")
        sp_ids = {int(e.get("id")) for e in self.slide._element.iter(P + "cNvPr") if e.getparent().getparent().tag == P + "sp"}
        bld = etree.SubElement(timing, P + "bldLst")
        seen = set()
        for _, effects in self.groups:
            for _, _, _, spid, _ in effects:
                if spid not in seen and spid in sp_ids:
                    seen.add(spid); etree.SubElement(bld, P + "bldP", spid=str(spid), grpId="0", animBg="1")
        if not len(bld):
            timing.remove(bld)
        sld = self.slide._element
        anchor = sld.find(P + "transition")
        if anchor is None:
            anchor = sld.find(P + "clrMapOvr")
        anchor.addnext(timing)


def add_transition(slide):
    """HTML: 450 ms cross-fade with a 40 px drift. PowerPoint: Fade, fast (0.5 s)."""
    trans = etree.Element(P + "transition"); trans.set("spd", "fast"); etree.SubElement(trans, P + "fade")
    sld = slide._element; anchor = sld.find(P + "clrMapOvr")
    if anchor is None:
        anchor = sld.find(P + "cSld")
    anchor.addnext(trans)


def wipe_edge(rec):
    pts = rec["points"]; dx, dy = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]
    if abs(dx) >= abs(dy):
        return "left" if dx >= 0 else "right"
    return "up" if dy >= 0 else "down"  # PowerPoint: wipe(up) = From Top, wipe(down) = From Bottom


def entry_motion(rec):
    m = dict(rec["meta"])
    if m["kind"] == "wipe":
        m["edge"] = wipe_edge(rec) if rec.get("kind") == "polyline" else "left"
        if m.get("sub", 0) > 0:  # an arrowhead finishes the stroke it sits on
            m["dur"] = 200; m["delay"] = m.get("delay", 0) + 800
    return m


# ---------------------------------------------------------------- one slide
def hex_of(css_color, default="5B63E8"):
    m = re.match(r"#([0-9a-fA-F]{6})", (css_color or "").strip())
    return m.group(1).upper() if m else default


def build_slide(prs, icons, folder, n, states, note_text, report):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    per_state = [elements(folder, st[1]) for st in states]
    d0 = per_state[0][0]
    slide_background(slide, d0)
    nS = len(states)
    tm = Timing(slide)
    groups = [tm.new_group(auto=True)] + [tm.new_group() for _ in range(1, nS)]
    # lifetimes (one per contiguous run of states); movers and the comet are handled apart
    life, order, open_run, movers, comet = {}, [], {}, {}, None
    for i, (_, els) in enumerate(per_state):
        present = set()
        for cat, k, rec in els:
            mt = rec.get("meta", {})
            if mt.get("mover"):
                movers.setdefault((mt["mover"], rec.get("tag"), round(rec["z"], 3), cat), [None] * nS)[i] = rec; continue
            if mt.get("spin"):
                comet = rec; continue
            present.add(k)
        for k in list(open_run):
            if k not in present:
                del open_run[k]
        for cat, k, rec in els:
            if k not in present:
                continue
            if k in open_run:
                life[(k, open_run[k])][1] = i
            else:
                open_run[k] = i; life[(k, i)] = [i, i, cat, rec]; order.append((k, i))
    items = [("life", lid, life[lid][3]["z"], life[lid][0]) for lid in order]
    items += [("mover", mk, recs[next(i for i, r in enumerate(recs) if r)]["z"], 0) for mk, recs in movers.items()]
    if comet:
        items.append(("comet", None, comet["z"], 0))
    particles = per_state[-1][0].get("particles", [])
    items += [("particle", p, p["z"], 0) for p in particles]
    items.sort(key=lambda t: (t[2], t[3]))   # browser paint order, so no shape ghosts above the one that covers it
    brand = hex_of(d0.get("brand"))

    spids = {}
    for kind, ref, z, _ in items:
        if kind == "life":
            first, last, cat, rec = life[ref]
            shs = emit(slide, slide.shapes, cat, rec, icons)
            if (first, last) != (0, nS - 1):
                for s in shs:
                    s.name = f"[state {first}-{last}] " + s.name
            spids[ref] = [s.shape_id for s in shs]
            if cat == "shape" and rec.get("meta", {}).get("ping"):
                ring = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rec["kind"] == "rect" else MSO_SHAPE.OVAL, emu(rec["x"]), emu(rec["y"]), emu(rec["w"]), emu(rec["h"]))
                strip_style(ring); ring.fill.background(); set_line(ring, {"hex": brand, "a": 0.55, "w": 3})
                if rec["kind"] == "rect":
                    ring.adjustments[0] = min(0.5, rec.get("rx", 0) / max(rec["w"], 1))
                ring.name = "gate ping ring"; spids[("ping", ref)] = [ring.shape_id]
        elif kind == "mover":
            recs = movers[ref]; r0 = next(r for r in recs if r)
            spids[("mover", ref)] = [s.shape_id for s in emit(slide, slide.shapes, ref[3], r0, icons)]
        elif kind == "comet":
            spids["comet"] = [s.shape_id for s in comet_shape(slide.shapes, comet, d0["spin"])]
        else:
            p = ref; w = p["w"]; x0, y0 = p["x0"], p["y0"]
            col = {"hex": p["color"], "a": 1.0}
            g = glow_oval(slide.shapes, x0 - w / 2, y0 - w / 2, w, w, {"spread": 2, "blur": 12, "color": col})
            dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, emu(x0 - w / 2), emu(y0 - w / 2), emu(w), emu(w))
            strip_style(dot); set_fill(dot, col); dot.line.fill.background(); dot.name = "flow particle"
            spids[("particle", id(p))] = [g.shape_id, dot.shape_id]

    stats = {"clicks": nS - 1, "auto": 0, "enter": 0, "exit": 0, "motion": 0, "loops": 0}
    for lid in order:
        first, last, cat, rec = life[lid]; mt = rec.get("meta", {})
        ids = spids[lid]
        # build 0 enters with the slide; later builds on their click; everything else is static
        enter_at = first if first > 0 else (0 if mt.get("build") == 0 else None)
        if enter_at is not None:
            g = groups[enter_at]
            if mt.get("grow"):
                m = {"kind": "wipe", "edge": "left", "dur": mt["dur"]}; delay = 0
            elif mt.get("build") == enter_at:
                m = entry_motion(rec); delay = m.get("delay", 0)
            else:   # a state change (highlight, done, current panel): cross-fade
                m = {"kind": "fade", "dur": 300, "fade": 300}; delay = mt.get("delay", 0)
            for sid in ids:
                tm.entrance(g, sid, m, delay)
            stats["enter" if enter_at else "auto"] += 1
            if mt.get("count"):  # count-up: the final value lands, then a grow-and-shrink emphasis
                for sid in ids:
                    tm.effect(g, sid, "emph", 26, 0, delay + m.get("dur", 500), lambda ch, sid=sid: tm.scale(ch, sid, 1.12, 220, autoRev="1"))
            if mt.get("ping") and ("ping", lid) in spids:
                rid = spids[("ping", lid)][0]
                grow = (rec["w"] + 44) / rec["w"]

                def pb(ch, rid=rid, grow=grow, pd=mt["ping"]["dur"]):
                    tm.set_vis(ch, rid, "visible"); tm.scale(ch, rid, grow, pd); tm.fade(ch, rid, "out", pd)
                tm.effect(g, rid, "emph", 6, 0, delay, pb, dur=mt["ping"]["dur"], repeat=str(mt["ping"]["count"] * 1000))
                tm.animated.append(rid)
        if last < nS - 1:
            g = groups[last + 1]
            succ = next((l2 for l2 in order if life[l2][0] == last + 1 and life[l2][2] == cat and abs(life[l2][3]["z"] - rec["z"]) < 1e-6), None)
            for sid in ids:
                if succ is not None:  # the new look fades in on top; the old one disappears underneath once covered
                    sm = life[succ][3].get("meta", {})
                    tm.exit(g, sid, "disappear", 0, delay=(sm["dur"] if sm.get("grow") else 300) + sm.get("delay", 0))
                else:
                    tm.exit(g, sid, "fade", 300, delay=mt.get("delay", 0))
            stats["exit"] += 1
    # movers travel along motion paths written relative to the shape's layout position, one leg per click
    for mk, recs in movers.items():
        r0 = next(r for r in recs if r); cx0, cy0 = r0["x"], r0["y"]; prev = (0.0, 0.0)
        for i in range(1, nS):
            r = recs[i]
            if not r:
                continue
            off = ((r["x"] - cx0) / 1920, (r["y"] - cy0) / 1080)
            if abs(off[0] - prev[0]) > 1e-5 or abs(off[1] - prev[1]) > 1e-5:
                path = f"M {prev[0]:.5f} {prev[1]:.5f} L {off[0]:.5f} {off[1]:.5f} E"
                for sid in spids[("mover", mk)]:
                    tm.effect(groups[i], sid, "path", 0, 0, 0, lambda ch, sid=sid, path=path: tm.motion(ch, sid, path, 600, accel=40000, decel=60000))
                stats["motion"] += 1
                prev = off
    if comet:   # ambient comet: Spin, one lap per animation period, until the end of the slide
        sid = spids["comet"][0]
        tm.effect(groups[0], sid, "emph", 8, 0, 0, lambda ch: tm.rot(ch, sid, comet["meta"]["spin"]["dur"]), dur=comet["meta"]["spin"]["dur"], repeat="indefinite")
        stats["loops"] += 1
    for p in particles:   # flow dots: looping motion paths that start with their wire's build
        path = f"M 0 0 L {p['run'] / 1920:.5f} 0 E"
        g = groups[min(p["build"], nS - 1)]; D = p["dur"]
        for sid in spids[("particle", id(p))]:
            def pb(ch, sid=sid, D=D, path=path):
                tm.set_vis(ch, sid, "visible"); tm.fade(ch, sid, "in", int(D * 0.12)); tm.motion(ch, sid, path, D)
                tm.fade(ch, sid, "out", int(D * 0.12), delay=int(D * 0.88))
            tm.effect(g, sid, "path", 0, 0, p["delay"] + (450 if p["build"] == 0 else 0), pb, dur=D, repeat="indefinite")
            tm.animated.append(sid)  # hidden until its wire builds
        stats["loops"] += 1
    if n > 1:
        add_transition(slide)
    tm.write()
    if note_text is not None:
        slide.notes_slide.notes_text_frame.text = note_text
    report[n] = stats
    return slide


def build(folder, states, notes, out_path, title):
    """folder: extraction output for one theme. notes: list of per-slide strings, or None for a share file."""
    prs = Presentation(); prs.slide_width = emu(1920); prs.slide_height = emu(1080)
    icons = IconCache(prs, folder); report = {}
    slides = sorted({s[0] for s in states})
    for n in slides:
        build_slide(prs, icons, folder, n, [s for s in states if s[0] == n], notes[n - 1] if notes else None, report)
    prs.save(out_path)
    neutral_metadata(out_path, title)
    return report


def neutral_metadata(path, title):
    """Rewrite docProps to neutral values and drop the template thumbnail, so no author, company or tool user leaks."""
    import datetime
    import shutil
    import tempfile
    import zipfile
    from xml.sax.saxutils import escape
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{escape(title)}</dc:title><dc:creator>presentation-coach</dc:creator>'
            '<cp:lastModifiedBy>presentation-coach</cp:lastModifiedBy><cp:revision>1</cp:revision>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx"); tmp.close()
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "docProps/thumbnail.jpeg" or item.filename.startswith("ppt/printerSettings/"):
                continue   # template thumbnail and print settings from the python-pptx default file
            data = zin.read(item.filename)
            if item.filename == "docProps/core.xml":
                data = core.encode("utf-8")
            elif item.filename == "docProps/app.xml":
                t = data.decode("utf-8")
                t = re.sub(r"<Application>.*?</Application>", "<Application>presentation-coach</Application>", t)
                t = re.sub(r"<(Company|Manager)>.*?</\1>", "", t)
                data = t.encode("utf-8")
            elif item.filename == "_rels/.rels":
                data = re.sub(rb'<Relationship [^>]*Target="docProps/thumbnail.jpeg"[^>]*/>', b"", data)
            elif item.filename == "[Content_Types].xml":
                data = re.sub(rb'<Override [^>]*PartName="/docProps/thumbnail.jpeg"[^>]*/>', b"", data)
                data = re.sub(rb'<Override [^>]*PartName="/ppt/printerSettings/[^"]*"[^>]*/>', b"", data)
            elif item.filename == "ppt/_rels/presentation.xml.rels":
                data = re.sub(rb'<Relationship [^>]*Target="printerSettings/[^"]*"[^>]*/>', b"", data)
            zout.writestr(item, data)
    shutil.move(tmp.name, path)
