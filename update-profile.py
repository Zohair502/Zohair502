"""Refresh a public-only GitHub statistics card using the standard library."""
from datetime import datetime, timezone
from pathlib import Path
import json
import urllib.request

OWNER = "Zohair502"


def public_json(path):
    # Intentionally unauthenticated: this card cannot read private repositories.
    request = urllib.request.Request(
        "https://api.github.com/" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Zohair502-profile"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def render(repositories, timestamp):
    public = [repo for repo in repositories if not repo.get("private", True)]
    originals = [repo for repo in public if not repo.get("fork", False)]
    metrics = [
        (len(public), "PUBLIC REPOSITORIES"),
        (len(originals), "ORIGINAL REPOSITORIES"),
        (sum(repo["stargazers_count"] for repo in originals), "STARS EARNED"),
        (sum(repo["forks_count"] for repo in originals), "FORKS RECEIVED"),
    ]
    cells = []
    for index, (value, label) in enumerate(metrics):
        x = 32 + index * 240
        cells.append(f'<text x="{x}" y="109" fill="#F5F3ED" font-size="40" font-weight="700">{value:,}</text>')
        cells.append(f'<text x="{x}" y="139" fill="#9AACBF" font-size="11" letter-spacing="1">{label}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="202" viewBox="0 0 1000 202" role="img" aria-labelledby="title desc">
<title id="title">Zohair502 public GitHub statistics</title>
<desc id="desc">{'; '.join(f'{label}: {value}' for value, label in metrics)}. Refreshed {timestamp}.</desc>
<rect x="1" y="1" width="998" height="200" rx="16" fill="#0C192B" stroke="#34404D"/>
<g font-family="Segoe UI,Arial,sans-serif">
<text x="32" y="38" fill="#D8B66A" font-size="14" letter-spacing="3">PUBLIC GITHUB / ZOHAIR502</text>
{''.join(cells)}
<path d="M32 160H968" stroke="#26374C"/>
<text x="32" y="184" fill="#8295AC" font-size="12">Public data only · Refreshed {timestamp} · Updates daily</text>
</g></svg>'''


def main():
    repositories = []
    page = 1
    while True:
        batch = public_json(f"users/{OWNER}/repos?type=owner&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("GitHub did not return a repository list")
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    Path(__file__).with_name("github-stats.svg").write_text(render(repositories, timestamp), encoding="utf-8")
    print(f"Updated public statistics from {len(repositories)} repositories")


if __name__ == "__main__":
    main()
