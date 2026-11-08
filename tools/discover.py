#!/usr/bin/env python3
"""Discover SideStore/AltStore source JSON URLs across a list of repos.
Strategy per repo: git recursive tree -> candidate *.json -> validate as source
-> if none valid, read README/HTML for cited source URLs -> validate those."""
import json, ssl, re, sys, urllib.request, urllib.error, gzip

UA = "SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
GH = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

REPOS = [l.strip() for l in """
LiveContainer/LiveContainer
notrifty1/riftysrepo
FrizzleM/SideInstaller
Neoncat-OG/TrollStore-IPAs
RipeStore/altmaker
dsewerek/dsewerek-s-source
NexSideloading/app-source
shplash/shplash-repo
OwO-Network/Repo
ittza7aa/repo
itslevii-dev/repo
""".split() if l.strip()]

def http(url, headers=GH, timeout=60):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout, context=ctx)
        d = r.read()
        if "gzip" in (r.headers.get("Content-Encoding") or "").lower():
            try: d = gzip.decompress(d)
            except Exception: pass
        return getattr(r, "status", 200), d
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return -1, b""

SKIP = re.compile(r"(Contents\.json$|package(-lock)?\.json$|tsconfig|\.vscode/|node_modules/|Pods/|locale|strings\.json$|\.xcassets)", re.I)

def validate(url):
    st, body = http(url, {"User-Agent": UA}, 180)
    if st != 200 or not body: return ("HTTP %s" % st), None
    try: src = json.loads(body.decode("utf-8", "replace"))
    except Exception: return "NOT JSON", None
    if not isinstance(src, dict): return "json %s" % type(src).__name__, None
    if not (isinstance(src.get("name"), str) and isinstance(src.get("identifier"), str)):
        return "missing header fields", None
    apps = src.get("apps")
    if not isinstance(apps, list): return "no apps[]", None
    std = [a for a in apps if isinstance(a, dict) and isinstance(a.get("versions"), list) and a["versions"]
           and isinstance(a["versions"][0], dict) and a["versions"][0].get("downloadURL")]
    leg = [a for a in apps if isinstance(a, dict) and a.get("downloadURL") and a not in std]
    if std and not leg: return "OK (%d apps)" % len(std), src
    if std and leg: return "PARTIAL (%d std / %d legacy of %d)" % (len(std), len(leg), len(apps)), src
    return "LEGACY-ONLY (%d apps, no versions[])" % len(leg), src

def tree(repo):
    for br in ("main", "master"):
        st, d = http("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (repo, br))
        if st == 200:
            j = json.loads(d)
            return br, [t["path"] for t in j.get("tree", []) if t.get("type") == "blob"]
    return None, []

for repo in REPOS:
    print("\n################ %s" % repo)
    br, paths = tree(repo)
    if not br:
        print("  no tree (repo missing/private/renamed)"); continue
    print("  branch %s, %d files" % (br, len(paths)))
    cites = [p for p in paths if re.search(r"(README|SOURCE|repo|source|index\.html)", p, re.I) and p.count("/") <= 2][:4]
    cands = []
    for p in paths:
        if not p.lower().endswith(".json") or SKIP.search(p): continue
        raw = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, br, p)
        status, _ = validate(raw)
        print("   %-52s %s" % (p, status))
        cands.append((p, raw, status))
    if not any(s.startswith(("OK", "PARTIAL")) for _, _, s in cands):
        for c in cites:
            raw = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, br, c)
            st, body = http(raw)
            if st != 200: continue
            txt = body.decode("utf-8", "replace")
            found = set(re.findall(r'https?://[^\s"\'<>()\]]+\.json', txt))
            found |= {"https://raw.githubusercontent.com/%s/%s/%s" % (repo, br, m) for m in re.findall(r'["\'(]([^"\'\s]+\.json)["\')]', txt)}
            for f in sorted(found)[:12]:
                if "raw.githubusercontent.com/%s/" % repo in f and f.endswith("/"+c): continue
                status, _ = validate(f)
                if "HTTP" != status: print("   [cited in %s] %-60s %s" % (c, f[:150], status))
