#!/usr/bin/env python3
"""Strict schema audit against SideStore's AltStoreSource Codable models.
Reports every file/field that would raise a DecodingError, with a sample path."""
import json, glob, sys
def audit(path):
    o = json.load(open(path)); bad = []
    for k in ("name", "identifier"):
        if not isinstance(o.get(k), str): bad.append(("%s" % k, "missing header string"))
    for i, a in enumerate(o.get("apps", [])):
        for k in ("name", "bundleIdentifier"):
            if not isinstance(a.get(k), str): bad.append(("apps[%d].%s" % (i, k), "missing string"))
        if not isinstance(a.get("versions"), list) or not a["versions"]:
            bad.append(("apps[%d].versions" % i, "missing/empty")); continue
        for j, v in enumerate(a["versions"]):
            p = "apps[%d].versions[%d]" % (i, j)
            for k in ("version", "date", "downloadURL"):
                if not isinstance(v.get(k), str): bad.append((p + "." + k, "missing string"))
            if not isinstance(v.get("size"), int): bad.append((p + ".size", "missing Int (SideStore decodes non-optional)"))
    return bad
if __name__ == "__main__":
    rc = 0
    for f in sorted(sys.argv[1:] or glob.glob("sources/*.json")):
        b = audit(f)
        rc |= 1 if b else 0
        print("%-38s %s" % (f.split("/")[-1], "OK" if not b else "%d problems, e.g. %s (%s)" % (len(b), b[0][0], b[0][1])))
    sys.exit(rc)
