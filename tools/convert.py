#!/usr/bin/env python3
"""Convert every upstream source listed in upstreams.json into a SideStore-native
source, one output file per upstream.

Rules (SideStore's Source decoding):
  header: name (str), identifier (str), subtitle/description/iconURL/tintColor/website
  apps[]: bundleIdentifier (real reverse-DNS), name, developerName, iconURL,
          localizedDescription, subtitle, screenshots, versions[]
  versions[]: version, date, downloadURL, size, localizedDescription
  legacy (app-level version/versionDate/downloadURL) is lifted into versions[]
  entries without a conforming bundleIdentifier are dropped (SideStore indexes by it)
  duplicate bundle IDs are collapsed, newest version first (3 history entries max)
"""
import json, os, re, ssl, sys, datetime, urllib.request, urllib.error, gzip

UA = "SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
BID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]*(\.[A-Za-z0-9][A-Za-z0-9\-]*)+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
STALE = "2000-01-01T00:00:00Z"   # unknown date: sorts last, never wins a dedupe

def fetch(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"}),
                                   timeout=600, context=ctx)
        d = r.read()
        if "gzip" in (r.headers.get("Content-Encoding") or "").lower():
            try: d = gzip.decompress(d)
            except Exception: pass
        return json.loads(d.decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s" % e.code)
    except Exception as e:
        raise RuntimeError(str(e)[:80])

def iso_date(v):
    s = str(v or "").strip()
    if not DATE.match(s): return STALE
    if len(s) == 10: return s + "T00:00:00Z"
    return s if (s.endswith("Z") or "+" in s[10:] or s[10:].startswith("-")) else s + "Z"

def norm_versions(a):
    vs = []
    if isinstance(a.get("versions"), list):
        for v in a["versions"]:
            if isinstance(v, dict) and v.get("downloadURL") and v.get("version"):
                e = {"version": str(v["version"]), "date": iso_date(v.get("date")),
                     "localizedDescription": str(v.get("localizedDescription") or "")[:4000],
                     "downloadURL": v["downloadURL"]}
                if isinstance(v.get("size"), int): e["size"] = v["size"]
                elif isinstance(a.get("size"), int) and len(a["versions"]) == 1: e["size"] = a["size"]
                vs.append(e)
    if not vs and a.get("downloadURL") and a.get("version"):
        e = {"version": str(a["version"]), "date": iso_date(a.get("versionDate") or a.get("fullDate")),
             "localizedDescription": str(a.get("versionDescription") or a.get("localizedDescription") or "")[:4000],
             "downloadURL": a["downloadURL"]}
        if isinstance(a.get("size"), int): e["size"] = a["size"]
        vs.append(e)
    # newest first, dedupe by version string
    seen, out = set(), []
    for v in sorted(vs, key=lambda x: x["date"], reverse=True):
        if v["version"] in seen: continue
        seen.add(v["version"]); out.append(v)
    return out[:3]

def vs_ok(a):
    return bool(norm_versions(a))

def norm_app(a):
    if not isinstance(a, dict): return None
    bid = a.get("bundleIdentifier") or a.get("bundleID")
    vs = norm_versions(a)
    if not vs: return None
    shots = a.get("screenshots") or a.get("screenshotURLs") or []
    if isinstance(shots, str): shots = [shots]
    real = isinstance(bid, str) and BID.match(bid.strip())
    if not real and not vs: return None
    app = {
        "bundleIdentifier": bid.strip() if real else "synthetic.%s.%s" % (
            re.sub(r"[^A-Za-z0-9]+", "-", str(a.get("name") or "app"))[:24].strip("-").lower() or "app",
            __import__("hashlib").md5(str(vs[0]["downloadURL"]).encode()).hexdigest()[:8]),
        "name": str(a.get("name") or bid)[:120],
        "developerName": str(a.get("developerName") or "")[:120],
        "subtitle": str(a.get("subtitle") or "")[:200],
        "localizedDescription": str(a.get("localizedDescription") or "")[:8000],
        "iconURL": str(a.get("iconURL") or a.get("icon") or ""),
        "tintColor": a.get("tintColor") or "#0A84FF",
        "screenshots": [s for s in shots if isinstance(s, str) and s.startswith("http")][:5],
        "versions": vs,
    }
    if isinstance(a.get("appPermissions"), dict): app["appPermissions"] = a["appPermissions"]
    if isinstance(a.get("version"), str) and a["version"].lower() not in ("", "latest", "last", "unknown"):
        app["version"] = a["version"]
    if isinstance(a.get("versionDate"), str) and DATE.match(a["versionDate"]):
        app["versionDate"] = iso_date(a["versionDate"])
    if isinstance(a.get("versionDescription"), str) and a["versionDescription"]:
        app["versionDescription"] = a["versionDescription"][:8000]
    return app

def convert(cfg):
    src = fetch(cfg["url"]) if cfg.get("url") else []
    if not isinstance(src, dict) or not isinstance(src.get("apps"), list):
        raise RuntimeError("not a source object")
    merged, dropped_bid, dropped_empty, dupes = {}, 0, 0, 0
    for a in src["apps"]:
        n = norm_app(a)
        if not n:
            if isinstance(a, dict) and vs_ok(a): dropped_empty += 1
            else: dropped_bid += 1
            continue
        cur = merged.get(n["bundleIdentifier"])
        if cur:
            dupes += 1
            if n["versions"][0]["date"] > cur["versions"][0]["date"]: merged[n["bundleIdentifier"]] = n
        else:
            merged[n["bundleIdentifier"]] = n
    out = {
        "name": cfg["name"], "identifier": cfg["identifier"],
        "subtitle": cfg.get("subtitle", ""), "description": cfg.get("description", ""),
        "website": cfg.get("website", ""), "tintColor": cfg.get("tintColor", "#0A84FF"),
        "iconURL": cfg.get("iconURL", ""),
        "apps": sorted(merged.values(), key=lambda x: x["name"].lower()),
    }
    stats = dict(upstream=len(src["apps"]), kept=len(out["apps"]), no_bundle_id=dropped_bid,
                 no_versions=dropped_empty, duplicates=dupes)
    return out, stats

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    reg = json.load(open(os.path.join(root, "upstreams.json")))
    only = sys.argv[1:]
    report = []
    for cfg in reg["sources"]:
        if only and cfg["out"] not in only: continue
        try:
            out, st = convert(cfg)
        except Exception as e:
            print("  ! %-26s %s" % (cfg["out"], e)); report.append({"file": cfg["out"], "error": str(e)}); continue
        p = os.path.join(root, "sources", cfg["out"])
        with open(p, "w") as f: json.dump(out, f, ensure_ascii=False, indent=1)
        print("  %-26s %6d upstream -> %5d apps  (no bid %d, no ver %d, dupes %d)"
              % (cfg["out"], st["upstream"], st["kept"], st["no_bundle_id"], st["no_versions"], st["duplicates"]))
        report.append(dict(file=cfg["out"], name=out["name"], **st))
    json.dump({"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "results": report}, open(os.path.join(root, "docs", "conversion.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
