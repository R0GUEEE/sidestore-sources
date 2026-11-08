#!/usr/bin/env python3
import json, ssl, re, urllib.request, gzip

UA = "SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

def get(url, timeout=30, ua=UA):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept":"*/*"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        d = r.read()
        if (r.headers.get("Content-Encoding") or "").lower().find("gzip")>=0:
            try: d = gzip.decompress(d)
            except Exception: pass
        return getattr(r,"status",200), r.geturl(), r.headers.get("Content-Type",""), d
    except urllib.error.HTTPError as e:
        return e.code, url, e.headers.get("Content-Type","") if e.headers else "", b""
    except Exception as e:
        return -1, url, "", str(e).encode()

def probe(paths, label):
    print("\n### "+label)
    for p in paths:
        st, final, ctype, d = get(p)
        if st == -1:
            print(f"  {st:>3} {p}  ERR {d[:60].decode()}")
            continue
        ok = False
        det = ""
        try:
            o = json.loads(d.decode("utf-8","replace"))
            if isinstance(o, dict) and isinstance(o.get("apps"), list):
                ok = True
                det = f"apps={len(o['apps'])} name={str(o.get('name'))[:40]} id={str(o.get('identifier'))[:40]}"
            elif isinstance(o, dict):
                ok = True; det = "json keys="+",".join(list(o.keys())[:8])
            else:
                ok = True; det = "json list len=%d" % len(o)
        except Exception:
            det = "not-json: " + d[:70].decode("utf-8","replace").replace("\n"," ")
        print(f"  {st:>3} {final[:95]}  {len(d)}B  {'OK ' if ok else '-- '} {det}")

probe([
 "https://shplash.github.io/shplash-repo/apps.json",
 "https://shplash.github.io/shplash-repo/repo.json",
 "https://shplash.github.io/shplash-repo/source.json",
 "https://shplash.github.io/shplash-repo/index.json",
 "https://shplash.github.io/shplash-repo/",
], "shplash")

probe([
 "https://repository.apptesters.org/",
 "https://repository.apptesters.org/apps.json",
 "https://repository.apptesters.org/repo.json",
 "https://repository.apptesters.org/source.json",
 "https://repository.apptesters.org/ipas.json",
 "https://apps.apptesters.org/",
 "https://apptesters.org/repo.json",
 "https://repository.apptesters.org/trollstore.json",
], "apptesters")

probe([
 "https://ipa.cypwn.xyz/cypwn.json",
 "https://ipa.cypwn.xyz/cypwn_ts.json",
 "https://ipa.cypwn.xyz/cypwn_es.json",
 "https://ipa.cypwn.xyz/cypwn_altstore.json",
 "https://ipa.cypwn.xyz/index.html",
 "https://ipa.cypwn.xyz/",
], "cypwn")

probe([
 "https://repo.owo.network/",
 "https://repo.owo.network/repo.json",
 "https://repo.owo.network/apps.json",
 "https://repo.owo.network/source.json",
 "https://owo.network/repo.json",
], "owo")

probe([
 "https://ittza7aa.com/repo.json",
 "https://ittza7aa.com/apps.json",
 "https://ittza7aa.com/vip.json",
 "https://ittza7aa.com/free.json",
 "https://ittza7aa.com/",
], "ittza7aa")

probe([
 "https://itslevii.dev/repo.json",
 "https://itslevii.dev/apps.json",
 "https://itslevii.dev/source.json",
 "https://itslevii.dev/",
], "itslevii")

probe([
 "https://fastsign.dev/repo.json",
 "https://fastsign.dev/apps.json",
 "https://fastsign.dev/source.json",
 "https://fastsign.dev/trollstore.json",
 "https://fastsign.dev/",
], "fastsign")
