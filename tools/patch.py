#!/usr/bin/env python3
"""Patch an arbitrary AltStore/SideStore source JSON in place so it decodes in
SideStore's AltStoreSource model: every versions[] entry gets an Int `size`
(unknown -> 0), dates are ISO 8601, legacy app-level version fields are lifted,
and header name/identifier are present.

usage: python3 tools/patch.py in.json out.json [--lenient]
       --lenient omits `size` where unknown instead of writing 0
"""
import json, re, sys, hashlib

BID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]*(\.[A-Za-z0-9][A-Za-z0-9\-]*)+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
STALE = "2000-01-01T00:00:00Z"

def iso(v):
    s = str(v or "").strip()
    if not DATE.match(s): return STALE
    if len(s) == 10: return s + "T00:00:00Z"
    return s if (s.endswith("Z") or "+" in s[10:] or s[10:].startswith("-")) else s + "Z"

def patch(src, lenient=False):
    apps = src.get("apps") if isinstance(src, dict) else None
    assert isinstance(apps, list), "no apps[] array"
    out, fix = [], {"versions": 0, "size_added": 0, "date_fixed": 0, "legacy_lifted": 0}
    for a in apps:
        if not isinstance(a, dict): continue
        vs = []
        if isinstance(a.get("versions"), list):
            for v in a["versions"]:
                if not isinstance(v, dict) or not v.get("downloadURL"): continue
                d0 = v.get("date")
                e = dict(v)
                e["version"] = str(v.get("version") or "unknown")
                e["date"] = iso(d0)
                if e["date"] != d0: fix["date_fixed"] += 1
                if not isinstance(e.get("localizedDescription"), str): e["localizedDescription"] = ""
                if not isinstance(e.get("size"), int):
                    if not lenient: e["size"] = 0
                    fix["size_added"] += 1
                vs.append(e)
        if not vs and a.get("downloadURL"):
            vs = [{"version": str(a.get("version") or "unknown"),
                   "date": iso(a.get("versionDate")),
                   "localizedDescription": str(a.get("versionDescription") or a.get("localizedDescription") or ""),
                   "downloadURL": a["downloadURL"]}]
            if not lenient: vs[0]["size"] = a.get("size") if isinstance(a.get("size"), int) else 0
            fix["legacy_lifted"] += 1
        if not vs: continue
        fix["versions"] += len(vs)
        b = a.get("bundleIdentifier") or a.get("bundleID")
        if not (isinstance(b, str) and BID.match(b.strip())):
            b = "synthetic.%s.%s" % (re.sub(r"[^A-Za-z0-9]+", "-", str(a.get("name") or "app"))[:24].strip("-").lower() or "app",
                                     hashlib.md5(str(vs[0]["downloadURL"]).encode()).hexdigest()[:8])
        na = dict(a)
        na["bundleIdentifier"] = b
        na["versions"] = vs
        na.setdefault("name", b); na.setdefault("developerName", ""); na.setdefault("subtitle", "")
        na.setdefault("localizedDescription", ""); na.setdefault("iconURL", ""); na.setdefault("tintColor", "#0A84FF")
        na.setdefault("screenshots", [])
        for k in ("version", "versionDate", "versionDescription", "downloadURL", "size"):
            na.pop(k, None) if k in ("downloadURL", "size") else None
        out.append(na)
    src = dict(src)
    src["name"] = str(src.get("name") or "Source")
    src["identifier"] = str(src.get("identifier") or "com.example.source")
    src["apps"] = out
    return src, fix

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = json.load(open(args[0]))
    fixed, stats = patch(src, "--lenient" in sys.argv)
    json.dump(fixed, open(args[1], "w"), ensure_ascii=False, indent=1)
    print("%s -> %s | apps %d | %s" % (args[0], args[1], len(fixed["apps"]), stats))
