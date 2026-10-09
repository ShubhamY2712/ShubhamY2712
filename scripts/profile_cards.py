"""Generates the amber GitHub stats card and contribution graph for the profile README.

Run by .github/workflows/snake.yml. Uses only the Python standard library and the
workflow's built-in GITHUB_TOKEN, so nothing depends on third-party card services.

Usage: python3 scripts/profile_cards.py <output-folder>
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "ShubhamY2712")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

AMBER, AMBER_LIGHT, AMBER_DEEP = "#FFC53D", "#FDE68A", "#B7791F"
PAPER, SURFACE, LINE, INK, INK_SOFT = "#0D0B07", "#15120B", "#2B251A", "#F7F4EE", "#ABA396"
FONT = "'Segoe UI','Poppins','Helvetica Neue',Arial,sans-serif"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { stargazerCount }
    }
    pullRequests { totalCount }
    issues { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch() -> dict:
    """Ask the GitHub GraphQL API for the numbers shown on the cards."""
    if os.environ.get("MOCK_DATA"):
        return json.load(open(os.environ["MOCK_DATA"]))
    body: bytes = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": USER},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        payload: dict = json.load(res)
    if payload.get("errors") or not payload.get("data", {}).get("user"):
        raise SystemExit(f"GitHub API error: {payload.get('errors')}")
    return payload["data"]["user"]


def fmt(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 10000 else f"{n:,}"


def stats_card(user: dict) -> str:
    cc: dict = user["contributionsCollection"]
    stars: int = sum(r["stargazerCount"] for r in user["repositories"]["nodes"])
    rows = [
        ("Contributions (last 12 months)", cc["contributionCalendar"]["totalContributions"], "spark"),
        ("Commits (last 12 months)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"], "commit"),
        ("Pull requests", user["pullRequests"]["totalCount"], "pr"),
        ("Issues opened", user["issues"]["totalCount"], "issue"),
        ("Public repositories", user["repositories"]["totalCount"], "repo"),
        ("Stars earned", stars, "star"),
    ]
    icons = {
        "spark": '<path d="M0-7 L1.8-1.8 L7 0 L1.8 1.8 L0 7 L-1.8 1.8 L-7 0 L-1.8-1.8Z" fill="%s"/>' % AMBER,
        "commit": '<circle r="3.6" fill="none" stroke="%s" stroke-width="2"/><path d="M-8 0H-3.6M3.6 0H8" stroke="%s" stroke-width="2"/>' % (AMBER, AMBER),
        "pr": '<circle cx="-4" cy="-5" r="2.2" fill="none" stroke="%s" stroke-width="1.8"/><circle cx="-4" cy="5" r="2.2" fill="none" stroke="%s" stroke-width="1.8"/><circle cx="5" cy="5" r="2.2" fill="none" stroke="%s" stroke-width="1.8"/><path d="M-4-2.8V2.8M5 2.8V-2Q5-5 2-5H0" fill="none" stroke="%s" stroke-width="1.8"/>' % (AMBER, AMBER, AMBER, AMBER),
        "issue": '<circle r="7" fill="none" stroke="%s" stroke-width="1.8"/><circle r="1.8" fill="%s"/>' % (AMBER, AMBER),
        "repo": '<path d="M-6-7H5V5H-4Q-6 5-6 7Z M-6 7Q-6 9-4 9H5" fill="none" stroke="%s" stroke-width="1.8" stroke-linejoin="round"/>' % AMBER,
        "star": '<path d="M0-7.5 L2.2-2.6 L7.4-2.1 L3.5 1.4 L4.6 6.6 L0 3.9 L-4.6 6.6 L-3.5 1.4 L-7.4-2.1 L-2.2-2.6Z" fill="none" stroke="%s" stroke-width="1.7" stroke-linejoin="round"/>' % AMBER,
    }
    W, H = 495, 200
    out = []
    for i, (label, value, icon) in enumerate(rows):
        y = 74 + i * 22
        out.append(
            f'<g class="row" style="animation-delay:{0.15 + i * 0.12:.2f}s">'
            f'<g transform="translate(36 {y - 5})">{icons[icon]}</g>'
            f'<text x="56" y="{y}" class="lbl">{escape(label)}</text>'
            f'<text x="300" y="{y}" class="val" text-anchor="end">{fmt(value)}</text></g>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats for {USER}">
  <title>GitHub stats</title>
  <defs>
    <radialGradient id="g" cx="85%" cy="55%" r="45%"><stop offset="0" stop-color="{AMBER}" stop-opacity=".22"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>
    <clipPath id="c"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16"/></clipPath>
  </defs>
  <style>
    text {{ font-family: {FONT}; }}
    .title {{ font-size: 19px; font-weight: 700; fill: {AMBER}; }}
    .lbl {{ font-size: 13.5px; fill: {INK_SOFT}; }}
    .val {{ font-size: 14px; font-weight: 700; fill: {INK}; }}
    .row {{ opacity: 0; animation: rise .7s cubic-bezier(.22,1,.36,1) forwards; }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateX(-8px); }} to {{ opacity: 1; transform: none; }} }}
    .spin {{ animation: spin 18s linear infinite; transform-origin: 405px 108px; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .pulse {{ animation: pulse 3s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes pulse {{ 0%,100% {{ opacity: .7; transform: scale(1); }} 50% {{ opacity: 1; transform: scale(1.08); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .row {{ opacity: 1; }} }}
  </style>
  <g clip-path="url(#c)">
    <rect width="{W}" height="{H}" fill="{PAPER}"/>
    <rect width="{W}" height="{H}" fill="url(#g)"/>
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" fill="none" stroke="{LINE}" stroke-width="1.5"/>
  <text x="28" y="40" class="title">GitHub stats</text>
  {''.join(out)}
  <circle class="spin" cx="405" cy="108" r="58" fill="none" stroke="{AMBER}" stroke-opacity=".45" stroke-width="1.5" stroke-dasharray="3 7"/>
  <circle class="pulse" cx="405" cy="108" r="40" fill="{SURFACE}" stroke="{AMBER}" stroke-width="2"/>
  <text x="405" y="117" text-anchor="middle" font-size="26" font-weight="800" fill="{AMBER}">SY</text>
</svg>
"""


def activity_graph(user: dict) -> str:
    days = [d for w in user["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days = days[-31:]
    counts = [d["contributionCount"] for d in days]
    W, H = 1200, 340
    L, R, T, B = 70, 40, 78, 290
    top = max(4, max(counts))
    step = (W - L - R) / (len(days) - 1)
    pts = [(L + i * step, B - (c / top) * (B - T)) for i, c in enumerate(counts)]

    def smooth(points: list) -> str:
        d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            cx = (x0 + x1) / 2
            d += f" C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
        return d

    line = smooth(pts)
    area = line + f" L{pts[-1][0]:.1f},{B} L{pts[0][0]:.1f},{B} Z"
    grid = "".join(
        f'<line x1="{L}" x2="{W - R}" y1="{B - f * (B - T):.1f}" y2="{B - f * (B - T):.1f}" stroke="{LINE}" stroke-dasharray="3 6"/>'
        f'<text x="{L - 14}" y="{B - f * (B - T) + 4:.1f}" class="ax" text-anchor="end">{round(top * f)}</text>'
        for f in (0, 0.5, 1)
    )
    labels = "".join(
        f'<text x="{pts[i][0]:.1f}" y="{B + 24}" class="ax" text-anchor="middle">{dt.date.fromisoformat(days[i]["date"]).strftime("%d %b")}</text>'
        for i in range(0, len(days), 5)
    )
    dots = "".join(
        f'<circle class="dot" style="animation-delay:{1.4 + i * 0.03:.2f}s" cx="{x:.1f}" cy="{y:.1f}" r="{4.5 if counts[i] else 3}" fill="{AMBER_LIGHT if counts[i] else LINE}"/>'
        for i, (x, y) in enumerate(pts)
    )
    total = sum(counts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last 31 days">
  <title>Contribution activity, last 31 days</title>
  <defs>
    <linearGradient id="a" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity=".45"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>
    <clipPath id="c"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20"/></clipPath>
    <clipPath id="reveal"><rect class="wipe" x="0" y="0" width="{W}" height="{H}"/></clipPath>
  </defs>
  <style>
    text {{ font-family: {FONT}; }}
    .title {{ font-size: 20px; font-weight: 700; fill: {AMBER}; }}
    .sub {{ font-size: 14px; fill: {INK_SOFT}; }}
    .ax {{ font-size: 12px; fill: {INK_SOFT}; }}
    .draw {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 2.2s cubic-bezier(.65,0,.35,1) .2s forwards; }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
    .wipe {{ transform: scaleX(0); transform-origin: left; animation: wipe 2.2s cubic-bezier(.65,0,.35,1) .2s forwards; }}
    @keyframes wipe {{ to {{ transform: scaleX(1); }} }}
    .dot {{ opacity: 0; animation: pop .4s ease-out forwards; transform-box: fill-box; transform-origin: center; }}
    @keyframes pop {{ from {{ opacity: 0; transform: scale(0); }} to {{ opacity: 1; transform: scale(1); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .draw {{ stroke-dashoffset: 0; }} .wipe {{ transform: none; }} .dot {{ opacity: 1; }} }}
  </style>
  <g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{PAPER}"/></g>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="none" stroke="{LINE}" stroke-width="1.5"/>
  <text x="{L - 30}" y="42" class="title">Contribution activity</text>
  <text x="{W - R}" y="42" class="sub" text-anchor="end">{total} contributions in the last 31 days</text>
  {grid}{labels}
  <path d="{area}" fill="url(#a)" clip-path="url(#reveal)"/>
  <path class="draw" pathLength="1" d="{line}" fill="none" stroke="{AMBER}" stroke-width="3" stroke-linecap="round"/>
  {dots}
</svg>
"""


def main() -> None:
    out_dir: str = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(out_dir, exist_ok=True)
    user: dict = fetch()
    with open(os.path.join(out_dir, "stats.svg"), "w", encoding="utf-8") as f:
        f.write(stats_card(user))
    with open(os.path.join(out_dir, "activity.svg"), "w", encoding="utf-8") as f:
        f.write(activity_graph(user))
    print("Wrote stats.svg and activity.svg to", out_dir)


if __name__ == "__main__":
    main()
