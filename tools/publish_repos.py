#!/usr/bin/env python3
"""Mirror repos/<slug>/ to its own GitHub repo R0GUEEE/<repo>.

Resumable and stateful: docs/repos.json records every target repo name, its source
source file/URL, and its push state. Repos already marked pushed are skipped unless
--force is given, so an interrupted run just continues where it stopped.

usage: python3 tools/publish_repos.py [--limit N] [--force] [--slug a b c]
"""
import base64, json, os, re, subprocess, sys, time

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
repos_dir = os.path.join(root, "repos")
state_path = os.path.join(root, "docs", "repos.json")
idx = json.load(open(os.path.join(root, "apps", "index.json")))

args = sys.argv[1:]
limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
force = "--force" in args
only = args[args.index("--slug") + 1:] if "--slug" in args else []

def slugify(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()[:95] or "app"

state = json.load(open(state_path)) if os.path.exists(state_path) else {"repos": {}}
entries = {a["file"][:-5]: a for a in idx["apps"]}

def gh(*a):
    # stream outputs to /dev/null: capturing these on iSH occasionally hits MemoryError
    with open(os.devnull, "wb") as dn:
        return subprocess.run(["gh"] + list(a), stdout=dn, stderr=subprocess.PIPE)

def push(slug, repo):
    d = os.path.join(repos_dir, slug)
    git = lambda *a: subprocess.run(["git"] + list(a), cwd=d, capture_output=True,
                                    env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    # blob pushed straight through the API: no .git directory, so no state to repair
    blobs = {}
    size_hint = os.path.getsize(os.path.join(d, "apps.json"))
    for fn in ("apps.json", "README.md"):
        t0 = time.time()
        fp = os.path.join(d, fn)
        if not os.path.exists(fp): continue
        with open(fp, "rb") as f: data = f.read()
        r = subprocess.run(["gh", "api", "-X", "POST", "repos/R0GUEEE/%s/git/blobs" % repo, "-f", "encoding=base64", "-f", "content=" + base64.b64encode(data).decode()],
                           capture_output=True)
        if r.returncode != 0: return False, "blob: " + r.stderr.decode()[:120]
        blobs[fn] = json.loads(r.stdout)["sha"]
        print("    %-10s %6dB blob %.1fs" % (fn, len(data), time.time() - t0), flush=True)
    r = subprocess.run(["gh", "api", "git/trees", "-f", "base_tree=main", "-f", "tree=[]"], capture_output=True)
    body = json.dumps({"base_tree": None,
                       "tree": [{"path": k, "mode": "100644", "type": "blob", "sha": v} for k, v in blobs.items()]})
    r = subprocess.run(["gh", "api", "-X", "POST", "repos/R0GUEEE/%s/git/trees" % repo, "--input", "-"],
                       input=body.encode(), capture_output=True)
    if r.returncode != 0: return False, "tree: " + r.stderr.decode()[:120]
    tree = json.loads(r.stdout)["sha"]
    body = json.dumps({"message": "SideStore source for %s" % slug, "tree": tree, "force": True})
    r = subprocess.run(["gh", "api", "-X", "POST", "repos/R0GUEEE/%s/git/commits" % repo, "--input", "-"],
                       input=body.encode(), capture_output=True)
    if r.returncode != 0: return False, "commit: " + r.stderr.decode()[:120]
    commit = json.loads(r.stdout)["sha"]
    body = json.dumps({"force": True, "sha": commit})
    r = subprocess.run(["gh", "api", "-X", "PATCH", "repos/R0GUEEE/%s/git/refs/heads/main" % repo, "--input", "-"],
                       input=body.encode(), capture_output=True)
    if r.returncode != 0: return False, "ref: " + r.stderr.decode()[:120]
    return True, ""

todo = [s for s in entries if (not only or s in only) and (force or state["repos"].get(s, {}).get("state") != "pushed")]
if limit: todo = todo[:limit]
print("targets: %d (already pushed: %d)" % (len(todo), sum(1 for v in state["repos"].values() if v.get("state") == "pushed")), flush=True)

ok = fail = 0
for i, slug in enumerate(todo):
    e = entries[slug]
    repo = slugify(slug)
    rec = {"repo": repo, "url": "https://raw.githubusercontent.com/R0GUEEE/%s/main/apps.json" % repo,
           "source_file": e["file"], "name": e["name"], "bundleIdentifier": e["bundleIdentifier"],
           "version": e.get("version")}
    if not os.path.isdir(os.path.join(repos_dir, slug)):
        rec["state"] = "missing-tree"; state["repos"][slug] = rec; continue
    with open(os.devnull, "wb") as dn:
        exists = subprocess.run(["gh", "repo", "view", "R0GUEEE/" + repo],
                                stdout=dn, stderr=dn).returncode == 0
    if not exists:
        r = gh("api", "-X", "POST", "user/repos", "-f", "name=" + repo,
               "-f", "description=SideStore source: " + slug, "-F", "private=false", "-F", "auto_init=true")
        if r.returncode != 0:
            msg = r.stderr.decode()[:160]
            rec["state"] = "create-failed"; rec["error"] = msg
            state["repos"][slug] = rec; fail += 1
            json.dump(state, open(state_path, "w"), indent=1)
            print("create failed", repo, msg, flush=True)
            if "rate limit" in msg.lower() or "abuse" in msg.lower(): break
            continue
    good, err = push(slug, repo)
    rec["state"] = "pushed" if good else "push-failed"
    if not good: rec["error"] = err; fail += 1
    else: ok += 1
    state["repos"][slug] = rec
    if (i + 1) % 20 == 0 or not good:
        json.dump(state, open(state_path, "w"), indent=1)
        print("%5d ok=%d fail=%d %s" % (i + 1, ok, fail, repo), flush=True)
json.dump(state, open(state_path, "w"), indent=1)
print("done ok=%d fail=%d total_pushed=%d" % (ok, fail, sum(1 for v in state["repos"].values() if v["state"] == "pushed")))
