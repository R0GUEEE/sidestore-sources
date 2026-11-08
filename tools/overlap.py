#!/usr/bin/env python3
import json, ssl, urllib.request, gzip, collections
UA="SideStore/0.6.0"; ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def g(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=600,context=ctx)
    d=r.read()
    if "gzip" in (r.headers.get("Content-Encoding") or "").lower(): d=gzip.decompress(d)
    return json.loads(d.decode("utf-8","replace"))
fs=g("https://fastsign.dev/repo.json")
gen=g("https://raw.githubusercontent.com/dsewerek/dsewerek-s-source/main/general.json")
devs=collections.Counter(a.get("developerName") for a in fs["apps"])
print("fastsign apps",len(fs["apps"]),"distinct developers",len(devs))
print("top20:",devs.most_common(20))
fv=set(); genids=set()
for a in fs["apps"]:
    for v in a.get("versions",[]): fv.add(v.get("downloadURL"))
keep=[]
for a in gen["apps"]:
    vs=[]
    for v in a.get("versions",[]):
        if v.get("downloadURL") not in fv: vs.append(v)
    if vs:
        keep.append(dict(a, versions=vs))
print("general apps with versions NOT already in fastsign:",len(keep),"of",len(gen["apps"]))
print("sample kept:",[a["name"] for a in keep[:15]])
# which developers show up
print("kept developers:",collections.Counter(a.get("developerName") for a in keep).most_common(15))
# bundle id collisions in fastsign (dupes)
bids=collections.Counter(a.get("bundleIdentifier") for a in fs["apps"])
print("fastsign duplicate bundleIDs:",sum(1 for k,v in bids.items() if v>1),"apps involved:",sum(v for k,v in bids.items() if v>1))
print("fastsign sample dupe:",[(k,v) for k,v in bids.most_common(3)])
