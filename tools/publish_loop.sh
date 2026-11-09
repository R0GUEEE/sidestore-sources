#!/bin/sh
# Resumable background publisher: keeps publishing app repos under R0GUEEE until
# docs/repos.json shows everything pushed, or the process is killed.
cd /var/minis/workspace/reposcan || exit 1
LOG=/var/minis/workspace/reposcan/docs/publish.log
while :; do
    out=$(timeout 240 nice -n 10 ionice -c 3 python3 tools/publish_repos.py --limit 6 2>&1 | grep '^done' | tail -1)
    echo "$(date '+%H:%M:%S') $out" >> "$LOG"
    case "$out" in
        done*fail=0\ total_pushed=*) ;;
        *"total_pushed=11289"*) echo "ALL DONE" >> "$LOG"; break ;;
    esac
    sleep 1
done
