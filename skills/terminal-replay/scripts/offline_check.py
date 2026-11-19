#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Static offline check: prove an HTML file is one self-contained file that makes 0 network requests.

Usage:
  offline_check.py FILE.html [FILE.html ...] [--allow-local] [--json OUT.json]

Reads each file (no browser, no network) and lists every reference that would make the browser fetch something:
  * src, srcset, poster, data, background, action, formaction, <link href>, <meta http-equiv=refresh>, <base href>
  * url(...) and @import in <style> blocks and style="" attributes
  * fetch(, XMLHttpRequest .open(, import(, import ... from, new Worker(, new EventSource(, new WebSocket(,
    navigator.sendBeacon(, and any http(s):// or // URL literal inside <script>
data:, blob:, about:, javascript: and #fragment references are inline and do not count. XML namespace URIs
(xmlns="http://www.w3.org/...") are names, not requests, and do not count.

Each reference is classed as:
  REQUEST    a network fetch (http, https, protocol-relative //, ws, wss)       -> must be 0
  LOCAL      a file next to this one (the page breaks when copied alone)       -> must be 0 unless --allow-local
  LINK       an <a href> to the web: not loaded, only opened when clicked       -> reported, never fails
Prints one line per finding and a summary line per file:  OFFLINE: <file> requests=N local=N links=N PASS|FAIL
Exit 0 when every file passes, 1 otherwise, 2 on usage errors.

This is a static scan. It cannot see a URL built at run time from pieces, so for a final proof also open the file
with the network off (for example browser dev tools, Network tab, "Offline") and watch for requests. Say which of
the two you ran. Python 3.9+, standard library only.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser

DATA_URI = re.compile(r"data:[a-z0-9.+/-]+(?:;[a-z0-9=.+-]+)*;base64,[A-Za-z0-9+/=\s]+", re.I)
NETWORK = re.compile(r"^\s*(?:https?:|wss?:|//)", re.I)
INLINE = re.compile(r"^\s*(?:data:|blob:|about:|javascript:|mailto:|tel:|#|$)", re.I)
NAMESPACE = re.compile(r"^https?://www\.w3\.org/", re.I)
CSS_URL = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)|@import\s+(?:url\()?\s*['\"]([^'\"]+)['\"]", re.I)
JS_CALLS = re.compile(
    r"\b(?:fetch|import|navigator\.sendBeacon|new\s+(?:Worker|SharedWorker|EventSource|WebSocket))\s*\(\s*[`'\"]([^`'\"]+)"
    r"|\.open\(\s*['\"][A-Z]+['\"]\s*,\s*[`'\"]([^`'\"]+)"
    r"|\bimport\s+[^'\"]*?\bfrom\s+['\"]([^'\"]+)['\"]"
    r"|^\s*import\s+['\"]([^'\"]+)['\"]", re.M)
JS_URL = re.compile(r"[`'\"]((?:https?:|wss?:)?//[^`'\"\s]+)[`'\"]")
URL_ATTRS = {"src", "poster", "data", "background", "action", "formaction"}


def classify(url):
    if INLINE.match(url) or NAMESPACE.match(url):
        return None
    return "REQUEST" if NETWORK.match(url) else "LOCAL"


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found, self.in_style, self.in_script = [], False, False

    def add(self, kind, where, url):
        if kind:
            self.found.append({"kind": kind, "where": where, "url": url.strip()[:160], "line": self.getpos()[0]})

    def css(self, text, where):
        for m in CSS_URL.finditer(text):
            u = m.group(2) or m.group(3) or ""
            self.add(classify(u), where, u)

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "style":
            self.in_style = True
        if tag == "script":
            self.in_script = True
            if a.get("src"):
                self.add(classify(a["src"]), "script src", a["src"])
            return
        for k in URL_ATTRS & a.keys():
            self.add(classify(a[k]), f"{tag} {k}", a[k])
        for k in ("srcset", "imagesrcset"):
            for part in filter(None, (p.strip().split(" ")[0] for p in a.get(k, "").split(","))):
                self.add(classify(part), f"{tag} {k}", part)
        if tag in ("link", "base") and a.get("href"):
            self.add(classify(a["href"]), f"{tag} href", a["href"])
        if tag in ("a", "area") and a.get("href") and NETWORK.match(a["href"]):
            self.add("LINK", f"{tag} href", a["href"])
        if tag == "meta" and a.get("http-equiv", "").lower() == "refresh":
            m = re.search(r"url\s*=\s*(.+)", a.get("content", ""), re.I)
            if m:
                self.add(classify(m.group(1)), "meta refresh", m.group(1))
        if tag in ("use", "image", "feimage"):
            for k in ("href", "xlink:href"):
                if a.get(k):
                    self.add(classify(a[k]), f"{tag} {k}", a[k])
        if a.get("style"):
            self.css(a["style"], f"{tag} style")

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag == "script":
            self.in_script = False

    def handle_data(self, data):
        if self.in_style:
            self.css(data, "style")
        elif self.in_script:
            seen = set()
            for m in JS_CALLS.finditer(data):
                u = next(g for g in m.groups() if g)
                seen.add(u)
                self.add(classify(u), "script call", u)
            for m in JS_URL.finditer(data):
                if m.group(1) not in seen:
                    self.add(classify(m.group(1)), "script url", m.group(1))


def check(path, allow_local):
    text = open(path, encoding="utf-8", errors="replace").read()
    text = DATA_URI.sub(lambda m: "data:x;base64," + " " * 0, text)   # inline payloads cannot request anything
    s = Scan()
    s.feed(text)
    s.close()
    n = {k: sum(1 for f in s.found if f["kind"] == k) for k in ("REQUEST", "LOCAL", "LINK")}
    ok = n["REQUEST"] == 0 and (allow_local or n["LOCAL"] == 0)
    return {"file": path, "bytes": len(text.encode("utf-8")), "counts": n, "pass": ok, "findings": s.found}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--allow-local", action="store_true", help="a folder package: local files are allowed")
    ap.add_argument("--json", help="write the full result as JSON")
    a = ap.parse_args()
    results, ok = [], True
    for f in a.files:
        try:
            r = check(f, a.allow_local)
        except OSError as e:
            print(f"offline_check: {e}", file=sys.stderr)
            return 2
        results.append(r)
        for x in r["findings"]:
            print(f"  {x['kind']:<8} {f}:{x['line']}  {x['where']:<14} {x['url']}")
        c = r["counts"]
        print(f"OFFLINE: {f} requests={c['REQUEST']} local={c['LOCAL']} links={c['LINK']} "
              f"{'PASS' if r['pass'] else 'FAIL'} (static scan)")
        ok = ok and r["pass"]
    if a.json:
        json.dump(results, open(a.json, "w", encoding="utf-8"), indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
