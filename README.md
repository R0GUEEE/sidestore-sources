# sidestore-sources

Every upstream source I could reach — including the ones that still publish the legacy
AltStore 1.x / eSign layout — converted into the format SideStore actually parses.

SideStore reads `name`, `identifier`, `apps[].bundleIdentifier` and
`apps[].versions[].downloadURL`. Fix one field and a broken source starts working.
`tools/convert.py` fixes all of them.

## Add to SideStore (`Sources → +`)

**Everything in one source:**

```
https://raw.githubusercontent.com/R0GUEEE/sidestore-sources/main/sources/merged.json
```
9,484 apps, deduplicated by bundle ID.

Per-upstream files (29) are in [`sources/`](sources) — browse them at
[docs/sources.html](docs/sources.html):

| Source | Apps | File |
|---|---|---|
| dsewerek fastsign (organized) | 8,400 | `dsewerek-fastsign.json` |
| dsewerek general | 1,959 | `dsewerek-general.json` |
| fastsign.dev | 3,725 | `fastsign.json` |
| AppTesters | 812 | `apptesters.json` |
| ittza7aa | 726 | `ittza7aa.json` |
| AltMaker (RipeStore) | 445 | `altmaker.json` |
| Neoncat-OG | 286 | `neoncat.json` |
| CyPwn (native + TrollStore) | 180 + 119 | `cypwn*.json` |
| swaggyP36000 | 109 | `swaggy.json` |
| Riftys | 36 | `riftys.json` |
| QuantumSource++ | 35 | `quantumsource.json` |
| OwO | 29 | `owo.json` |
| SideStore community | 23 | `sidestore-community.json` |
| SideStore connect | 8 | `sidestore-connect.json` |
| NexSideloading | 7 | `nexsideloading.json` |
| itslevii | 6 | `itslevii.json` |
| Provenance | 4 | `provenance.json` |
| FrizzleM, shplash, StikDebug, Geode, LiveContainer ×3, SideStore official, dsewerek selected | 1–2 each | — |

## What the conversion does

- **legacy → `versions[]`** — app-level `version` / `versionDate` / `downloadURL` / `size`
  move into a `versions` array; multi-version sources are sorted newest-first and capped at 3.
- **dates normalized to ISO 8601** — `2026-11-08` → `2026-11-08T00:00:00Z`; a date that can't be
  parsed sorts last instead of silently winning the dedupe.
- **bundle IDs** — entries with a non reverse-DNS ID (Amperwave hashes, `hello-weather-app`,
  `cypwn.AppDB_1.1.5.1.1.5`) get a stable `synthetic.<name>.<hash>` placeholder so the entry
  remains listed; entries with a `null` ID and no app payload are dropped.
- **dedupe** — one app per bundle ID, newest version wins (AppTesters: 10,084 rows → 812 apps,
  9,272 duplicates collapsed; fastsign 16,945 → 3,725; ittza7aa 1,794 → 726).
- **headers** — sources missing `identifier` (all three dsewerek files) get one; missing icons,
  subtitles and tint colors are filled in.
- legacy keys (`version`, `versionDate`, `versionDescription`) are re-emitted next to `versions[]`
  for clients that still look for them.

## Not convertible

| Input | Why |
|---|---|
| `file:///var/mobile/Containers/…/telegram-source.json` | an iOS app container path — not readable by the sandbox, and not a URL SideStore can load. Re-export the file to Files, then host it (the converter takes any http(s) URL; add it to `upstreams.json`). |
| `https://repos.yattee.stream/alt/apps.json` | 404 upstream |
| `https://theodyssey.dev/altstore/odysseysource.json` | 404 upstream |
| `https://ftrepo.xyz/apps.json` | 530 upstream |
| `https://alt.crystall1ne.dev`, `https://rickowens.su/repo.json` | unreachable / 403 |

## Layout

```
sources/            converted source JSON (served straight to SideStore)
upstreams.json      registry: one entry per upstream URL → output file
docs/index.html     audit of the original 16 URLs
docs/sources.html   index of every converted file with its raw URL
docs/catalog.json   machine-readable list of the same
tools/convert.py    fetch + normalize (the converter)
tools/aggregate.py  rebuild sources/merged.json + docs/catalog.json
tools/ja.py         validate a URL list (stdin, one per line)
tools/fcheck.py     validate converted files
tools/verify.py     compatibility matrix against SideStore's decode rules
tools/discover.py   walk a GitHub repo tree and validate every .json
```

Regenerate everything:

```sh
python3 tools/convert.py      # all upstreams → sources/*.json
python3 tools/aggregate.py    # → sources/merged.json
python3 tools/fcheck.py sources/*.json
```

These files only point at upstream download URLs — no IPAs are mirrored here.
