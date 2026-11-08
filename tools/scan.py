#!/usr/bin/env python3
import json, ssl, sys, re, urllib.request, urllib.error, gzip, io

UA = "SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"

URLS = [
 "https://github.com/LiveContainer/LiveContainer/releases/download/nightly/apps_nightly.json",
 "https://shplash.github.io/shplash-repo/apps.json",
 "https://repository.apptesters.org",
 "https://ipa.cypwn.xyz/cypwn.json",
 "https://raw.githubusercontent.com/notrifty1/riftysrepo/refs/heads/main/reposource.json",
 "https://github.com/FrizzleM/SideInstaller/raw/main/frizzlem.json",
 "https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps_esign.json",
 "https://repo.owo.network/",
 "https://ipa.cypwn.xyz/cypwn_ts.json",
 "https://raw.githubusercontent.com/RipeStore/altmaker/main/AltMaker.json",
 "https://raw.githubusercontent.com/dsewerek/dsewerek-s-source/main/general.json",
 "https://ittza7aa.com/repo.json",
 "https://itslevii.dev/repo.json",
 "file:///var/mobile/Containers/Data/Application/3602361B-8948-4A8C-A015-AF28C0AC56EE/Documents/Telegram/telegram-source.json",
 "https://raw.githubusercontent.com/NexSideloading/app-source/refs/heads/main/repo.json",
 "https://fastsign.dev/repo.json",
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/html,*/*"})
    r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
    data = r.read()
    enc = (r.headers.get("Content-Encoding") or "").lower()
    if "gzip" in enc:
        try: data = gzip.decompress(data)
        except Exception: pass
    body = data.decode("utf-8", "replace")
    return r.status if hasattr(r, "status") else 200, r.geturl(), r.headers.get("Content-Type", ""), body

def classify(obj):
    if not isinstance(obj, dict): return "json(non-object)"
    keys = set(obj.keys())
    apps = obj.get("apps")
    has_std = "name" in keys and "identifier" in keys and isinstance(apps, list)
    out = []
    if isinstance(apps, list):
        n = len(apps)
        # version counting
        vtotal = 0; dl = 0
        bid = 0; screenshots = 0
        for a in apps:
            if not isinstance(a, dict): continue
            if a.get("bundleIdentifier"): bid += 1
            if a.get("screenshots") or a.get("appPermissions"): screenshots += 1
            vs = a.get("versions")
            if isinstance(vs, list):
                vtotal += len(vs)
                for v in vs:
                    if isinstance(v, dict) and v.get("downloadURL"): dl += 1
        out.append(f"apps={n} bundleIDs={bid} versions={vtotal} downloadURLs={dl}")
    else:
        out.append("no apps[]")
    if "iconURL" in keys: out.append("iconURL")
    if "news" in keys: out.append(f"news={len(obj['news']) if isinstance(obj['news'], list) else '?'}")
    if "featuredApps" in keys: out.append("featuredApps")
    if "tintColor" in keys: out.append("tintColor")
    if "subtitle" in keys: out.append("subtitle")
    typ = "SIDESTORE/ALTSTORE source" if has_std else ("JSON w/ apps, non-standard header" if isinstance(apps, list) else "JSON unknown shape")
    out.append(typ)
    return "; ".join(out)

def json_links(url, body):
    links = set()
    for m in re.finditer(r'href=["\']([^"\']+\.json[^"\']*)["\']', body, re.I):
        links.add(m.group(1))
    for m in re.finditer(r'(https?://[^\s"\'<>]+\.json)', body):
        links.add(m.group(1))
    return sorted(links)[:25]

for u in URLS:
    print("="*100)
    print("URL:", u)
    try:
        st, final, ctype, body = get(u)
        print(f"HTTP {st}  final={final}")
        print(f"ctype={ctype}  bytes={len(body)}")
        ok = False
        try:
            obj = json.loads(body)
            ok = True
        except Exception as e:
            obj = None
        if ok:
            print("CLASS:", classify(obj))
            if isinstance(obj, dict):
                print("TOPKEYS:", list(obj.keys())[:20])
                for k in ("name","identifier","subtitle","website","tintColor","iconURL"):
                    if k in obj and not isinstance(obj[k], list):
                        print(f"  {k} = {str(obj[k])[:120]}")
            else:
                print("TOP type:", type(obj).__name__)
        else:
            s = body.lstrip()
            print("NOT JSON. head:", s[:180].replace("\n"," "))
            for l in json_links(u, body):
                print("  JSONLINK:", l)
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e)[:200])
