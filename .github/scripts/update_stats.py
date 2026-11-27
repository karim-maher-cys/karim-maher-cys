#!/usr/bin/env python3
"""Regenerate the self-hosted GitHub stats cards from public GitHub data.
Run weekly by .github/workflows/update-stats.yml. Uses only the standard library.
HTB numbers are not public, so htb-card.svg is intentionally not touched.
"""
import json
import re
import subprocess
import urllib.request
from datetime import date, timedelta

USER = "karim-maher-cys"


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "stats-updater"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


COMMON_STYLE = (
    ".c{animation:ci .8s cubic-bezier(.2,.7,.3,1) both;animation-delay:var(--d,0s)}"
    "@keyframes ci{0%{transform:translateY(10px);opacity:0}100%{transform:translateY(0);opacity:1}}"
    ".sh{animation:shm 6s linear infinite}"
    "@keyframes shm{0%{transform:translateX(-440px)}100%{transform:translateX(440px)}}"
    ".br{animation:bp 3.6s ease-in-out infinite}"
    "@keyframes bp{0%,100%{stroke-opacity:.5}50%{stroke-opacity:1}}"
    ".num{font-family:Verdana,Geneva,sans-serif;font-size:26px;font-weight:bold;fill:#ffffff}"
    ".cap{font-family:Consolas,Menlo,monospace;font-size:10.5px;fill:#8f95a0;letter-spacing:1px}"
    ".ttl{font-family:Consolas,Menlo,monospace;font-size:11px;fill:#9a9a9a;letter-spacing:2px}"
    ".lbl{font-family:Verdana,Geneva,sans-serif;font-size:13px;fill:#e8e8e8}"
    ".pct{font-family:Consolas,Menlo,monospace;font-size:11px;fill:#8f95a0}"
)

DEFS = (
    '<defs>'
    '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#2b2f36"/><stop offset="1" stop-color="#14161a"/></linearGradient>'
    '<linearGradient id="hl" x1="0" y1="0" x2="1" y2="0">'
    '<stop offset="0" stop-color="#ffffff" stop-opacity="0"/>'
    '<stop offset="0.5" stop-color="#ffffff" stop-opacity=".55"/>'
    '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>'
    '<linearGradient id="red" x1="0" y1="0" x2="1" y2="0">'
    '<stop offset="0" stop-color="#a02020"/><stop offset="1" stop-color="#d63a3a"/></linearGradient>'
    '<pattern id="dgrid" width="18" height="18" patternUnits="userSpaceOnUse">'
    '<circle cx="1" cy="1" r="1" fill="#ffffff" fill-opacity="0.05"/></pattern>'
    '<clipPath id="cp"><rect width="440" height="{h}" rx="14"/></clipPath>'
    "</defs>"
)


def frame(h, inner):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="440" height="{h}" viewBox="0 0 440 {h}">'
        f"<style>{COMMON_STYLE}</style>{DEFS.format(h=h)}"
        f'<g class="c"><rect width="440" height="{h}" rx="14" fill="url(#bg)"/>'
        f'<rect width="440" height="{h}" rx="14" fill="url(#dgrid)"/>'
        f'<g clip-path="url(#cp)"><rect class="sh" x="0" y="0" width="120" height="{h}" fill="url(#hl)" opacity="0.10" transform="skewX(-18)"/></g>'
        f'<rect class="br" x="0.5" y="0.5" width="439" height="{h-1}" rx="14" fill="none" stroke="#4a4f58"/>'
        f'<rect x="0" y="20" width="3" height="{h-40}" rx="1.5" fill="#a02020"/>'
        f"{inner}</g></svg>"
    )


def overview_card(repos, active_days, since):
    cols = [(repos, "PUBLIC REPOS"), (active_days, "ACTIVE DAYS (12M)"), (since.split()[-1], "MEMBER SINCE " + since.split()[0])]
    cells = ""
    for (val, cap), x in zip(cols, (40, 180, 315)):
        cells += f'<text class="num" x="{x}" y="74">{val}</text><text class="cap" x="{x}" y="96">{cap}</text>'
    return frame(112, f'<text class="ttl" x="40" y="36">GITHUB OVERVIEW</text>{cells}')


def langs_card(langs):
    rows = ""
    y = 48
    maxw = 180
    top = langs[0][1]
    for name, pct in langs:
        w = max(8, round(maxw * pct / top))
        rows += (
            f'<text class="lbl" x="40" y="{y}">{name}</text>'
            f'<rect x="200" y="{y-10}" width="{maxw}" height="9" rx="4.5" fill="#22252b" stroke="#3d424b" stroke-width="1"/>'
            f'<rect x="200" y="{y-10}" width="{w}" height="9" rx="4.5" fill="url(#red)"/>'
            f'<text class="pct" x="432" y="{y}" text-anchor="end">{pct}%</text>'
        )
        y += 27
    return frame(112, f'<text class="ttl" x="40" y="30">TOP LANGUAGES</text>{rows}')


def streak_card(current, longest, asof):
    flame = (
        '<g transform="translate(28,44) scale(1.15)">'
        '<g transform="translate(-2,-4) scale(1.9)">'
        '<path d="M12 1c1 4.5-5 6.5-5 12a5 5 0 0 0 10 0c0-2-1-3.4-2-4.6-.4 1.6-1.2 2.6-2.4 3.2C13.4 8.6 14.5 5 12 1z" fill="#d63a3a"/>'
        '<path d="M12 22.5a3.4 3.4 0 0 1-3.4-3.4c0-2 1.4-3 3.4-5.6 2 2.6 3.4 3.6 3.4 5.6A3.4 3.4 0 0 1 12 22.5z" fill="#ff8a5c" opacity="0.9"/></g>'
    )
    inner = (
        '<text class="ttl" x="40" y="36">CONTRIBUTION STREAK</text>'
        f"{flame}"
        f'<text class="num" x="110" y="66">{current} day{"s" if current != 1 else ""}</text>'
        '<text class="cap" x="110" y="88">CURRENT STREAK</text>'
        f'<text class="num" x="270" y="66">{longest} days</text>'
        '<text class="cap" x="270" y="88">LONGEST STREAK</text>'
        f'<text class="pct" x="432" y="106" text-anchor="end">updated {asof}</text>'
    )
    return frame(112, inner)


def main():
    user = json.loads(get(f"https://api.github.com/users/{USER}"))
    repos = json.loads(get(f"https://api.github.com/users/{USER}/repos?per_page=100"))
    repo_count = user["public_repos"]

    lang_counts = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    total_known = sum(lang_counts.values()) or 1
    langs = sorted(lang_counts.items(), key=lambda kv: -kv[1])[:3]
    langs = [(n, round(100 * c / total_known, 1)) for n, c in langs]

    svg = get(f"https://github.com/users/{USER}/contributions")
    days = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"', svg)
    days = sorted((d, int(l)) for d, l in days)
    active = {d for d, l in days if l > 0}
    active_days = len(active)

    today = date.today()

    def streak_from(end):
        s, cur = 0, end
        while cur.isoformat() in active:
            s += 1
            cur -= timedelta(days=1)
        return s

    current = max(streak_from(today), streak_from(today - timedelta(days=1)))
    best, prev, s = 0, None, 0
    for d, l in days:
        dd = date.fromisoformat(d)
        if l > 0:
            s = s + 1 if prev and (dd - prev).days == 1 else 1
            best = max(best, s)
            prev = dd
        else:
            s, prev = 0, None

    since = date.fromisoformat(user["created_at"][:10]).strftime("%b %Y").upper()
    asof = today.strftime("%b %-d, %Y")

    files = {
        "stats-overview.svg": overview_card(repo_count, active_days, since),
        "stats-langs.svg": langs_card(langs),
        "stats-streak.svg": streak_card(current, best, asof),
    }
    changed = []
    for fn, content in files.items():
        try:
            old = open(fn).read()
        except FileNotFoundError:
            old = None
        if old != content:
            open(fn, "w").write(content)
            changed.append(fn)
    if changed:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "add"] + changed, check=True)
        subprocess.run(["git", "commit", "-m", "chore: refresh stats cards [skip ci]"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("updated:", ", ".join(changed))
    else:
        print("no changes")


if __name__ == "__main__":
    main()
