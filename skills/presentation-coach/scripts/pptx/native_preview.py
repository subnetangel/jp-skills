#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render a built PPTX the way PowerPoint should draw it, one image per click state, with no browser involved.

Reads the PPTX itself: shapes in file (z) order, solid and gradient fills with alpha, outlines and dashes, glows and drop
shadows (approximate), custom geometry, text runs in the file's typefaces (resolved to local font files with fc-match),
pictures with alphaModFix. It plays the slide's timing tree: the hidden-at-start set, the With-Previous group, then each
click (entrances show, exits hide, motion paths move), so image k is what PowerPoint shows after k clicks.
It checks the file's structure and layout; it is not PowerPoint's own renderer.

Usage: native_preview.py DECK.pptx OUT_DIR [--stills DIR]
  writes OUT_DIR/sN-bK.png; with --stills (the extractor's reference stills, named sN-bK.png) it also writes
  side-by-side sheets OUT_DIR/pair-sN-bK.png (HTML left, PPTX right) and prints the mean pixel difference per state.
"""
import argparse
import functools
import io
import os
import re
import shutil
import subprocess
import zipfile

import numpy as np
from lxml import etree
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
P, A, R = "{%s}" % NS["p"], "{%s}" % NS["a"], "{%s}" % NS["r"]
E = 6350
W, H = 1920, 1080


@functools.lru_cache(maxsize=None)
def font_file(name, bold):
    """Typeface name -> a local font file via fontconfig; DejaVu Sans as the last resort."""
    if shutil.which("fc-match"):
        q = f"{name}:bold" if bold else name
        out = subprocess.run(["fc-match", "-f", "%{file}", q], capture_output=True, text=True).stdout.strip()
        if out and os.path.exists(out):
            return out
    return "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"


@functools.lru_cache(maxsize=None)
def font(name, px, bold=False):
    try:
        return ImageFont.truetype(font_file(name, bold), px)
    except OSError:
        return ImageFont.load_default(size=px)


def color(el):
    """first srgbClr under el -> (r,g,b,a 0..1)"""
    c = el.find(f".//{A}srgbClr") if el is not None else None
    if c is None:
        return None
    v = c.get("val"); a = c.find(A + "alpha")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), (int(a.get("val")) / 100000) if a is not None else 1.0)


def over(img, layer):
    img.alpha_composite(layer)


def geom_mask(sp, x, y, w, h, scale=1.0):
    """filled-area mask (L) of a shape; None for open freeforms"""
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    prst = sp.find(f".//{A}prstGeom")
    if prst is not None:
        g = prst.get("prst")
        if g == "ellipse":
            d.ellipse([x, y, x + w, y + h], fill=255)
        elif g == "roundRect":
            av = prst.find(f".//{A}gd"); adj = int(re.findall(r"\d+", av.get("fmla"))[0]) / 100000 if av is not None else 0.16667
            d.rounded_rectangle([x, y, x + w, y + h], radius=adj * min(w, h), fill=255)
        else:
            d.rectangle([x, y, x + w, y + h], fill=255)
        return m
    return None


def cust_paths(sp, x, y, w, h):
    out = []
    for path in sp.findall(f".//{A}path"):
        pw, ph = float(path.get("w") or 0) or 1.0, float(path.get("h") or 0) or 1.0; pts = []; closed = False; arcs = []
        for el in path:
            tag = etree.QName(el).localname
            if tag in ("moveTo", "lnTo"):
                pt = el.find(A + "pt"); pts.append((x + float(pt.get("x")) / pw * w, y + float(pt.get("y")) / ph * h))
            elif tag == "arcTo":  # full circle from the last point: centre is wR to the left of the start
                r = float(el.get("wR")) / pw * w; sx, sy = pts[-1]; arcs.append((sx - r, sy, r))
            elif tag == "close":
                closed = True
        out.append((pts, closed, arcs))
    return out


def grad_layer(gf, x, y, w, h, mask):
    stops = []
    for gs in gf.findall(f".//{A}gs"):
        stops.append((int(gs.get("pos")) / 100000, color(gs)))
    pos = np.array([s[0] for s in stops]); cols = np.array([s[1][:3] for s in stops], dtype=np.float32); al = np.array([s[1][3] for s in stops], dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    if gf.find(A + "path") is not None:
        cx, cy = x + w / 2, y + h / 2
        t = np.sqrt(((xx - cx) / (w / 2 * 1.41421)) ** 2 + ((yy - cy) / (h / 2 * 1.41421)) ** 2)
    else:
        ang = int(gf.find(A + "lin").get("ang")) / 60000; rad = np.deg2rad(ang)
        dx, dy = np.cos(rad), np.sin(rad)
        proj = (xx - x) * dx + (yy - y) * dy; L = abs(w * dx) + abs(h * dy); t = proj / max(L, 1e-6)
        if dx < 0 or dy < 0:
            t = ((xx - x - w) * dx + (yy - y - h) * dy) / max(L, 1e-6)
    t = np.clip(t, 0, 1)
    arr = np.zeros((H, W, 4), dtype=np.float32)
    for ch in range(3):
        arr[..., ch] = np.interp(t, pos, cols[:, ch])
    arr[..., 3] = np.interp(t, pos, al) * 255 * (np.asarray(mask, dtype=np.float32) / 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def draw_sp(img, sp, dxy):
    off = sp.find(f".//{A}xfrm/{A}off"); ext = sp.find(f".//{A}xfrm/{A}ext")
    if off is None:
        return
    x, y = int(off.get("x")) / E + dxy[0], int(off.get("y")) / E + dxy[1]; w, h = int(ext.get("cx")) / E, int(ext.get("cy")) / E
    spPr = sp.find(P + "spPr")
    if spPr is None:
        spPr = sp.find(f".//{P}spPr")
    mask = geom_mask(spPr, x, y, w, h)
    paths = cust_paths(spPr, x, y, w, h) if mask is None else []
    if mask is None and paths:
        mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
        for pts, closed, arcs in paths:
            for cx, cy, r in arcs:
                dm.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
            if closed and len(pts) > 2 and not arcs:
                dm.polygon(pts, fill=255)
    fill = spPr.find(A + "solidFill"); gf = spPr.find(A + "gradFill")
    eff = spPr.find(A + "effectLst")
    if eff is not None and mask is not None:
        sh = eff.find(A + "outerShdw")
        if sh is not None:
            c = color(sh); dist = int(sh.get("dist", 0)) / E; blur = int(sh.get("blurRad", 0)) / E; sx = int(sh.get("sx", 100000)) / 100000; sy = int(sh.get("sy", 100000)) / 100000
            m2 = Image.new("L", (W, H), 0); ImageDraw.Draw(m2).rounded_rectangle([x + w * (1 - sx) / 2, y + h * (1 - sy) / 2 + dist, x + w * (1 + sx) / 2, y + h * (1 + sy) / 2 + dist], radius=12, fill=int(255 * c[3]))
            layer = Image.new("RGBA", (W, H), c[:3] + (0,)); layer.putalpha(m2.filter(ImageFilter.GaussianBlur(blur / 2))); over(img, layer)
        gl = eff.find(A + "glow")
        if gl is not None:
            c = color(gl); rad = int(gl.get("rad")) / E
            m2 = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(rad / 2)).point(lambda v: int(min(255, v * 2) * c[3]))
            layer = Image.new("RGBA", (W, H), c[:3] + (0,)); layer.putalpha(m2); over(img, layer)
    if mask is not None:
        if gf is not None:
            over(img, grad_layer(gf, x, y, w, h, mask))
        elif fill is not None:
            c = color(fill); layer = Image.new("RGBA", (W, H), c[:3] + (0,)); layer.putalpha(mask.point(lambda v: int(v * c[3]))); over(img, layer)
    ln = spPr.find(A + "ln")
    if ln is not None and ln.find(A + "solidFill") is not None:
        c = color(ln.find(A + "solidFill")); lw = max(1, int(round(int(ln.get("w", 12700)) / E)))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer); col = c[:3] + (int(255 * c[3]),)
        dash = ln.find(A + "custDash")
        prst = spPr.find(f".//{A}prstGeom")
        if prst is not None:
            g = prst.get("prst"); box = [x, y, x + w, y + h]
            if dash is not None:  # dashed outline: draw the outline, then knock out gaps along it
                pass
            if g == "ellipse":
                d.ellipse(box, outline=col, width=lw)
            elif g == "roundRect":
                av = prst.find(f".//{A}gd"); adj = int(re.findall(r"\d+", av.get("fmla"))[0]) / 100000 if av is not None else 0.16667
                d.rounded_rectangle(box, radius=adj * min(w, h), outline=col, width=lw)
            else:
                d.rectangle(box, outline=col, width=lw)
            if dash is not None:
                ds = dash.find(A + "ds"); on = int(ds.get("d")) / 100000 * lw; offd = int(ds.get("sp")) / 100000 * lw
                yy, xx = np.mgrid[0:H, 0:W]; per = on + offd
                knock = ((xx + yy) % per) > on
                arr = np.array(layer); arr[..., 3][knock] = 0; layer = Image.fromarray(arr)
        else:
            for pts, closed, arcs in paths:
                if len(pts) > 1 and not arcs:
                    if dash is not None:
                        ds = dash.find(A + "ds"); on = int(ds.get("d")) / 100000 * lw; offd = int(ds.get("sp")) / 100000 * lw
                        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                            L = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** .5, 1); t = 0
                            while t < L:
                                a0, a1 = t / L, min(t + on, L) / L
                                d.line([(x1 + (x2 - x1) * a0, y1 + (y2 - y1) * a0), (x1 + (x2 - x1) * a1, y1 + (y2 - y1) * a1)], fill=col, width=lw); t += on + offd
                    else:
                        d.line(pts, fill=col, width=lw, joint="curve")
        over(img, layer)
    tx = sp.find(P + "txBody")
    if tx is not None:
        draw_text(img, tx, x, y, w)


def draw_text(img, tx, x, y, w):
    d = ImageDraw.Draw(img)
    for p in tx.findall(A + "p"):
        algn = (p.find(A + "pPr").get("algn") if p.find(A + "pPr") is not None else None) or "l"
        sp = p.find(f"{A}pPr/{A}lnSpc/{A}spcPts")
        lines = [[]]
        for el in p:
            tag = etree.QName(el).localname
            if tag == "br":
                lines.append([])
            elif tag == "r":
                rp = el.find(A + "rPr"); t = el.find(A + "t").text or ""
                size = int(rp.get("sz", 1800)) / 100 * 2; latin = rp.find(A + "latin"); c = color(rp.find(A + "solidFill"))
                spc = int(rp.get("spc", 0)) / 100 * 2
                lines[-1].append((t, font(latin.get("typeface") if latin is not None else "", max(6, int(round(size))), rp.get("b") == "1"), c, spc, rp.get("strike")))
        lh = int(sp.get("val")) / 100 * 2 if sp is not None else 40
        for li, line in enumerate(lines):
            tot = sum(d.textlength(t, font=f) + s * len(t) for t, f, c, s, st in line)
            cx = x if algn == "l" else (x + (w - tot) / 2 if algn == "ctr" else x + w - tot)
            for t, f, c, s, st in line:
                asc, desc = f.getmetrics(); base = y + li * lh + (lh - (asc + desc)) / 2 + asc
                layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(layer); col = c[:3] + (int(255 * c[3]),); x0 = cx
                if s:
                    for ch in t:
                        dl.text((cx, base), ch, font=f, fill=col, anchor="ls"); cx += d.textlength(ch, font=f) + s
                else:
                    dl.text((cx, base), t, font=f, fill=col, anchor="ls"); cx += d.textlength(t, font=f)
                if st:
                    dl.line([(x0, base - asc * 0.3), (cx, base - asc * 0.3)], fill=col, width=1)
                over(img, layer)


def draw_pic(img, pic, rels, z, dxy):
    off = pic.find(f".//{A}xfrm/{A}off"); ext = pic.find(f".//{A}xfrm/{A}ext")
    x, y, w, h = int(off.get("x")) / E + dxy[0], int(off.get("y")) / E + dxy[1], int(ext.get("cx")) / E, int(ext.get("cy")) / E
    blip = pic.find(f".//{A}blip"); target = rels[blip.get(R + "embed")]
    im = Image.open(io.BytesIO(z.read(target))).convert("RGBA").resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
    amf = blip.find(A + "alphaModFix")
    if amf is not None:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * int(amf.get("amt")) / 100000)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); layer.paste(im, (int(round(x)), int(round(y)))); over(img, layer)


def timeline(sld):
    """-> (hidden_at_start:set, groups:[(auto, [(cls, spid, kind, data)])])"""
    hidden = set(); groups = []
    tm = sld.find(P + "timing")
    if tm is None:
        return hidden, groups
    root = tm.find(f"{P}tnLst/{P}par/{P}cTn/{P}childTnLst")
    for par in root.findall(P + "par"):
        for s in par.iter(P + "set"):
            hidden.add(int(s.find(f".//{P}spTgt").get("spid")))
    main = root.find(f"{P}seq/{P}cTn/{P}childTnLst")
    for click in main.findall(P + "par"):
        ctn = click.find(P + "cTn"); auto = any(c.get("evt") == "onBegin" for c in ctn.find(P + "stCondLst"))
        effs = []
        for eff in ctn.iter(P + "cTn"):
            cls = eff.get("presetClass")
            if not cls:
                continue
            spid = int(eff.find(f".//{P}spTgt").get("spid"))
            mo = eff.find(f".//{P}animMotion")
            effs.append((cls, spid, eff.get("repeatCount"), mo.get("path") if mo is not None else None))
        groups.append((auto, effs))
    return hidden, groups


def render_pptx(path, theme, out_dir, prefix_states):
    z = zipfile.ZipFile(path)
    pres = etree.fromstring(z.read("ppt/presentation.xml"))
    prels = {r.get("Id"): r.get("Target") for r in etree.fromstring(z.read("ppt/_rels/presentation.xml.rels"))}
    slides = ["ppt/" + prels[s.get(R + "id")] for s in pres.find(P + "sldIdLst")]
    outs = []
    for n, sp in enumerate(slides, 1):
        sld = etree.fromstring(z.read(sp))
        relp = sp.replace("slides/", "slides/_rels/") + ".rels"
        rels = {r.get("Id"): os.path.normpath(os.path.join(os.path.dirname(sp), r.get("Target"))) for r in etree.fromstring(z.read(relp))}
        hidden0, groups = timeline(sld)
        clicks = [g for g in groups if not g[0]]; autos = [g for g in groups if g[0]]
        for k in range(len(clicks) + 1):
            hidden = set(hidden0); offs = {}
            for _, effs in autos + clicks[:k]:
                for cls, spid, rep, mpath in effs:
                    if cls == "entr":
                        hidden.discard(spid)
                    elif cls == "exit":
                        hidden.add(spid)
                    elif cls == "path":
                        if rep == "indefinite":
                            hidden.discard(spid)  # looping particle: shown at its start point
                        else:
                            v = [float(t) for t in re.findall(r"-?[\d.]+", mpath)]; offs[spid] = (v[-2] * W, v[-1] * H)
                    elif cls == "emph" and rep and rep != "indefinite":
                        pass  # ping ring: grows, fades out, ends invisible
            bgc = color(sld.find(f".//{P}bg"))
            img = Image.new("RGBA", (W, H), (bgc[:3] if bgc else (0, 0, 0)) + (255,))
            tree = sld.find(f"{P}cSld/{P}spTree")
            for el in tree:
                tag = etree.QName(el).localname
                if tag not in ("sp", "pic"):
                    continue
                spid = int(el.find(f".//{P}cNvPr").get("id"))
                name = el.find(f".//{P}cNvPr").get("name")
                if spid in hidden or name == "gate ping ring":
                    continue
                dxy = offs.get(spid, (0, 0))
                if tag == "sp":
                    draw_sp(img, el, dxy)
                else:
                    draw_pic(img, el, rels, z, dxy)
            fn = os.path.join(out_dir, f"s{n}-b{k}.png"); img.convert("RGB").save(fn); outs.append((n, k, fn))
    return outs


def compare(deck, out, stills):
    """Render every click state of DECK into OUT; with STILLS, return [(state, mean |diff|)] and write pair sheets."""
    os.makedirs(out, exist_ok=True)
    rows = []
    for n, k, fn in render_pptx(deck, None, out, None):
        ref = os.path.join(stills, f"s{n}-b{k}.png") if stills else None
        if not ref or not os.path.exists(ref):
            continue
        a_ = np.asarray(Image.open(fn).convert("L"), dtype=np.float32)
        b_ = np.asarray(Image.open(ref).convert("L").resize((W, H)), dtype=np.float32)
        rows.append((f"s{n}-b{k}", float(np.abs(a_ - b_).mean())))
        pair = Image.new("RGB", (W * 2 + 16, H), (128, 128, 128))
        pair.paste(Image.open(ref).convert("RGB").resize((W, H)), (0, 0)); pair.paste(Image.open(fn).convert("RGB"), (W + 16, 0))
        pair.resize((W + 8, H // 2)).save(os.path.join(out, f"pair-s{n}-b{k}.png"))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck"); ap.add_argument("out"); ap.add_argument("--stills")
    a = ap.parse_args()
    rows = compare(a.deck, a.out, a.stills)
    for sid, d in rows:
        print(f"{sid}  mean |diff| vs HTML still = {d:5.2f}")
    if rows:
        print("worst:", ", ".join(f"{s} {d:.2f}" for s, d in sorted(rows, key=lambda r: -r[1])[:5]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
