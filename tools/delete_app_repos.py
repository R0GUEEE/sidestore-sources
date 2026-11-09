#!/usr/bin/env python3
"""Delete the per-app repos R0GUEEE/<slug> recorded in docs/repos.json.

Only names recorded as published app repos are touched; anything absent from that state
file (sidestore-sources and unrelated repos) can never be hit. Resumable: deleted entries
are marked in docs/repos.json.

usage: python3 tools/delete_app_repos.py [--dry-run] [--limit N]
"""
import json, os, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
state_path = os.path.join(root, "docs", "repos.json")
state = json.load(open(state_path))
args = sys.argv[1:]
dry = "--dry-run" in args
limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
PROTECTED = {"sidestore-sources"}

targets = [v["repo"] for v in state["repos"].values()
           if v.get("state") == "pushed" and v.get("repo") not in PROTECTED]
if limit: targets = targets[:limit]
print("targets: %d%s" % (len(targets), " (dry run)" if dry else ""), flush=True)

ok = fail = 0
for i, repo in enumerate(targets):
    if dry:
        print(" would delete", repo)
        ok += 1
        continue
    with open(os.devnull, "wb") as dn:
        r = subprocess.run(["gh", "repo", "delete", "R0GUEEE/" + repo, "--yes"],
                           stdout=dn, stderr=subprocess.PIPE)
    if r.returncode == 0:
        ok += 1
        for v in state["repos"].values():
            if v.get("repo") == repo:
                v["state"] = "deleted"
    else:
        fail += 1
        print("delete failed", repo, r.stderr.decode()[:100], flush=True)
    if (i + 1) % 25 == 0:
        json.dump(state, open(state_path, "w"), indent=1)
        print("%5d ok=%d fail=%d" % (i + 1, ok, fail), flush=True)

json.dump(state, open(state_path, "w"), indent=1)
print("done deleted=%d failed=%d" % (ok, fail))
