#!/usr/bin/env python3
import json, ssl, urllib.request, gzip
UA="SideStore/0.6.0"; ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Accept":"application/vnd.github+json"})
    try:
        r=urllib.request.urlopen(req, timeout=30, context=ctx); d=r.read()
        if (r.headers.get("Content-Encoding") or "").find("gzip")>=0:
            d=gzip.decompress(d)
        return r.status, d
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return -1, str(e).encode()

def gh_tree(repo, branch):
    st,d = get(f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1")
    if st!=200:
        print(f"  [{repo}] tree err {st}: {d[:150].decode('utf-8','replace')}")
        return
    j=json.loads(d)
    js=[t["path"] for t in j.get("tree",[]) if t["path"].lower().endswith(".json")]
    print(f"  [{repo}@{branch}] {len(js)} json files:")
    for p in js: print("      ", p)

for repo,branch in [
 ("LiveContainer/LiveContainer","main"),
 ("notrifty1/riftysrepo","main"),
 ("FrizzleM/SideInstaller","main"),
 ("Neoncat-OG/TrollStore-IPAs","main"),
 ("RipeStore/altmaker","main"),
 ("dsewerek/dsewerek-s-source","main"),
 ("NexSideloading/app-source","main"),
 ("shplash/shplash-repo","main"),
 ("OwO-Network/Repo","main"),
]:
    gh_tree(repo,branch)

print("\n=== LiveContainer nightly release assets ===")
st,d=get("https://api.github.com/repos/LiveContainer/LiveContainer/releases/tags/nightly")
if st==200:
    j=json.loads(d)
    for a in j.get("assets",[]):
        print(f"  {a['name']}  {a['size']}B  {a['browser_download_url']}")
else: print(st, d[:200])

print("\n=== cypwn_altstore keys ===")
st,d=get("https://ipa.cypwn.xyz/cypwn_altstore.json")
o=json.loads(d); print(list(o.keys())[:12], "apps", len(o["apps"]))
print("first app:", json.dumps(o["apps"][0])[:400])
