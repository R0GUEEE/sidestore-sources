#!/usr/bin/env python3
"""Validate SideStore/AltStore source JSON as SideStore would consume it."""
import json, ssl, urllib.request, urllib.error, gzip

UA = "SideStore/0.6.0 (com.SideStore.SideStore; build 1) iOS/18.0"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

CANDIDATES = [
    ("LiveContainer stable",   "https://raw.githubusercontent.com/LiveContainer/LiveContainer/main/.github/apps.json"),
    ("LiveContainer + SideStore","https://github.com/LiveContainer/LiveContainer/releases/download/nightly/apps_ss_lc.json"),
    ("LiveContainer nightly",  "https://github.com/LiveContainer/LiveContainer/releases/download/nightly/apps_nightly.json"),
    ("shplash",                "https://shplash.github.io/shplash-repo/apps.json"),
    ("AppTesters root",        "https://repository.apptesters.org"),
    ("AppTesters apps.json",   "https://repository.apptesters.org/apps.json"),
    ("CyPwn ipa",              "https://ipa.cypwn.xyz/cypwn.json"),
    ("CyPwn AltStore edition", "https://ipa.cypwn.xyz/cypwn_altstore.json"),
    ("CyPwn TrollStore",       "https://ipa.cypwn.xyz/cypwn_ts.json"),
    ("Riftys",                 "https://raw.githubusercontent.com/notrifty1/riftysrepo/refs/heads/main/reposource.json"),
    ("FrizzleM",               "https://raw.githubusercontent.com/FrizzleM/SideInstaller/raw/main/frizzlem.json"),
    ("Neoncat eSign",          "https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps_esign.json"),
    ("Neoncat AltStore",       "https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps_altstore.json"),
    ("Neoncat apps",           "https://raw.githubusercontent.com/Neoncat-OG/TrollStore-IPAs/main/apps.json"),
    ("OwO root",               "https://repo.owo.network/"),
    ("OwO apps.json",          "https://repo.owo.network/apps.json"),
    ("Altmaker",               "https://raw.githubusercontent.com/RipeStore/altmaker/main/AltMaker.json"),
    ("dsewerek general",       "https://raw.githubusercontent.com/dsewerek/dsewerek-s-source/main/general.json"),
    ("dsewerek selected",      "https://raw.githubusercontent.com/dsewerek/dsewerek-s-source/main/selected.json"),
    ("dsewerek fastsign",      "https://raw.githubusercontent.com/dsewerek/dsewerek-s-source/main/fastsign.json"),
    ("Ittz_A7aa",              "https://ittza7aa.com/repo.json"),
    ("itslevii",               "https://itslevii.dev/repo.json"),
    ("NexSideloading",         "https://raw.githubusercontent.com/NexSideloading/app-source/refs/heads/main/repo.json"),
    ("fastsign",               "https://fastsign.dev/repo.json"),
    ("Telegram local",         "file:///var/mobile/Containers/Data/Application/3602361B-8948-4A8C-A015-AF28C0AC56EE/Documents/Telegram/telegram-source.json"),
]

def fetch(url):
    if url.startswith("file://"):
        try:
            with open(url[7:], "rb") as f: return 200, f.read(), "local"
        except Exception as e:
            return -1, str(e).encode(), ""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,*/*"})
    try:
        r = urllib.request.urlopen(req, timeout=120, context=ctx); d = r.read()
        if "gzip" in (r.headers.get("Content-Encoding") or "").lower():
            try: d = gzip.decompress(d)
            except Exception: pass
        return getattr(r, "status", 200), d, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, b"", url
    except Exception as e:
        return -1, str(e).encode(), url

def check(url, body):
    """Return (fatal, warnings, info) mimicking SideStore's decoder requirements."""
    fatal, warn, info = [], [], {}
    try:
        src = json.loads(body.decode("utf-8", "replace"))
    except Exception as e:
        return ["not valid JSON (%s)" % str(e)[:60]], [], {}
    if not isinstance(src, dict):
        return ["top level is %s, SideStore requires an object" % type(src).__name__], [], {}
    for k in ("name", "identifier"):
        if not isinstance(src.get(k), str) or not src.get(k):
            fatal.append("missing/!#string header field '%s'" % k)
    apps = src.get("apps")
    if not isinstance(apps, list):
        return fatal + ["missing 'apps' array"], warn, info
    n = len(apps); ok_std = 0; ok_legacy = 0; bad = 0; legacy_example = None; bad_example = None
    for a in apps:
        if not isinstance(a, dict): bad += 1; bad_example = bad_example or "non-object entry"; continue
        std = (isinstance(a.get("bundleIdentifier"), str) and isinstance(a.get("versions"), list) and a["versions"])
        if std:
            v = a["versions"][0]
            if isinstance(v, dict) and v.get("downloadURL") and v.get("version"):
                ok_std += 1
            else:
                bad += 1; bad_example = bad_example or "app %r: version lacks downloadURL/version" % a.get("name")
            continue
        if a.get("downloadURL") and a.get("version"):
            ok_legacy += 1
            legacy_example = legacy_example or a.get("name")
        else:
            bad += 1; bad_example = bad_example or "app %r: no versions[] and no top-level downloadURL" % a.get("name")
    info.update(apps=n, standard=ok_std, legacy=ok_legacy, unusable=bad)
    if ok_std == 0 and ok_legacy > 0:
        fatal.append("100% legacy AltStore-1.x format (top-level version/downloadURL, no versions[]) — SideStore needs bundleIdentifier + versions[]")
    elif ok_std == 0:
        fatal.append("no app entry has a usable versions[] array")
    if bad and ok_std + ok_legacy:
        warn.append("%d/%d app entries have no usable install payload%s" % (bad, n, " (e.g. %s)" % bad_example if bad_example else ""))
    if ok_legacy and ok_std:
        warn.append("%d/%d apps only in legacy format (will be dropped)" % (ok_legacy, n))
    if not src.get("iconURL"): warn.append("no iconURL header")
    return fatal, warn, info

fails = []
print(f"{'SOURCE':26}{'HTTP':>6}{'BYTES':>11}  {'APPS':>6}{'STD':>7}{'LEGACY':>7}{'BAD':>6}  VERDICT")
print("-" * 118)
for label, url in CANDIDATES:
    st, body, final = fetch(url)
    if st < 200 or st >= 300 or not body:
        print(f"{label:26}{st:>6}{'':>11}  {'':>6}{'':>7}{'':>7}{'':>6}  DEAD -> {body[:60].decode('utf-8','replace')}")
        fails.append((label, url, "HTTP %s" % st)); continue
    fatal, warn, info = check(url, body)
    verdict = "OK" if not fatal else "FAIL: " + "; ".join(fatal)
    print(f"{label:26}{st:>6}{len(body):>11}  {info.get('apps',0):>6}{info.get('standard',0):>7}{info.get('legacy',0):>7}{info.get('unusable',0):>6}  {verdict}")
    for w in warn:
        print(f"{'':26}{'  ! '+w}")
    if fatal:
        fails.append((label, url, "; ".join(fatal)))

print("\n%d/%d dead or incompatible." % (len(fails), len(CANDIDATES)))
