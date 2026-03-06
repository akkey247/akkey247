#!/usr/bin/env python3
import os
import json
import urllib.request
from datetime import datetime, timezone

USERNAME = "akkey247"
TOKEN = os.environ["GITHUB_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    name
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
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

commits = data["contributionsCollection"]["totalCommitContributions"]
prs = data["contributionsCollection"]["totalPullRequestContributions"]
repos = data["repositories"]["totalCount"]
stars = sum(r["stargazerCount"] for r in data["repositories"]["nodes"])
updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
name = data.get("name") or USERNAME

svg = f"""<svg width="400" height="120" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="120" rx="10" fill="#0d1117" stroke="#30363d"/>
  <text x="16" y="28" font-size="14" fill="#e6edf3" font-family="monospace" font-weight="bold">{name}'s GitHub Stats</text>
  <text x="16" y="55" font-size="12" fill="#7d8590" font-family="monospace">Commits:  {commits:,}</text>
  <text x="16" y="73" font-size="12" fill="#7d8590" font-family="monospace">PRs:      {prs:,}</text>
  <text x="16" y="91" font-size="12" fill="#7d8590" font-family="monospace">Repos:    {repos}  /  Stars: {stars}</text>
  <text x="16" y="112" font-size="10" fill="#484f58" font-family="monospace">updated: {updated}</text>
</svg>"""

os.makedirs("assets", exist_ok=True)
with open("assets/stats.svg", "w") as f:
    f.write(svg)

print("Done!")
