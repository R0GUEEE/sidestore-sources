#!/usr/bin/env python3
"""Pull community repo directories (machine-readable) to widen the candidate set."""
import json, ssl, re, urllib.request, urllib.error, gzip
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
H = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}

def get(u, timeout=60):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=timeout, context=ctx)
        d = r.read()
        if "gzip" in (r.headers.get("Content-Encoding") or "").lower():
            try: d = gzip.decompress(d)
            except Exception: pass
        return r.status, d.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return -1, ""

SOURCES = [
    "https://api.github.com/repos/sideloading-repositories/repos/git/trees/main?recursive=1",
    "https://api.github.com/repos/SideStore/SideStore/git/trees/develop?recursive=1",
]
urls = set()
for s in SOURCES:
    st, body = get(s)
    if st != 200:
        print("ERR", st, s); continue
    j = json.loads(body)
    paths = [t["path"] for t in j.get("tree", [])]
    print(s, "->", len(paths), "paths")
    for p in paths:
        if p.endswith(".json") and p.count("/") <= 3 and "content" not in p:
            raw = "https://raw.githubusercontent.com/%s/%s/%s" % (
                "sideloading-repositories/repos" if "sideloading-repositories" in s else "SideStore/SideStore",
                "main" if "sideloading-repositories" in s else "develop", p)
            st2, b = get(raw, 90)
            if st2 != 200: continue
            for m in re.findall(r'https?://[^\s"\'<>()\]]+', b):
                if not m.endswith(".json") or "api.github.com" in m: continue
                if m not in urls:
                    urls.add(m)
                    print("   ", p, "->", m)
open("community_list.txt", "w").write("\n".join(sorted(urls)))
print("total", len(urls))
