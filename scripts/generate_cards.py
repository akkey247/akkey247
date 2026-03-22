#!/usr/bin/env python3
import os
import json
import re
import urllib.request

USERNAME = "akkey247"
TOKEN = os.environ["GITHUB_TOKEN"]

LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178C6",
    "JavaScript": "#f1e05a",
    "Go": "#00ADD8",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Java": "#b07219",
    "C#": "#178600",
    "C++": "#f34b7d",
    "C": "#555555",
    "Shell": "#89e051",
    "Rust": "#dea584",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Dart": "#00B4AB",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Lua": "#000080",
    "Scala": "#c22d40",
    "Elixir": "#6e4a7e",
    "Haskell": "#5e5086",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
    "Nix": "#7e7eff",
}
OTHER_COLOR = "#484f58"

query = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    following { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": USERNAME}}).encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read())["data"]["user"]

repos = data["repositories"]["totalCount"]
stars = sum(r["stargazerCount"] for r in data["repositories"]["nodes"])
followers = data["followers"]["totalCount"]
following = data["following"]["totalCount"]

# ── Aggregate language bytes ──
lang_bytes: dict[str, int] = {}
for repo in data["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        lang_name = edge["node"]["name"]
        lang_bytes[lang_name] = lang_bytes.get(lang_name, 0) + edge["size"]

total_bytes = sum(lang_bytes.values()) or 1
lang_sorted = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)

MAX_LANGS = 5
top_langs = lang_sorted[:MAX_LANGS]
other_bytes = sum(size for _, size in lang_sorted[MAX_LANGS:])
lang_entries: list[tuple[str, float, str]] = []
for lang_name, size in top_langs:
    pct = size / total_bytes * 100
    color = LANGUAGE_COLORS.get(lang_name, OTHER_COLOR)
    lang_entries.append((lang_name, pct, color))
if other_bytes > 0:
    lang_entries.append(("Other", other_bytes / total_bytes * 100, OTHER_COLOR))

FONT = "'Segoe UI',Helvetica,Arial,sans-serif"

# ── Generate languages.svg ──
SVG_W = 800
BAR_X = 24
BAR_WIDTH = SVG_W - BAR_X * 2

bar_rects = []
x_offset = float(BAR_X)
for lang_name, pct, color in lang_entries:
    w = BAR_WIDTH * pct / 100
    bar_rects.append(f'    <rect x="{x_offset}" y="52" width="{w:.2f}" height="10" fill="{color}"/>')
    x_offset += w
bar_rects_str = "\n".join(bar_rects)

legend_items = []
cols_per_row = 6
col_width = (SVG_W - BAR_X * 2) // cols_per_row
for i, (lang_name, pct, color) in enumerate(lang_entries):
    row = i // cols_per_row
    col = i % cols_per_row
    y_base = 84 + row * 26
    x_base = BAR_X + col * col_width
    legend_items.append(
        f'  <g transform="translate({x_base}, {y_base})">\n'
        f'    <circle cx="5" cy="5" r="5" fill="{color}"/>\n'
        f'    <text x="16" y="9" font-size="12" font-family="{FONT}">'
        f'<tspan fill="#e6edf3">{lang_name}</tspan>'
        f'<tspan fill="#7d8590" dx="14">{pct:.1f}%</tspan>'
        f'</text>\n'
        f'  </g>'
    )
legend_str = "\n".join(legend_items)

dot_colors = [e[2] for e in lang_entries[:3]] if len(lang_entries) >= 3 else [OTHER_COLOR] * 3
dots = "\n".join([
    f'  <circle cx="{SVG_W - 40 + i * 12}" cy="28" r="3" fill="{dot_colors[i]}" opacity="0.3"/>'
    for i in range(3)
])

languages_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} 130">
  <defs>
    <linearGradient id="bg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#161b22"/>
    </linearGradient>
    <linearGradient id="accent2" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#58a6ff"/>
      <stop offset="100%" stop-color="#1f6feb"/>
    </linearGradient>
    <clipPath id="bar-clip">
      <rect x="{BAR_X}" y="52" width="{BAR_WIDTH}" height="10" rx="5"/>
    </clipPath>
  </defs>

  <rect width="{SVG_W}" height="130" rx="12" fill="url(#bg2)" stroke="#30363d" stroke-width="1"/>

  <!-- Title -->
  <text x="24" y="32" font-size="15" fill="#e6edf3" font-family="{FONT}" font-weight="600">Top Languages</text>
  <rect x="24" y="42" width="60" height="2" rx="1" fill="url(#accent2)"/>

  <!-- Combined Progress Bar -->
  <g clip-path="url(#bar-clip)">
{bar_rects_str}
  </g>

  <!-- Legend -->
{legend_str}

  <!-- Decorative dots -->
{dots}
</svg>"""

os.makedirs("assets", exist_ok=True)
with open("assets/languages.svg", "w") as f:
    f.write(languages_svg)

# ── Update README.md profile stats ──
stats_badges = (
    f"<!-- PROFILE_STATS:START -->\n"
    f"<p>\n"
    f'  <img alt="Followers" src="https://img.shields.io/badge/Followers-{followers}-181717?style=flat&logo=github" />\n'
    f'  <img alt="Following" src="https://img.shields.io/badge/Following-{following}-181717?style=flat&logo=github" />\n'
    f'  <img alt="Repositories" src="https://img.shields.io/badge/Repos-{repos}-181717?style=flat&logo=github" />\n'
    f'  <img alt="Stars" src="https://img.shields.io/badge/Stars-{stars}-181717?style=flat&logo=github" />\n'
    f"</p>\n"
    f"<!-- PROFILE_STATS:END -->"
)

readme_path = "README.md"
with open(readme_path, "r") as f:
    readme = f.read()
readme = re.sub(
    r"<!-- PROFILE_STATS:START -->.*?<!-- PROFILE_STATS:END -->",
    stats_badges,
    readme,
    flags=re.DOTALL,
)
with open(readme_path, "w") as f:
    f.write(readme)

print(f"Generated languages.svg ({len(lang_entries)} languages)")
print(f"Updated README.md (followers={followers}, following={following})")
print("Done!")
