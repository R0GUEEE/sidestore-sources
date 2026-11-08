#!/usr/bin/env python3
"""Emit one SideStore-compatible source file per app.

Output: apps/<slug>.json — header carries the app name/identifier, apps[] holds exactly
one entry, every version object has version/date/downloadURL/localizedDescription/size(Int).
Also writes apps/index.json (catalog) and apps/all.json (concatenation of every app).
"""
import json, os, re, glob, hashlib, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
src_dir = os.path.join(root, "sources")
out_dir = os.path.join(root, "apps")
os.makedirs(out_dir, exist_ok=True)

BASE = "https://raw.githubusercontent.com/R0GUEEE/sidestore-sources/main/apps/"

def slug(bid):
    s = re.sub(r"[^A-Za-z0-9]+", "-", bid).strip("-").lower()
    return s[:80] or "app-" + hashlib.md5(bid.encode()).hexdigest()[:8]

def clean(a, fallback_icon=""):
    bid = a["bundleIdentifier"]
    vs = []
    for v in a.get("versions", []):
        vs.append({
            "version": str(v.get("version") or "unknown"),
            "date": str(v.get("date") or "2000-01-01T00:00:00Z"),
            "localizedDescription": str(v.get("localizedDescription") or ""),
            "downloadURL": v["downloadURL"],
            "size": v["size"] if isinstance(v.get("size"), int) else 0,
        })
    app = {
        "bundleIdentifier": bid,
        "name": str(a.get("name") or bid),
        "developerName": str(a.get("developerName") or ""),
        "subtitle": str(a.get("subtitle") or ""),
        "localizedDescription": str(a.get("localizedDescription") or ""),
        "iconURL": str(a.get("iconURL") or fallback_icon),
        "tintColor": a.get("tintColor") or "#0A84FF",
        "screenshots": [s for s in (a.get("screenshots") or []) if isinstance(s, str)][:5],
        "versions": vs,
    }
    if isinstance(a.get("appPermissions"), dict): app["appPermissions"] = a["appPermissions"]
    return app

# Variant-aware unit: the same bundle ID appears in several repos as *different*
# builds (YouTube+YTKACE, YouTube+uYou, Instagram mods…). Group by
# (bundleIdentifier, app name, download host) so each variant gets its own file,
# then keep the newest version per unit. Different sources that describe the same
# build just collapse into one file.
units = {}
for p in sorted(glob.glob(os.path.join(src_dir, "*.json"))):
    fn = os.path.basename(p)
    o = json.load(open(p))
    icon = o.get("iconURL") or ""
    for a in o.get("apps", []):
        bid = a.get("bundleIdentifier")
        if not isinstance(bid, str) or not a.get("versions"): continue
        dl = a["versions"][0].get("downloadURL") or ""
        host = dl.split("/")[2] if dl.count("/") >= 2 else ""
        key = (bid, str(a.get("name") or ""), host)
        d = str(a["versions"][0].get("date") or "")
        if key not in units or d > str(units[key][0]["versions"][0].get("date") or ""):
            units[key] = (a, fn, icon)

used_names = set()
def unique_slug(bid, name):
    """Deterministic, collision-free: base slug for the primary variant of a bundle ID,
    base--<variant> for others, numeric suffix if two variants sanitize identically."""
    base = slug(bid)
    if not used_names or base not in used_names:
        cand = base
    else:
        v = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()[:50] or "v"
        cand = base + "--" + v
        i = 2
        while cand in used_names:
            cand = "%s--%s-%d" % (base, v, i); i += 1
    used_names.add(cand)
    return cand

written, index = 0, []
for (bid, aname, host), (a, fn, icon) in units.items():
    app = clean(a, icon)
    name = app["name"]
    fname = unique_slug(bid, aname) + ".json"
    src = {
        "name": name,
        "identifier": "dev.perapp.%s" % slug(bid)[:60],
        "subtitle": (app["subtitle"] or ("%s by %s" % (name, app["developerName"]) if app["developerName"] else name))[:120],
        "description": "Single-app source for %s (%s). Converted from %s." % (name, bid, fn),
        "website": "https://github.com/R0GUEEE/sidestore-sources",
        "tintColor": app["tintColor"],
        "iconURL": app["iconURL"],
        "apps": [app],
    }
    with open(os.path.join(out_dir, fname), "w") as f:
        json.dump(src, f, ensure_ascii=False, indent=1)
    written += 1
    index.append({"file": fname, "url": BASE + fname, "name": name, "bundleIdentifier": bid, "host": host,
                  "developer": app["developerName"], "version": app["versions"][0]["version"],
                  "date": app["versions"][0]["date"], "icon": app["iconURL"],
                  "source_file": fn})

index.sort(key=lambda x: x["name"].lower())
json.dump({"generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "count": written, "apps": index}, open(os.path.join(out_dir, "index.json"), "w"), indent=1)

allapps = [clean(a, icon) for _, (a, fn, icon) in sorted(best.items())] if False else [clean(a, icon) for (a, fn, icon) in
           sorted(units.values(), key=lambda x: (x[0].get("bundleIdentifier") or "", str(x[0].get("name") or "")))]
json.dump({"name": "Individual apps", "identifier": "dev.perapp.all",
           "subtitle": "Every app in this repo, one entry per app file",
           "description": "Concatenation of apps/*.json", "website": "https://github.com/R0GUEEE/sidestore-sources",
           "tintColor": "#0A84FF", "iconURL": "https://apptesters.org/apptesters-512x512.png",
           "apps": allapps}, open(os.path.join(out_dir, "all.json"), "w"), ensure_ascii=False, indent=1)
print("wrote %d per-app sources + index.json + all.json" % written)
print("bundle IDs: %d unique, %d variants" % (len({k[0] for k in units}), len(units)))
