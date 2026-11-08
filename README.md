# sidestore-sources

SideStore-native source JSON, rebuilt from repositories that still publish the legacy
AltStore 1.x / eSign layout. Plus the tooling that produces and validates them.

SideStore parses `name`, `identifier`, `apps[].bundleIdentifier` and
`apps[].versions[].downloadURL`. Sources that put `version` / `versionDate` / `downloadURL`
at the app level parse to an empty app list, so they import "successfully" and then show
nothing. Everything in `sources/` is in the `versions[]` form.

## Add to SideStore

`SideStore → Sources → +` and paste one of:

| Source | URL | Apps |
|---|---|---|
| Everything, merged | `https://raw.githubusercontent.com/R0GUEEE/sidestore-sources/main/sources/merged.json` | 1,230 |
| AppTesters (AppStore apps) | `https://raw.githubusercontent.com/R0GUEEE/sidestore-sources/main/sources/mirror-apptesters.json` | 785 |
| Neoncat-OG | `https://raw.githubusercontent.com/R0GUEEE/sidestore-sources/main/sources/mirror-neoncat.json` | 286 |
| CyPwn (TrollStore-era builds) | `https://raw.githubusercontent.com/R0GUEEE/sidestore-sources/main/sources/mirror-cypwn.json` | 130 |

## Upstream URLs that work as-is

| Repo | URL | Apps |
|---|---|---|
| LiveContainer (nightly) | `https://github.com/LiveContainer/LiveContainer/releases/download/nightly/apps_nightly.json` | 1 |
| LiveContainer + SideStore | `https://raw.githubusercontent.com/LiveContainer/LiveContainer/main/.github/apps_ss_lc.json` | 1 |
| shplash | `https://shplash.github.io/shplash-repo/apps.json` | 2 |
| AltMaker (RipeStore) | `https://raw.githubusercontent.com/RipeStore/altmaker/main/AltMaker.json` | 445 |
| itslevii | `https://itslevii.dev/repo.json` | 6 |
| NexSideloading | `https://raw.githubusercontent.com/NexSideloading/app-source/refs/heads/main/repo.json` | 7 |
| fastsign | `https://fastsign.dev/repo.json` | 16,945 |
| Neoncat-OG (native) | `https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps.json` | 347 |
| CyPwn (native) | `https://ipa.cypwn.xyz/cypwn_altstore.json` | 180 |
| FrizzleM | `https://raw.githubusercontent.com/FrizzleM/SideInstaller/main/frizzlem.json` | 2 |
| SideStore official | `https://apps.sidestore.io` | 6 |
| SideStore community | `https://community-apps.sidestore.io/sidecommunity.json` | 23 |
| SideStore connect | `https://connect.sidestore.io/apps.json` | 8 |
| QuantumSource++ | `https://quarksources.github.io/quantumsource++.json` | 35 |
| swaggyP36000 | `https://raw.githubusercontent.com/swaggyP36000/TrollStore-IPAs/main/apps.json` | 133 |

## Why the rest of the list is here

| Upstream | Problem |
|---|---|
| `https://repository.apptesters.org` | 10,084 apps, 100% legacy layout → `sources/mirror-apptesters.json` |
| `https://ipa.cypwn.xyz/cypwn.json` | legacy + 50 bogus bundle IDs (hex hashes) → use `cypwn_altstore.json` |
| `https://ipa.cypwn.xyz/cypwn_ts.json` | legacy, no native twin → `sources/mirror-cypwn.json` |
| `https://repo.owo.network/` | legacy only → folded into `merged.json` |
| `Neoncat-OG/.../apps_esign.json` | 1,988 legacy entries → use `apps.json`, or `sources/mirror-neoncat.json` |
| `notrifty1/riftysrepo` | legacy, and 36/43 download URLs point at dead Heroku dynos |
| `ittza7aa.com/repo.json` | 1,794 entries for 341 bundle IDs, 704 with `bundleIdentifier: null` |
| `dsewerek/dsewerek-s-source` | valid apps but no `identifier` header — add it and it loads (1,961 apps) |
| `LiveContainer/.../nightly/apps_ss_lc.json` | 404, it is only in the git tree |

## Layout

```
sources/            generated source JSON (served straight to SideStore)
docs/index.html     audit report for the 16 upstream URLs
tools/ja.py         validate a URL list (stdin, one per line)
tools/fcheck.py     validate local files
tools/merge.py      legacy -> versions[] normalizer + per-source generation
tools/verify.py     compatibility matrix against SideStore's decode rules
tools/discover.py   walk a GitHub repo tree and validate every .json
```

Regenerate:

```sh
python3 tools/merge.py                      # rewrites sources/*.json
python3 tools/fcheck.py sources/*.json
```

Merging keeps the newest version per `bundleIdentifier`, drops entries without a
conforming bundle ID (SideStore looks apps up by bundle ID), and caps history at three
versions per app.

These files only point at upstream download URLs — IPAs are not mirrored here.
