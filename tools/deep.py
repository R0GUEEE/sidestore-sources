#!/usr/bin/env python3
import json, ssl, urllib.request, gzip
UA="SideStore/0.6.0"; ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA})
    try:
        r=urllib.request.urlopen(req, timeout=90, context=ctx); d=r.read()
        if (r.headers.get("Content-Encoding") or "").find("gzip")>=0: d=gzip.decompress(d)
        return r.status, d
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return -1, str(e).encode()

S={}
def load(k,u):
    st,d=get(u)
    try: S[k]=(st,json.loads(d.decode("utf-8","replace")))
    except Exception: S[k]=(st,None)
    return S[k][1]

def appshape(k):
    st,o=S[k]
    if not o: print(k,"FAIL",st); return
    a=o["apps"][0]
    print("\n##",k,"|",o.get("name"),"| apps",len(o["apps"]))
    print("  appkeys:",sorted(a.keys()))
    for f in ("versions","version","versionDate","versionDescription","downloadURL","size","bundleIdentifier"):
        if f in a: print("  %s=%s"%(f,json.dumps(a[f])[:200]))
    if "versions" in a and a["versions"]: print("  version[0]:",json.dumps(a["versions"][0])[:300])
    miss=sum(1 for x in o["apps"] if not isinstance(x.get("versions"),list) or not x.get("versions"))
    print("  apps missing versions:",miss)

load("apptesters","https://repository.apptesters.org/apps.json"); appshape("apptesters")
load("neon_esign","https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps_esign.json"); appshape("neon_esign")
load("neon_apps","https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps.json"); appshape("neon_apps")
load("neon_alt","https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps_altstore.json"); appshape("neon_alt")
load("owo","https://repo.owo.network/apps.json"); appshape("owo")
load("cypwn","https://ipa.cypwn.xyz/cypwn.json"); appshape("cypwn")
load("cypwn_alt","https://ipa.cypwn.xyz/cypwn_altstore.json"); appshape("cypwn_alt")
load("cypwn_ts","https://ipa.cypwn.xyz/cypwn_ts.json"); appshape("cypwn_ts")
load("ittz","https://ittza7aa.com/repo.json"); appshape("ittz")

# ipa.cypwn.xyz difference
c=S["cypwn"][1]; ca=S["cypwn_alt"][1]
cn={a.get("bundleIdentifier") for a in c["apps"]}; can={a.get("bundleIdentifier") for a in ca["apps"]}
print("\ncypwn.json bid only:",len(cn-can),"| cypwn_altstore.json only:",len(can-cn))
print("  altstore-only samples:",list(can-cn)[:5])
# version check for same bids
diffs=0
for a in ca["apps"]:
    m=[b for b in c["apps"] if b.get("bundleIdentifier")==a.get("bundleIdentifier")]
    if m and m[0].get("versions") and a.get("versions"):
        if m[0]["versions"][0].get("version")!=a["versions"][0].get("version"): diffs+=1
print("  same-bid version mismatches:",diffs)

# fastsign / dsewerek featured
for k,u in [("fastsign","https://fastsign.dev/repo.json"),("dsewer_general","https://raw.githubusercontent.com/dsewerek/dsewerek-s-source/main/general.json"),("dsewer_fastsign","https://raw.githubusercontent.com/dsewerek/dsewerek-s-source/main/fastsign.json"),("altmaker","https://raw.githubusercontent.com/RipeStore/altmaker/main/AltMaker.json")]:
    o=load(k,u)
    print("\n##",k,o.get("name"),"apps",len(o["apps"]),"featured",o.get("featuredApps"))
    a=o["apps"][0]; print("  sample:",json.dumps({x:a.get(x) for x in ("name","bundleIdentifier","developerName","subtitle")})[:220])
    print("  version[0]:",json.dumps(a["versions"][0])[:260] if a.get("versions") else None)

# riftys / ittza7aa duplicates
r=load("riftys","https://raw.githubusercontent.com/notrifty1/riftysrepo/refs/heads/main/reposource.json")
print("\nriftys apps:",len(r["apps"]),"sample:",json.dumps(r["apps"][0])[:250])
print("ittz apps:",len(S["ittz"][1]["apps"]),"unique bids:",len({a.get('bundleIdentifier') for a in S['ittz'][1]['apps']}))
print("  ittz version[0]:",json.dumps(S["ittz"][1]["apps"][0].get("versions",[{}])[0])[:200] if isinstance(S["ittz"][1]["apps"][0].get("versions"),list) else S["ittz"][1]["apps"][0].get("version"))
print("  ittz sample app:",json.dumps({x:S['ittz'][1]['apps'][0].get(x) for x in ('name','bundleIdentifier','version','downloadURL')})[:250])
o=S["owo"][1]; print("owo version[0]:",json.dumps(o["apps"][0].get("versions",[{}])[0])[:220] if isinstance(o["apps"][0].get("versions"),list) else "no versions")
print("apptesters META:",json.dumps(S["apptesters"][1].get("META"))[:300])
