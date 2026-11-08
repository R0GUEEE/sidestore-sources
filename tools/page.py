#!/usr/bin/env python3
import json, re, ssl, sys, urllib.request, urllib.error, gzip
UA="SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def fetch(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=240,context=ctx)
        d=r.read()
        if "gzip" in (r.headers.get("Content-Encoding") or "").lower():
            try: d=gzip.decompress(d)
            except Exception: pass
        return r.status, d
    except urllib.error.HTTPError as e: return e.code, b""
    except Exception: return -1, b""
def judge(u):
    st,b=fetch(u)
    if st!=200: return "HTTP %s"%st
    try: src=json.loads(b.decode("utf-8","replace"))
    except Exception: return "NOT JSON"
    if not isinstance(src,dict): return "json %s"%type(src).__name__
    if not all(isinstance(src.get(k),str) for k in ("name","identifier")): return "HEADER MISSING"
    apps=src.get("apps") if isinstance(src.get("apps"),list) else []
    std=[a for a in apps if isinstance(a,dict) and isinstance(a.get("versions"),list) and a["versions"] and isinstance(a["versions"][0],dict) and a["versions"][0].get("downloadURL")]
    leg=[a for a in apps if isinstance(a,dict) and a.get("downloadURL") and a not in std]
    if std and not leg: return "OK %d"%len(std)
    if std: return "PARTIAL %d/%d"%(len(std),len(apps))
    if leg: return "LEGACY %d"%len(leg)
    return "NO APPS"
pages = sys.argv[1:]
cands=set()
for p in pages:
    st,b=fetch(p)
    if st!=200: print("page",st,p); continue
    t=b.decode("utf-8","replace")
    found=set(re.findall(r'https?://[^\s"\'<>()\]]+\.json', t))
    found|={"https://%s%s"%(p.split('/')[2],"".join(mm.split('"')[0])) for mm in re.findall(r'["\']((?:/|\.\./|\./)?[^"\']{0,120}\.json)', t) if not mm.startswith("http")}
    print("--",p,"candidates",len(found))
    cands|=found
for c in sorted(cands):
    print("%-22s %s"%(judge(c), c))
