#!/usr/bin/env python3
"""Validate a list of source URLs the way SideStore's Source decoding works."""
import json, ssl, sys, urllib.request, urllib.error, gzip

UA = "SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    if url.startswith("file://"):
        try:
            with open(url[7:], "rb") as f: return 200, f.read()
        except Exception as e:
            return -1, str(e).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180, context=ctx)
        d = r.read()
        if "gzip" in (r.headers.get("Content-Encoding") or "").lower():
            try: d = gzip.decompress(d)
            except Exception: pass
        return getattr(r, "status", 200), d
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return -1, b""

for url in sys.argv[1:]:
    st, body = fetch(url)
    if st != 200:
        print("HTTP %s  %s" % (st, url)); continue
    try: src = json.loads(body.decode("utf-8", "replace"))
    except Exception as e:
        print("NOT JSON (%s)  %s" % (str(e)[:40], url)); continue
    if not isinstance(src, dict):
        print("%-46s %-34s %s" % ("NOT A SOURCE (json %s)" % type(src).__name__, "-", url)); continue
    hdr = [k for k in ("name", "identifier") if isinstance(src.get(k), str) and src.get(k)]
    apps = src.get("apps") if isinstance(src.get("apps"), list) else []
    std = [a for a in apps if isinstance(a, dict) and isinstance(a.get("versions"), list) and a["versions"]
           and isinstance(a["versions"][0].get("downloadURL"), str)]
    leg = [a for a in apps if isinstance(a, dict) and not (isinstance(a.get("versions"), list) and a["versions"])
           and a.get("downloadURL")]
    if len(hdr) < 2:
        v = "FAIL header missing %s" % ({"name","identifier"} - set(hdr))
    elif not apps:
        v = "FAIL no apps"
    elif len(std) == 0:
        v = "FAIL 0/%d apps in versions[] format" % len(apps)
    elif len(std) < len(apps):
        v = "PARTIAL %d std / %d legacy of %d" % (len(std), len(leg), len(apps))
    else:
        v = "OK %d apps" % len(std)
    print("%-46s %-34s %s" % (v, str(src.get("name"))[:32], url))
