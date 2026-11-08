#!/usr/bin/env python3
"""Generate a merged, SideStore-native source from a mix of native/legacy sources:
   - drops apps with invalid bundle IDs (SideStore bundle lookup needs real IDs)
   - normalises legacy (top-level version/downloadURL) to versions[]
   - fixes headers (name/identifier/iconURL)
   - removes duplicate bundleIdentifier entries, keeping the newest version."""
import json, ssl, sys, re, urllib.request, urllib.error, gzip

UA = "SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
BID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]*(\.[A-Za-z0-9][A-Za-z0-9\-]*)+$")

def fetch(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=600, context=ctx)
        d = r.read()
        if "gzip" in (r.headers.get("Content-Encoding") or "").lower():
            try: d = gzip.decompress(d)
            except Exception: pass
        return json.loads(d.decode("utf-8", "replace"))
    except Exception as e:
        print("  ! fetch failed", u, str(e)[:60]); return None

def norm_app(a):
    if not isinstance(a, dict): return None
    bid = a.get("bundleIdentifier")
    if not (isinstance(bid, str) and BID.match(bid)): return None
    out = {k: v for k, v in a.items() if k not in ("versions", "version", "versionDate", "versionDescription", "downloadURL", "size")}
    out["bundleIdentifier"] = bid
    vs = []
    if isinstance(a.get("versions"), list):
        for v in a["versions"]:
            if isinstance(v, dict) and v.get("downloadURL") and v.get("version"):
                vs.append({"version": str(v["version"]),
                           "date": v.get("date") or "2026-01-01T00:00:00Z",
                           "localizedDescription": v.get("localizedDescription", ""),
                           "downloadURL": v["downloadURL"],
                           **({"size": v["size"]} if v.get("size") else {})})
    if not vs and a.get("downloadURL") and a.get("version"):
        vs.append({"version": str(a["version"]), "date": a.get("versionDate") or "2026-01-01T00:00:00Z",
                   "localizedDescription": a.get("versionDescription", ""), "downloadURL": a["downloadURL"],
                   **({"size": a["size"]} if a.get("size") else {})})
    if not vs: return None
    out["versions"] = vs[:3]
    return out

def main(outfile, name, ident, icon, sources):
    merged = {}
    dropped = 0
    for label, url in sources:
        src = fetch(url)
        if not src or not isinstance(src, dict) or not isinstance(src.get("apps"), list):
            print("  ! not a source:", label); continue
        kept = 0
        for a in src["apps"]:
            n = norm_app(a)
            if not n: dropped += 1; continue
            kept += 1
            cur = merged.get(n["bundleIdentifier"])
            if cur is None or n["versions"][0].get("date", "") > cur["versions"][0].get("date", ""):
                merged[n["bundleIdentifier"]] = n
        print("  %-24s %6d apps -> %6d" % (label, len(src["apps"]), kept))
    out = {"name": name, "identifier": ident, "subtitle": "Merged SideStore-native source",
           "description": "Merged from %d upstream sources, legacy entries upgraded to versions[] format." % len(sources),
           "website": "https://github.com", "tintColor": "#0A84FF", "iconURL": icon,
           "apps": sorted(merged.values(), key=lambda a: a["name"].lower())}
    if outfile:
        with open(outfile, "w") as f: json.dump(out, f, ensure_ascii=False, indent=1)
        print("  wrote %s: %d apps, %d entries dropped" % (outfile, len(out["apps"]), dropped))

if __name__ == "__main__":
    main("sources/merged.json", "Merged Sideload Source", "dev.workspace.merged",
         "https://apptesters.org/apptesters-512x512.png",
         [("AppTesters", "https://repository.apptesters.org/apps.json"),
          ("CyPwn", "https://ipa.cypwn.xyz/cypwn.json"),
          ("OwO", "https://repo.owo.network/apps.json"),
          ("Neoncat eSign", "https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps_esign.json"),
          ("swaggy", "https://raw.githubusercontent.com/swaggyP36000/TrollStore-IPAs/main/apps.json"),
          ("Riftys", "https://raw.githubusercontent.com/notrifty1/riftysrepo/refs/heads/main/reposource.json"),
          ("Ittz_A7aa", "https://ittza7aa.com/repo.json")])
