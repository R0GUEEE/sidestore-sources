#!/usr/bin/env python3
"""Build one aggregate source from all converted files in sources/ (excluding
sources/merged.json itself) and refresh docs/catalog.json + docs/conversion.json."""
import json, os, glob, datetime, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
sys.path.insert(0, here)
from convert import BID  # noqa: E402

src_dir = os.path.join(root, "sources")
apps, per = {}, []
for p in sorted(glob.glob(os.path.join(src_dir, "*.json"))):
    fn = os.path.basename(p)
    if fn == "merged.json": continue
    try: o = json.load(open(p))
    except Exception as e:
        print("  ! %-30s %s" % (fn, e)); continue
    if not isinstance(o, dict) or not isinstance(o.get("apps"), list):
        print("  ! %-30s not a source" % fn); continue
    kept = 0
    for a in o["apps"]:
        bid = a.get("bundleIdentifier")
        if not isinstance(bid, str) or not a.get("versions"): continue
        kept += 1
        cur = apps.get(bid)
        if cur is None or a["versions"][0].get("date", "") > cur["versions"][0].get("date", ""):
            apps[bid] = a
    per.append({"file": fn, "name": o.get("name", ""), "identifier": o.get("identifier", ""),
                "apps": len(o["apps"]), "unique_bundle_ids": kept,
                "url": "https://raw.githubusercontent.com/R0GUEEE/sidestore-sources/main/sources/" + fn})
    print("  %-30s %5d apps" % (fn, len(o["apps"])))

merged = {
    "name": "Sideload Sources (merged)",
    "identifier": "dev.sideloadsources.merged",
    "subtitle": "%d apps merged from %d converted sources" % (len(apps), len(per)),
    "description": "Every upstream source in this repository, normalized into SideStore's versions[] format and deduplicated by bundle identifier (newest version wins).",
    "website": "https://github.com/R0GUEEE/sidestore-sources",
    "tintColor": "#0A84FF",
    "iconURL": "https://apptesters.org/apptesters-512x512.png",
    "apps": sorted(apps.values(), key=lambda a: a["name"].lower()),
}
with open(os.path.join(src_dir, "merged.json"), "w") as f:
    json.dump(merged, f, ensure_ascii=False, indent=1)
print("  %-30s %5d apps (unique bundle IDs)" % ("merged.json", len(merged["apps"])))

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
json.dump({"generated": now, "sources": per, "merged_apps": len(merged["apps"])},
          open(os.path.join(root, "docs", "catalog.json"), "w"), indent=1)
conv = json.load(open(os.path.join(root, "docs", "conversion.json"))) if os.path.exists(os.path.join(root, "docs", "conversion.json")) else {"results": []}
conv["merged"] = {"apps": len(merged["apps"]), "sources": len(per)}
conv["generated"] = now
json.dump(conv, open(os.path.join(root, "docs", "conversion.json"), "w"), indent=1)
