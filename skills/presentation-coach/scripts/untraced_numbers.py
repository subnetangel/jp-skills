#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Count numeric claims in a talk track (and deck) that have no source in a figures file.

Usage:
  untraced_numbers.py --spec talk-track-spec.json [--deck deck.html] \
      --figures FIGURES.md [--figures BRIEF.md ...] [--allow allow.txt]

Prints a markdown table (claim, location, sourced, matched line) and ends with
"UNSOURCED: N". Always exits 0. Standard library only.

A claim is sourced when some line in a figures file carries the same normalized
value (number, date, multiplier, ordinal...) AND shares at least one distinctive
keyword with the claim's context, measured in a window around the value in that
source line. Distinctive = not a stopword and not present in most source lines.
"""
import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser

# ---------------------------------------------------------------- vocabulary
STOP = set("""
a an the and or but if then than that this these those there here of in on at by for to from with without into onto
over under about above below after before since until while within across per via vs versus is are was were be been
being am do does did done have has had having it its it's they them their we our us you your i me my he him his she her
who whom which what when where why how all any each every some most more less many much few no not only also just
so too very can could will would should may might must shall up down out off again still even ever yet now today
said says say let lets get got go goes going come coming one ones own same other another such like as well back
want think know see look make made take thing things way ways lot really actually right left here's that's what's
don't didn't isn't aren't wasn't i'm i'd i'll we're we've you're you've let's it'll
""".split())

NUMWORDS = {
    "zero": 0, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
# shortcut: "one" is skipped as a claim (too many idioms: "one of them", "one thing"); add a
# rule here if a deck leans on "one X" as a fact.
ORDINALS = {"first": 1, "second": 2, "third": 3}
VAGUE = {"dozens", "hundreds", "thousands", "millions", "billions"}
MULTWORDS = {"double": 2, "doubles": 2, "doubled": 2, "doubling": 2, "triple": 3, "triples": 3,
             "tripled": 3, "tripling": 3, "half": 0.5, "halve": 0.5, "halves": 0.5, "halved": 0.5}
MONTHS = {m: i + 1 for i, m in enumerate(
    "january february march april may june july august september october november december".split())}
for _k, _v in list(MONTHS.items()):
    MONTHS[_k[:3]] = _v
MONTHS["sept"] = 9
QUAL = {"early": (1, 4), "mid": (5, 8), "late": (9, 12)}
APPROX = re.compile(r"(about|almost|roughly|nearly|around|approximately|~|close to|more than|over)\s*$", re.I)
UNITS = ("%|percent|x\\b|times\\b|days?|weeks?|months?|years?|hours?|minutes?|h\\b|d\\b")

MON = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
DASH = r"\s*(?:-|–|—|to|through)\s*"
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
SPELLED = "|".join(sorted(NUMWORDS, key=len, reverse=True))


def num(s):
    return float(s.replace(",", ""))


def spelled_value(text):
    """'five hundred and twelve' -> 512, 'fifty' -> 50."""
    total, cur = 0, 0
    for w in re.split(r"[\s-]+", text.lower()):
        if w == "and":
            continue
        if w == "hundred":
            cur = (cur or 1) * 100
        elif w == "thousand":
            total += (cur or 1) * 1000
            cur = 0
        elif w in NUMWORDS:
            cur += NUMWORDS[w]
    return total + cur


# Ordered patterns. Each yields (kind, match). Earlier patterns win on overlap.
CLAIM_PATTERNS = [
    ("qrange", re.compile(rf"\bQ([1-4])(?:{DASH}Q([1-4]))?\s*(?:FY)?\s*((?:19|20)\d\d)\b")),
    ("mrange", re.compile(rf"\b({MON}){DASH}({MON})\s+((?:19|20)\d\d)\b")),
    ("mdy", re.compile(rf"\b({MON})\s+(\d{{1,2}}),?\s+((?:19|20)\d\d)\b")),
    ("my", re.compile(rf"\b({MON})\s+((?:19|20)\d\d)\b")),
    ("iso", re.compile(r"\b((?:19|20)\d\d)-(\d\d)(?:-(\d\d))?\b")),
    ("qualyear", re.compile(r"\b(early|mid|late)[\s-]((?:19|20)\d\d)\b", re.I)),
    ("relyear", re.compile(r"\b(?:(?:start|beginning|end|middle) of |early |late )?(this|last|next) (year|quarter)\b", re.I)),
    ("md", re.compile(rf"\b({MON})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b(?!\s*,?\s*(?:19|20)\d\d)")),
    ("ofn", re.compile(rf"\b({NUM})\s+of\s+(?:the\s+)?({NUM})\b")),
    ("level", re.compile(r"\b(Level|Tier|Phase|Stage)\s+(\d+)\b")),
    ("version", re.compile(r"\bv(\d+(?:\.\d+)*)\b")),
    ("range", re.compile(rf"(?<![\d.:])({NUM}){DASH}({NUM})(?![\d:])(\s*(?:%|x\b))?")),
    ("year", re.compile(r"(?<![\d.,:$-])((?:19|20)\d\d)(?![\d,.:]|-\d)")),
    ("number", re.compile(rf"(?<![\w.,:/$-])[~]?({NUM})(\s*(?:{UNITS})|/day|-\w+)?(?![\w.,:/]|\.\d)")),
    ("spelled", re.compile(rf"\b((?:{SPELLED})(?:[\s-]+(?:hundred|thousand|and|{SPELLED}))*(?:[\s-]+(?:hundred|thousand))?)(?:-plus)?\b", re.I)),
    ("multword", re.compile(r"\b(" + "|".join(MULTWORDS) + r")\b", re.I)),
    ("ordinal", re.compile(r"\b(first|second|third)\b", re.I)),
    ("vague", re.compile(r"\b(" + "|".join(VAGUE) + r")\b", re.I)),
    ("quarter", re.compile(r"\b(?:a|one|within a|planned)\s+quarter\b", re.I)),
    ("more", re.compile(r"\b(more|fewer)\s+([a-z]+s)\b(?!\s+than)", re.I)),
]
# Source lines are scanned with the same patterns, then every remaining digit run ("4.1/4.2",
# "db-4.2-std", "1,204/1,310") so a figure in a table cell still counts.
RAWNUM = ("rawnum", re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(%|x\b)?"))

TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")      # clock times, m:ss durations, [28:23]


def tokens_for(kind, m, text):
    """Normalized value tokens for one match. Returns a list of string tokens, or None to skip."""
    g = m.groups()
    if kind == "qrange":
        y = g[2]
        return [f"q:{y}Q{g[0]}"] + ([f"q:{y}Q{g[1]}"] if g[1] else [])
    if kind == "mrange":
        y = g[2]
        return [f"ym:{y}-{MONTHS[g[0].lower().rstrip('.')[:3]]:02d}",
                f"ym:{y}-{MONTHS[g[1].lower().rstrip('.')[:3]]:02d}"]
    if kind == "mdy":
        mo = MONTHS[g[0].lower().rstrip('.')[:3]]
        return [f"ymd:{g[2]}-{mo:02d}-{int(g[1]):02d}"]
    if kind == "my":
        return [f"ym:{g[1]}-{MONTHS[g[0].lower().rstrip('.')[:3]]:02d}"]
    if kind == "iso":
        if not 1 <= int(g[1]) <= 12:
            return None
        return [f"ymd:{g[0]}-{g[1]}-{g[2]}" if g[2] else f"ym:{g[0]}-{g[1]}"]
    if kind == "qualyear":
        return [f"qy:{g[0].lower()}-{g[1]}"]
    if kind == "relyear":
        return [f"rel:{m.group(0).lower()}"]
    if kind == "md":
        if not 1 <= int(g[1]) <= 31:
            return None
        return [f"md:{MONTHS[g[0].lower().rstrip('.')[:3]]:02d}-{int(g[1]):02d}"]
    if kind == "rawnum":
        v = g[0]
        p = "pct" if g[1] == "%" else "x" if g[1] == "x" else "n"
        if p == "n" and re.fullmatch(r"\d+\.\d+", v):
            return [f"n:{v}", f"n:{num(v):g}"]
        return [f"{p}:{num(v):g}"]
    if kind == "ofn":
        return [f"n:{num(g[0]):g}", f"n:{num(g[1]):g}"]
    if kind == "level":
        return [f"lvl:{g[0].lower()} {g[1]}"]
    if kind == "version":
        return [f"n:v{g[0]}"]
    if kind == "range":
        unit = (g[2] or "").strip()
        p = "pct" if unit == "%" else "x" if unit == "x" else "n"
        return [f"{p}:{num(g[0]):g}", f"{p}:{num(g[1]):g}"]
    if kind == "year":
        return [f"y:{g[0]}"]
    if kind == "number":
        v = num(g[0])
        unit = (g[1] or "").strip().lower()
        if "." in g[0] and not unit and re.fullmatch(r"\d+\.\d+", g[0]):
            return [f"n:{g[0]}"]                     # versions like 4.2: keep the literal
        if unit in ("%", "percent"):
            return [f"pct:{v:g}"]
        if unit in ("x", "times"):
            return [f"x:{v:g}"]
        return [f"n:{v:g}"]
    if kind == "spelled":
        v = spelled_value(g[0])
        if g[0].lower() in ("times",):
            return None
        after = text[m.end():m.end() + 7].lower()
        if after.startswith(" times"):
            return [f"x:{v:g}"]
        return [f"n:{v:g}"]
    if kind == "multword":
        return [f"x:{MULTWORDS[g[0].lower()]:g}"]
    if kind == "ordinal":
        return [f"ord:{ORDINALS[g[0].lower()]}"]
    if kind == "vague":
        return [f"vague:{g[0].lower()}"]
    if kind == "quarter":
        return ["dur:quarter"]
    if kind == "more":
        return [f"cmp:{g[0].lower()}"]
    return None


def find_values(text, claims_mode):
    """Return list of (start, end, kind, tokens). claims_mode applies claim filters; source mode keeps all."""
    out, taken = [], []
    masked = TIME_RE.sub(lambda mm: " " * len(mm.group(0)), text)
    for kind, rx in CLAIM_PATTERNS + ([] if claims_mode else [RAWNUM]):
        for m in rx.finditer(masked):
            s, e = m.span()
            if any(s < te and ts < e for ts, te in taken):
                continue
            toks = tokens_for(kind, m, masked)
            if not toks:
                continue
            taken.append((s, e))       # a rejected claim still owns its span ("Mar 9 standup" is not "9")
            if claims_mode and not keep_claim(kind, m, masked, toks):
                continue
            out.append((s, e, kind, toks))
    out.sort()
    return out


def next_word(text, pos):
    m = re.match(r"[\s\-]*([A-Za-z][\w'’-]*)", text[pos:])
    return m.group(1).lower() if m else ""


CITE = re.compile(r"^[\s,]*(?:\d{4}[\s,]*)?(?:\w+\s+)?(?:notes?|transcript|call|email|update|huddle|session|"
                  r"prep|meeting|workshop|status update)\b", re.I)


SENT_END = re.compile(r"[.?!][\"”’')]*(?=\s|$)")


def sentence_of(text, s, e):
    starts = [m.end() for m in SENT_END.finditer(text, 0, s)]
    m = SENT_END.search(text, e)
    return text[starts[-1] if starts else 0:m.end() if m else len(text)].strip()


def keep_claim(kind, m, text, toks):
    """Claim filters: drop bare small numbers, labels, citations, questions, idioms."""
    s, e = m.span()
    nxt = next_word(text, e)
    prev = text[max(0, s - 12):s].lower()
    sent = sentence_of(text, s, e).rstrip('"”’\' )')
    if sent.endswith("?") and kind in ("relyear", "year", "ordinal", "more", "spelled"):
        return False                      # a question to the room, not a claim
    if kind in ("md", "mdy", "my", "iso") and CITE.match(text[e:e + 40]):
        return False                      # "Feb 12, 2026 notes": a citation, not a claim
    if re.match(r"\s*/\s*\d", text[e:]) and kind == "number" and "/" not in (m.group(2) or ""):
        return False                      # "2 / 6" page numbers
    if kind == "multword" and text[e:e + 1] == "-":
        return False                      # "half-beat"
    if kind == "range" and not m.group(3) and max(num(m.group(1)), num(m.group(2))) < 10:
        return False                      # "1-6 jump keys", step ranges
    if kind == "number":
        unit = (m.group(2) or "").strip()
        v = num(m.group(1))
        if unit or "," in m.group(1) or "." in m.group(1):
            return True
        if v >= 10:
            return True
        # small bare integers need a counted noun right after ("2 teams"), not a label ("1 · Title",
        # a numbered node "1 Discover" at the start of a block)
        if not text[:s].strip() or re.search(r"[|·→=/+×]\s*$", text[:s]):
            return False
        return bool(nxt) and nxt not in STOP and not re.search(r"(step|slide|page|segment|#)\s*$", prev)
    if kind == "spelled":
        word = m.group(1).lower()
        if nxt in ("of", "or", "and", "to", "things", "thing", "words", "minutes", "seconds", "sentences"):
            # "two of them", "two or three": quantity idioms, not counted facts
            return nxt == "words" and False
        return True
    if kind == "ordinal":
        word = m.group(1).lower()
        if nxt in ("time", "thing", "things", "step", "slide", "line", "name", "half", "glance", "place",
                   "sentence", "question", "pass", "click", "look", "and", "of", "is", ""):
            return False
        if re.search(r"\b(at|the)\s*$", prev) and nxt in STOP:
            return False
        if re.search(r"\b(our|your|their|my|his|her|its)\s*$", prev):
            return False                  # "our first session": a sequence, not a ranking
        return True
    if kind == "more":
        return m.group(2).lower() not in STOP
    if kind == "multword":
        return True
    return True


# ---------------------------------------------------------------- keywords
WORD = re.compile(r"[A-Za-z][A-Za-z0-9'’+]*|(?<![\d.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d)|(?<![\d.,])\d{2,}(?:\.\d+)?(?!\d)")


def stem(w):
    w = w.lower().replace("’", "'").strip("'-")
    w = re.sub(r"'s$", "", w)
    return w[:6] if len(w) > 6 else w


def words_with_pos(text):
    # Neighbouring figures count as keywords too ("312 in Jan-Jun 2026" vs "Jan-Jun 2026: 312 / 90 d").
    return [(m.start(), "#" + m.group(0).replace(",", "") if m.group(0)[0].isdigit() else stem(m.group(0)))
            for m in WORD.finditer(text)
            if m.group(0).lower() not in STOP and len(m.group(0)) >= 2 and m.group(0).lower() not in MONTHS
            and (len(m.group(0)) >= 3 or m.group(0)[0].isdigit() or m.group(0).isupper())]


def window_keywords(text, s, e, n, common):
    ws = words_with_pos(text)
    before = [w for p, w in ws if p < s][-n:]
    after = [w for p, w in ws if p >= e][:n]
    return {w for w in before + after if w not in common}


# ---------------------------------------------------------------- inputs
CUE = re.compile(r"\[(\w+)(?::\s*([^\]]*))?\]")
SPEC_SKIP = {"id", "nav", "pauses_s", "checkpoint", "time", "timing", "rehearsal", "rehearsal_title",
             "footer", "subtitle", "forbidden_terms", "heading", "doc_title", "badge", "how_to_use",
             "method_note", "count_transition", "notes_title", "questions_intro", "label",
             # coaching meta-text and clock reminders, not things the speaker claims
             "purpose", "warmth", "competence", "reminders"}


def clean_markup(t):
    t = CUE.sub(lambda m: (" " + m.group(2) + " ") if m.group(1) in ("click", "point") and m.group(2) else " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("**", "")
    return re.sub(r"\s+", " ", t).strip()


def spec_chunks(path):
    data = json.load(open(path, encoding="utf-8"))
    out = []

    def walk(o, loc):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in SPEC_SKIP:
                    continue
                walk(v, f"{loc}.{k}" if loc else k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, dict) and "id" in v and isinstance(v["id"], str):
                    walk(v, v["id"])
                else:
                    walk(v, f"{loc}[{i}]")
        elif isinstance(o, str):
            out.append((f"spec {loc}", clean_markup(o)))
    walk(data, "")
    return out


BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div", "section", "button", "td", "th", "tr",
         "ul", "ol", "figure", "figcaption", "blockquote", "header", "footer", "aside", "br"}


class DeckParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0          # inside <style>/<head-ish>
        self.in_script = False
        self.scripts = []
        self.section = "deck"
        self.chunks = []
        self.buf = []
        self.count_depth = 0

    def flush(self):
        t = re.sub(r"\s+", " ", " ".join(self.buf)).strip()
        if t:
            self.chunks.append((f"deck {self.section}", t))
        self.buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "style":
            self.skip += 1
        elif tag == "script":
            self.in_script = True
            self.scripts.append("")
        if tag in BLOCK:
            self.flush()
        if tag == "section" and a.get("id"):
            self.section = a["id"]
        if "data-count" in a:   # animated counter: the final value is in the attribute
            self.buf.append(f"{a.get('data-prefix', '')}{a['data-count']}{a.get('data-suffix', '')}")
            self.count_depth = 1
        elif self.count_depth:
            self.count_depth += 1

    def handle_endtag(self, tag):
        if tag == "style":
            self.skip = max(0, self.skip - 1)
        elif tag == "script":
            self.in_script = False
        if self.count_depth:
            self.count_depth -= 1
        if tag in BLOCK:
            self.flush()

    def handle_data(self, d):
        if self.in_script:
            self.scripts[-1] += d
        elif not self.skip and not self.count_depth:
            self.buf.append(re.sub(r"\{\{[^}]*\}\}", " ", d))


JS_STR = re.compile(r"`((?:\\.|[^`\\])*)`|'((?:\\.|[^'\\\n])*)'|\"((?:\\.|[^\"\\\n])*)\"")


def js_unescape(s):
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    return re.sub(r"\\(.)", r"\1", s)


def deck_chunks(path):
    p = DeckParser()
    p.feed(open(path, encoding="utf-8").read())
    p.flush()
    # A tile's number sits in its own block ("3 days") and its label in the next one ("median close in the pilot").
    # Give a block of three words or fewer the next block on the same slide as context, so the label counts.
    out = []
    for i, (loc, t) in enumerate(p.chunks):
        nxt = p.chunks[i + 1] if i + 1 < len(p.chunks) else None
        if len(WORD.findall(t)) <= 3 and re.search(r"\d", t) and nxt and nxt[0] == loc:
            t = t + " · " + nxt[1]
        out.append((loc, t))
    # Prose string literals inside <script> (timeline detail arrays, speaker-notes blocks).
    # Code is skipped; only literals that read like sentences (5+ words) are kept.
    for js in p.scripts:
        for m in JS_STR.finditer(js):
            raw = next(g for g in m.groups() if g is not None)
            before = js[:m.start()]
            names = re.findall(r"(?:const|let|var)\s+(\w+)\s*=", before)
            name = names[-1] if names else "script"
            for piece in re.split(r"(?i)</?(?:p|li|h\d|div|ul)[^>]*>", js_unescape(raw)):
                t = clean_markup(piece)
                if len(WORD.findall(t)) >= 5 and "${" not in t and not re.search(r"[{};=]\s*$|=>", t):
                    out.append((f"deck script {name}", t))
    return out


# ---------------------------------------------------------------- sources
PAREN_LOC = re.compile(r"\((?:[^()]*\b(?:slide|slides|node|tab|chip|strip)\b[^()]*)\)", re.I)


def load_sources(paths):
    lines = []
    for path in paths:
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            if not line.strip():
                continue
            # Drop "(slide 2 timeline node)"-style usage notes: they say where a figure is used,
            # not what the source says.
            text = PAREN_LOC.sub(" ", line.rstrip("\n"))
            lines.append({"file": path, "line": i, "raw": line.strip(), "text": text,
                          "vals": find_values(text, claims_mode=False)})
    return lines


def source_tokens(vals):
    """Expand source tokens with derived forms (an ISO date also counts as its month and year)."""
    out = []
    for s, e, kind, toks in vals:
        for t in toks:
            ex = {t}
            k, v = t.split(":", 1)
            if k == "ymd":
                y, mo, d = v.split("-")
                ex |= {f"ym:{y}-{mo}", f"y:{y}", f"md:{mo}-{d}", f"m:{mo}"}
            elif k == "ym":
                y, mo = v.split("-")
                ex |= {f"y:{y}", f"m:{mo}"}
            elif k in ("q", "qy"):
                ex.add("y:" + v[-4:] if k == "qy" else "y:" + v[:4])
            elif k == "md":
                ex.add(f"m:{v[:2]}")
            elif k == "rel":
                ex.add("rel:" + v)
            for x in ex:
                out.append((s, e, x))
    return out


def decimals(v):
    return len(v.split(".")[1]) if "." in v else 0


def tok_match(ct, st, approx):
    if ct == st:
        return True
    ck, cv = ct.split(":", 1)
    sk, sv = st.split(":", 1)
    if ck == "ymd" and sk == "md":          # "Mar 4, 2026" vs "on March 4th"
        return cv[5:] == sv
    if ck == "qy" and sk in ("ym", "ymd"):
        q, y = cv.split("-")
        lo, hi = QUAL[q]
        return sv.startswith(y + "-") and lo <= int(sv[5:7]) <= hi
    if ck == sk and ck in ("n", "pct", "x") or (ck, sk) in (("n", "pct"), ("pct", "n"), ("x", "n")):
        try:
            a, b = float(cv), float(sv)
        except ValueError:
            return False
        if a == b:
            return True
        # the talk rounds: "12/day" for 12.04, "81%" for 80.6%, "almost five times" for 4.83x
        if decimals(sv) > decimals(cv) and round(b, decimals(cv)) == a and (ck != "n" or a >= 10):
            return True
        return approx and abs(a - b) <= 0.05 * abs(a)
    return False


# Values that are distinctive on their own: a matching figure is enough. Everything else (years,
# month-years, quarters, small counts, ordinals, word multipliers, levels) also needs a shared keyword.
def is_specific(tok):
    k, v = tok.split(":", 1)
    if k in ("ymd", "md", "lvl"):
        return True
    if k in ("n", "pct", "x"):
        try:
            f = float(v)
        except ValueError:
            return False
        return f >= 20 or "." in v or k == "x" and f >= 3
    return False


def best_line(tok, claim, sources, common):
    """Best (source, score) for one value token."""
    best, bs = None, 0
    spec = is_specific(tok)
    for src in sources:
        for s, e, st in src["stoks"]:
            if not tok_match(tok, st, claim["approx"]):
                continue
            sc = len(window_keywords(src["text"], s, e, 12, common) & claim["keywords"])
            if spec:
                sc += 1
            if sc > bs:
                best, bs = src, sc
    return best, bs


def literal_word_hit(claim, sources, common):
    """Word claims (first, doubles, hundreds, more X) match the same word stem in a source line."""
    w = claim["word"]
    best, bs = None, 0
    for src in sources:
        for m in re.finditer(rf"\b{re.escape(w[:5])}\w*", src["text"], re.I):
            if claim["kind"] == "ordinal" and re.match(r"\s*\d", src["text"][m.end():]):
                continue        # "first 250 upgrades" is a count, not a ranking
            sc = len(window_keywords(src["text"], m.start(), m.end(), 12, common) & claim["keywords"])
            if sc > bs:
                best, bs = src, sc
    return best, bs


def classify(claim, sources, common, need):
    """Return the supporting source line or None. Every value token in the claim must be supported."""
    if claim["word"]:
        src, sc = literal_word_hit(claim, sources, common)
        if claim["kind"] == "multword" and not src:
            src, sc = best_line(claim["tokens"][0], claim, sources, common)
        return src if sc >= need else None
    first = None
    if len(claim["tokens"]) > 1:
        need = 1                     # two matching values ("Jan-Feb 2026", "41 of 42") are evidence already
    for tok in claim["tokens"]:
        src, sc = best_line(tok, claim, sources, common)
        if sc < (1 if is_specific(tok) else need):
            return None
        first = first or src
    return first


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec", required=True)
    ap.add_argument("--deck")
    ap.add_argument("--figures", action="append", required=True)
    ap.add_argument("--allow")
    ap.add_argument("--window", type=int, default=8, help="context words each side of a claim (default 8)")
    ap.add_argument("--min-keywords", type=int, default=2,
                    help="shared keywords a non-distinctive value needs (default 2)")
    args = ap.parse_args()

    try:
        chunks = spec_chunks(args.spec)
        if args.deck:
            chunks += deck_chunks(args.deck)
        sources = load_sources(args.figures)
        allow = []
        if args.allow:
            allow = [l.strip().lower() for l in open(args.allow, encoding="utf-8")
                     if l.strip() and not l.startswith("#")]
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("UNSOURCED: 0")
        return 0
    for src in sources:
        src["stoks"] = source_tokens(src["vals"])

    # Words present in a large share of source lines or of talk chunks carry no signal.
    def frequent(texts, share):
        df = {}
        for t in texts:
            for w in {w for _, w in words_with_pos(t)}:
                df[w] = df.get(w, 0) + 1
        return {w for w, c in df.items() if c > share * len(texts)}
    common = frequent([s["text"] for s in sources], 0.15) | frequent([t for _, t in chunks], 0.15)

    occ = []      # one entry per claim occurrence
    for ci, (loc, text) in enumerate(chunks):
        for s, e, kind, toks in find_values(text, claims_mode=True):
            surface = text[s:e].strip()
            ctx_s = max(0, text.rfind(" ", 0, max(0, s - 60)))
            snippet = text[ctx_s:min(len(text), e + 60)].strip(" |")
            claim = {
                "kind": kind, "tokens": toks, "surface": surface,
                "approx": bool(APPROX.search(text[max(0, s - 16):s])) or surface.startswith("~"),
                "keywords": window_keywords(text, s, e, args.window, common),
                "word": surface.split()[0].lower() if kind in ("ordinal", "multword", "vague", "more") else "",
            }
            if any(a in snippet.lower() for a in allow):
                src, how = None, "allow"
            else:
                src = classify(claim, sources, common, args.min_keywords)
                how = "yes" if src else "no"
            # ordinals group by the two words after them ("first pilot run" vs "first pilot: phase two")
            nxt = [w for _, w in words_with_pos(text[e:e + 40])][:2 if kind == "ordinal" else 1]
            occ.append({"ci": ci, "s": s, "e": e, "text": text, "loc": loc, "claim": surface, "kind": kind,
                        "snippet": snippet, "how": how, "src": src,
                        "key": (tuple(toks), tuple(nxt) if claim["word"] else ())})

    # A value already sourced on the same slide/segment is sourced on its repeats there
    # ("the work has to double too" after "roughly doubles the fleet"). Only for distinctive
    # values, word multipliers, spelled counts and early/late years: "first team" being sourced says
    # nothing about "first pilot", and one sourced "Oct 2026" says nothing about another.
    def segment(loc):
        m = re.search(r"\b(s\d+)\b", loc)
        return m.group(1) if m else loc
    sourced_here = {(segment(o["loc"]), o["key"][0]) for o in occ if o["how"] == "yes"}
    for o in occ:
        if o["how"] == "no" and (all(is_specific(t) for t in o["key"][0]) or len(o["key"][0]) > 1
                                 or o["kind"] in ("multword", "spelled", "qualyear")) \
                and (segment(o["loc"]), o["key"][0]) in sourced_here:
            o["how"] = "yes (same slide)"
            o["src"] = next(x["src"] for x in occ if x["how"] == "yes" and x["key"][0] == o["key"][0]
                            and segment(x["loc"]) == segment(o["loc"]))

    # Group repeats of one claim (spec, deck, notes) and adjacent unsourced values ("2026 · Phase 2").
    parent = list(range(len(occ)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    first_by_key = {}
    for i, o in enumerate(occ):
        k = (o["key"], o["how"])
        if k in first_by_key:
            parent[find(i)] = find(first_by_key[k])
        else:
            first_by_key[k] = i
        if i and o["how"] == "no" and occ[i - 1]["how"] == "no" and occ[i - 1]["ci"] == o["ci"] \
                and re.fullmatch(r"[\s·|,]*", o["text"][occ[i - 1]["e"]:o["s"]]):
            parent[find(i)] = find(i - 1)
    groups = {}
    for i, o in enumerate(occ):
        groups.setdefault(find(i), []).append(o)

    def cell(t, n=110):
        t = t.replace("|", "\\|")
        return t if len(t) <= n else t[:n - 1] + "…"

    rows = sorted(groups.values(), key=lambda g: (g[0]["how"] != "no", occ.index(g[0])))
    print("| # | Claim | Context | Location | Sourced | Matched line |")
    print("|---|---|---|---|---|---|")
    unsourced = 0
    for n, g in enumerate(rows, 1):
        o = g[0]
        if o["how"] == "no":
            unsourced += 1
        claims = []
        for x in g:
            if x["claim"] not in claims:
                claims.append(x["claim"])
        locs = []
        for x in g:
            if x["loc"] not in locs:
                locs.append(x["loc"])
        m = "—"
        if o["src"]:
            m = f"{o['src']['file'].split('/')[-1]}:L{o['src']['line']} {cell(o['src']['raw'], 90)}"
        elif o["how"] == "allow":
            m = "allow list"
        loc = ", ".join(locs[:4]) + (f" (+{len(locs) - 4})" if len(locs) > 4 else "")
        print(f"| {n} | {cell(' / '.join(claims), 50)} | {cell(o['snippet'])} | {loc} | "
              f"{'**no**' if o['how'] == 'no' else o['how']} | {m} |")
    print()
    print(f"UNSOURCED: {unsourced}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
