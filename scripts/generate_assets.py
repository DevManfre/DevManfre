#!/usr/bin/env python3
"""Generate the profile README SVG assets (hero, stack, projects, stats).

Run by .github/workflows/assets.yml. Locally: GITHUB_TOKEN=$(gh auth token) python3 scripts/generate_assets.py
"""
import json
import os
import subprocess
import urllib.request
from html import escape
from pathlib import Path

LOGIN = os.environ.get("GITHUB_REPOSITORY_OWNER", "DevManfre")
OUT = Path(__file__).resolve().parent.parent / "assets"
W = 800

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

THEMES = {
    "dark": dict(term="#010409", card="#161b22", border="#30363d", text="#e6edf3",
                 muted="#9da7b3", accent="#7ee787", dot="#3d444d", body="#c9d1d9"),
    "light": dict(term="#f6f8fa", card="#ffffff", border="#d1d9e0", text="#1f2328",
                  muted="#59636e", accent="#116329", dot="#c4ccd4", body="#3d444d"),
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection { totalCommitContributions }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes { stargazerCount }
    }
    pinnedItems(first: 3, types: REPOSITORY) {
      nodes { ... on Repository {
        name description stargazerCount primaryLanguage { name color }
      } }
    }
  }
}
"""


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or subprocess.check_output(
        ["gh", "auth", "token"], text=True).strip()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(payload["errors"])
    return payload["data"]["user"]


def wrap(text, width, lines):
    out, cur = [], ""
    for word in (text or "").split():
        if len(cur) + len(word) + (1 if cur else 0) > width:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: max(width - 1, 1)].rstrip() + "…"
    return out


def svg(width, height, title, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>{body}</svg>\n"
    )


def heading(t, label):
    return (f'<text x="0" y="16" font-family="{MONO}" font-size="13" '
            f'fill="{t["accent"]}">## {escape(label)}</text>')


def hero(t):
    lines = [
        ("cmd", "whoami"),
        ("name", "Alessio Manfredini"),
        ("cmd", "cat role.txt"),
        ("out", "Web developer. I build things for the browser and the server."),
        ("cmd", "pwd"),
        ("out", "Modena, Italy"),
        ("cmd", "cat stack.txt"),
        ("out", "HTML · CSS · JavaScript · TypeScript · Python · Docker"),
        ("cmd", ""),
    ]
    y, delay, rows, css = 92, 0.4, [], []
    for i, (kind, text) in enumerate(lines):
        n = max(len(text), 1)
        dur = round(n * 0.035, 2)
        if kind == "name":
            y += 12
            rows.append(
                f'<text class="r a{i}" x="28" y="{y}" font-family="{MONO}" font-size="30" '
                f'font-weight="700" fill="{t["text"]}">{escape(text)}</text>')
            css.append(f".a{i}{{animation:fade .4s ease {delay:.2f}s both}}")
            delay += 0.5
            y += 30
            continue
        color = t["body"] if kind == "out" else t["text"]
        prompt = (f'<tspan fill="{t["accent"]}">$ </tspan>' if kind == "cmd" else "")
        rows.append(
            f'<text class="r a{i}" x="28" y="{y}" font-family="{MONO}" font-size="15" '
            f'fill="{color}">{prompt}{escape(text)}</text>')
        if text:
            css.append(
                f".a{i}{{animation:type{i} {dur}s steps({n}) {delay:.2f}s both}}"
                f"@keyframes type{i}{{from{{clip-path:inset(0 100% 0 0)}}to{{clip-path:inset(0 0 0 0)}}}}")
            delay += dur + 0.25
        else:
            cx = 28 + 2 * 9.0 + 4
            rows.append(
                f'<rect class="cur" x="{cx}" y="{y - 14}" width="9" height="17" fill="{t["accent"]}"/>')
        y += 28
    height = y + 4
    style = (
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
        f".cur{{animation:blink 1.1s steps(1) {delay:.2f}s infinite;opacity:0}}"
        + "".join(css)
        + "@media (prefers-reduced-motion:reduce){.r,.cur{animation:none!important;opacity:1}}"
    )
    body = (
        f"<style>{style}</style>"
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="10" fill="{t["term"]}" stroke="{t["border"]}"/>'
        f'<path d="M0.5 40.5H{W - 0.5}" stroke="{t["border"]}"/>'
        + "".join(f'<circle cx="{22 + 18 * k}" cy="20" r="5.5" fill="{t["dot"]}"/>' for k in range(3))
        + f'<text x="86" y="24" font-family="{MONO}" font-size="12" fill="{t["muted"]}">alessio@modena: ~</text>'
        + "".join(rows)
    )
    return svg(W, height, "Alessio Manfredini, web developer from Modena", body)


def stack(t):
    groups = [
        ("frontend", ["HTML5 · CSS3 · JavaScript", "TypeScript · React · Next.js"]),
        ("backend", ["PHP · Python · Django", "Java"]),
        ("tools", ["Docker · Git"]),
    ]
    gap, cw, ch, top = 16, (W - 32) / 3, 100, 32
    body = heading(t, "stack")
    for i, (name, rows) in enumerate(groups):
        x = i * (cw + gap)
        body += (
            f'<rect x="{x + .5}" y="{top + .5}" width="{cw - 1}" height="{ch - 1}" rx="8" fill="{t["card"]}" stroke="{t["border"]}"/>'
            f'<text x="{x + 18}" y="{top + 30}" font-family="{MONO}" font-size="14" font-weight="700" fill="{t["text"]}">{name}</text>'
        )
        for j, r in enumerate(rows):
            body += (f'<text x="{x + 18}" y="{top + 54 + j * 20}" font-family="{SANS}" font-size="13" '
                     f'fill="{t["body"]}">{escape(r)}</text>')
    label = "Stack: " + "; ".join(f"{n}: {', '.join(r)}" for n, r in groups)
    return svg(W, top + ch, label, body)


def projects(t, repos):
    n = max(len(repos), 1)
    gap, top, ch = 16, 32, 140
    cw = (W - gap * (n - 1)) / n
    body = heading(t, "featured")
    for i, r in enumerate(repos):
        x = i * (cw + gap)
        body += (
            f'<rect x="{x + .5}" y="{top + .5}" width="{cw - 1}" height="{ch - 1}" rx="8" fill="{t["card"]}" stroke="{t["border"]}"/>'
            f'<text x="{x + 18}" y="{top + 30}" font-family="{MONO}" font-size="15" font-weight="700" fill="{t["accent"]}">{escape(r["name"])}</text>'
        )
        for j, line in enumerate(wrap(r["description"], int((cw - 36) / 6.6), 3)):
            body += (f'<text x="{x + 18}" y="{top + 56 + j * 19}" font-family="{SANS}" font-size="13" '
                     f'fill="{t["body"]}">{escape(line)}</text>')
        meta_y = top + ch - 18
        lang = r.get("primaryLanguage")
        mx = x + 18
        if lang:
            body += (f'<circle cx="{mx + 5}" cy="{meta_y - 4}" r="5" fill="{lang["color"] or t["muted"]}"/>'
                     f'<text x="{mx + 16}" y="{meta_y}" font-family="{MONO}" font-size="12" fill="{t["muted"]}">{escape(lang["name"])}</text>')
            mx += 16 + 8 * len(lang["name"]) + 14
        body += (f'<text x="{mx}" y="{meta_y}" font-family="{MONO}" font-size="12" fill="{t["muted"]}">'
                 f'★ {r["stargazerCount"]}</text>')
    label = "Featured repositories: " + ", ".join(r["name"] for r in repos)
    return svg(W, top + ch, label, body)


def stats(t, u):
    items = [
        (u["contributionsCollection"]["totalCommitContributions"], "commits, last year"),
        (u["repositories"]["totalCount"], "repositories"),
        (sum(r["stargazerCount"] for r in u["repositories"]["nodes"]), "stars"),
        (u["followers"]["totalCount"], "followers"),
    ]
    gap, cw, ch, top = 16, (W - 48) / 4, 84, 32
    body = heading(t, "stats")
    for i, (value, label) in enumerate(items):
        x = i * (cw + gap)
        body += (
            f'<rect x="{x + .5}" y="{top + .5}" width="{cw - 1}" height="{ch - 1}" rx="8" fill="{t["card"]}" stroke="{t["border"]}"/>'
            f'<text x="{x + 18}" y="{top + 40}" font-family="{MONO}" font-size="26" font-weight="700" fill="{t["text"]}">{value}</text>'
            f'<text x="{x + 18}" y="{top + 64}" font-family="{SANS}" font-size="13" fill="{t["muted"]}">{label}</text>'
        )
    label = "Stats: " + ", ".join(f"{v} {l}" for v, l in items)
    return svg(W, top + ch, label, body)


def main():
    u = fetch()
    repos = u["pinnedItems"]["nodes"]
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        files = {
            f"hero-{name}.svg": hero(t),
            f"stack-{name}.svg": stack(t),
            f"projects-{name}.svg": projects(t, repos),
            f"stats-{name}.svg": stats(t, u),
        }
        for fname, content in files.items():
            (OUT / fname).write_text(content, encoding="utf-8")
    print(f"wrote {len(THEMES) * 4} files to {OUT}")


if __name__ == "__main__":
    main()
