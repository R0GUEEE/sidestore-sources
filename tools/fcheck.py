#!/usr/bin/env python3
import json, sys
BID = __import__("re").compile(r"^[A-Za-z0-9][A-Za-z0-9\-]*(\.[A-Za-z0-9][A-Za-z0-9\-]*)+$")
for p in sys.argv[1:]:
    o = json.load(open(p))
    apps = o["apps"]
    std = [a for a in apps if a.get("versions") and a["versions"][0].get("downloadURL")]
    leg = [a for a in apps if a.get("downloadURL") and not (a.get("versions") and a["versions"][0].get("downloadURL"))]
    bid_ok = [a for a in std if BID.match(a.get("bundleIdentifier") or "")]
    print(f"{p}: apps={len(apps)} versions[]={len(std)} legacy={len(leg)} valid bundleID={len(bid_ok)} header=name+identifier={bool(o.get('name')) and bool(o.get('identifier'))}")
