#!/usr/bin/env python3
"""Push very many tiny app repos fast: prefer mirroring to a GitLab account
(unlimited projects, same raw URL shape) when GITLAB_TOKEN is set, otherwise
fan out across GitHub repos serially via tools/publish_repos.py.

usage:
  GITLAB_TOKEN=... python3 tools/publish_bulk.py gitlab [--limit N]
  python3 tools/publish_bulk.py github [--limit N]
"""
import base64, json, os, sys, threading, queue, time, urllib.request, urllib.error

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
idx = json.load(open(os.path.join(root, "apps", "index.json")))
repos_dir = os.path.join(root, "repos")
state_path = os.path.join(root, "docs", "repos.json")
state = json.load(open(state_path)) if os.path.exists(state_path) else {"repos": {}}

def http(method, url, token, body=None, headers=None):
    h = {"PRIVATE-TOKEN": token, "Content-Type": "application/json"}
    if headers: h.update(headers)
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers=h, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")

def gitlab_one(slug, token, ns):
    d = os.path.join(repos_dir, slug)
    if not os.path.isdir(d): return False, "missing tree"
    name = slug
    try:
        proj = http("GET", "https://gitlab.com/api/v4/projects/%s%%2F%s" % (ns, name), token)
        pid = proj["id"]
    except urllib.error.HTTPError as e:
        if e.code != 404: return False, "lookup %s" % e.code
        try:
            proj = http("POST", "https://gitlab.com/api/v4/projects", token,
                        {"name": name, "path": name, "visibility": "public",
                         "description": "SideStore source: " + slug})
        except urllib.error.HTTPError as e2:
            return False, "create %s %s" % (e2.code, e2.read()[:80])
        pid = proj["id"]
    actions = []
    for fn in ("apps.json", "README.md"):
        fp = os.path.join(d, fn)
        if not os.path.exists(fp): continue
        actions.append({"action": "update" if False else "create", "file_path": fn,
                        "content": open(fp, encoding="utf-8").read()})
    try:
        http("POST", "https://gitlab.com/api/v4/projects/%d/repository/commits" % pid, token,
             {"branch": "main", "commit_message": "SideStore source for " + slug, "actions": actions})
    except urllib.error.HTTPError as e:
        # file already exists → switch to update and retry once
        try:
            http("POST", "https://gitlab.com/api/v4/projects/%d/repository/commits" % pid, token,
                 {"branch": "main", "commit_message": "SideStore source for " + slug,
                  "actions": [{**a, "action": "update"} for a in actions]})
        except urllib.error.HTTPError as e2:
            return False, "commit %s %s" % (e2.code, e2.read()[:80])
    return True, ""

def bulk_gitlab(token, limit):
    ns = os.environ.get("GITLAB_NS") or http("GET", "https://gitlab.com/api/v4/user", token)["username"]
    todo = [a["file"][:-5] for a in idx["apps"] if state["repos"].get(a["file"][:-5], {}).get("state") != "pushed"]
    if limit: todo = todo[:limit]
    print("gitlab ns=%s targets=%d" % (ns, len(todo)), flush=True)
    q = queue.Queue(); [q.put(t) for t in todo]
    results = {"ok": 0, "fail": 0, "errs": []}
    lock = threading.Lock()
    def worker():
        while True:
            try: slug = q.get_nowait()
            except queue.Empty: return
            good, err = gitlab_one(slug, token, ns)
            with lock:
                if good:
                    results["ok"] += 1
                    state["repos"].setdefault(slug, {})["state"] = "pushed"
                    entry = next(a for a in idx["apps"] if a["file"][:-5] == slug)
                    state["repos"][slug].update({
                        "repo": slug, "host": "gitlab",
                        "url": "https://gitlab.com/%s/%s/-/raw/main/apps.json" % (ns, slug),
                        "name": entry["name"], "bundleIdentifier": entry["bundleIdentifier"],
                        "version": entry.get("version"), "source_file": entry["file"]})
                else:
                    results["fail"] += 1
                    results["errs"].append((slug, err))
                if (results["ok"] + results["fail"]) % 25 == 0:
                    json.dump(state, open(state_path, "w"), indent=1)
                    print("  ok=%d fail=%d" % (results["ok"], results["fail"]), flush=True)
    ts = [threading.Thread(target=worker) for _ in range(int(os.environ.get("THREADS", "8")))]
    [t.start() for t in ts]; [t.join() for t in ts]
    json.dump(state, open(state_path, "w"), indent=1)
    print("done ok=%d fail=%d" % (results["ok"], results["fail"]))
    for s, e in results["errs"][:5]: print("  ", s, e)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "gitlab"
    lim = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    if mode == "gitlab":
        tok = os.environ.get("GITLAB_TOKEN")
        if not tok:
            print("GITLAB_TOKEN not set — create one at https://gitlab.com/-/user_settings/personal_access_tokens (scope: api)")
            sys.exit(2)
        bulk_gitlab(tok, lim)
    else:
        os.execvp("python3", ["python3", os.path.join(here, "publish_repos.py")] +
                  (["--limit", str(lim)] if lim else []))
