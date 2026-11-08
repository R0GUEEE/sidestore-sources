#!/usr/bin/env python3
import json, ssl, urllib.request, gzip, sys
UA="SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"*/*"})
    try:
        r=urllib.request.urlopen(req, timeout=60, context=ctx); d=r.read()
        if (r.headers.get("Content-Encoding") or "").find("gzip")>=0: d=gzip.decompress(d)
        return r.status, d, r.headers.get("Content-Type","")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("Content-Type","") if e.headers else ""
    except Exception as e:
        return -1, str(e).encode(), ""

URLS = sys.argv[1:]
for u in URLS:
    st,d,ct = get(u)
    line=[u, str(st), str(len(d))]
    try:
        o=json.loads(d.decode("utf-8","replace"))
        if isinstance(o,dict) and isinstance(o.get("apps"),list):
            apps=o["apps"]; n=len(apps)
            withver=sum(1 for a in apps if isinstance(a,dict) and isinstance(a.get("versions"),list) and a["versions"])
            bids=sum(1 for a in apps if isinstance(a,dict) and a.get("bundleIdentifier"))
            line += ["apps=%d"%n, "withVersions=%d"%withver, "withBundleID=%d"%bids,
                     "name=%s"%str(o.get("name"))[:35], "id=%s"%str(o.get("identifier"))[:35]]
        elif isinstance(o,dict) and "apps" in o:
            line += ["apps is %s"%type(o["apps"]).__name__]
        elif isinstance(o,dict):
            line += ["json non-source keys=%d"%len(o)]
        else:
            line += ["json %s len=%d"%(type(o).__name__, len(o) if hasattr(o,'__len__') else 0)]
    except Exception:
        line += ["NON-JSON", d[:80].decode("utf-8","replace").replace("\n"," ")]
    print(" | ".join(line))
