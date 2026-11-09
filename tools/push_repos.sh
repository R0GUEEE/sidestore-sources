#!/bin/bash
# Push each repos/<slug>/ tree to its own GitHub repo R0GUEEE/<slug>.
# Creates the repo when missing, idempotent otherwise.
# usage: push_repos.sh <slug> [slug...]   (no args = every directory)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

slugify() {
    python3 - "$1" <<'PY'
import re, sys
s = re.sub(r"[^A-Za-z0-9]+", "-", sys.argv[1]).strip("-").lower()
print(s[:95] or "app")
PY
}

list=("$@")
if [ ${#list[@]} -eq 0 ]; then mapfile -t list < <(ls repos); fi

ok=0; fail=0
for n in "${list[@]}"; do
    d="repos/$n"
    [ -d "$d" ] || { echo "missing $d"; fail=$((fail+1)); continue; }
    repo="$(slugify "$n")"
    if ! gh repo view "R0GUEEE/$repo" >/dev/null 2>&1; then
        gh api -X POST user/repos \
            -f name="$repo" -f description="SideStore source: $n" -F private=false -F auto_init=true \
            >/dev/null 2>&1 || { echo "create failed: $repo"; fail=$((fail+1)); continue; }
    fi
    (
        cd "$d" || exit 1
        git init -q 2>/dev/null
        git add -A
        if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
            git -c user.name=R0GUEEE -c user.email=roguetm@icloud.com commit -q -m "SideStore source for $n"
        fi
        git -c credential.helper= push -q -f "https://x-access-token:${GITHUB_TOKEN}@github.com/R0GUEEE/${repo}.git" HEAD:main
    ) || { echo "push failed: $repo"; fail=$((fail+1)); continue; }
    ok=$((ok+1))
done
echo "pushed ok=$ok fail=$fail"
