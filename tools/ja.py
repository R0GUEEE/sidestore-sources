#!/usr/bin/env python3
"""Rate-limit-tolerant validator over a URL list (one line per URL)."""
import json, ssl, sys, urllib.request, urllib.error, gzip

UA = "SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120, context=ctx)
        d = r.read()
        if "gzip" in (r.headers.get("Content-Encoding") or "").lower():
            try: d = gzip.decompress(d)
            except Exception: pass
        return getattr(r, "status", 200), d
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return -1, b""

def judge(url):
    st, body = fetch(url)
    if st != 200: return "HTTP %s" % st
    try: src = json.loads(body.decode("utf-8", "replace"))
    except Exception: return "NOT JSON (%d bytes)" % len(body)
    if not isinstance(src, dict): return "json %s (not a source)" % type(src).__name__
    miss = [k for k in ("name", "identifier") if not isinstance(src.get(k), str)]
    apps = src.get("apps") if isinstance(src.get("apps"), list) else None
    if miss: return "HEADER MISSING %s" % ",".join(miss)
    if apps is None: return "NO apps[]"
    std = [a for a in apps if isinstance(a, dict) and isinstance(a.get("versions"), list) and a["versions"]
           and isinstance(a["versions"][0], dict) and a["versions"][0].get("downloadURL")]
    leg = [a for a in apps if isinstance(a, dict) and a.get("downloadURL") and not (isinstance(a.get("versions"), list) and a["versions"])]
    n = len(apps)
    if std and not leg: return "OK %d apps" % len(std)
    if std and leg: return "PARTIAL %d std / %d legacy of %d" % (len(std), len(leg), n)
    if leg: return "LEGACY-ONLY %d apps" % len(leg)
    return "NO INSTALLABLE APPS (%d entries)" % n

for url in [l.strip() for l in sys.stdin if l.strip()]:
    print("%-44s %s" % (judge(url), url))
