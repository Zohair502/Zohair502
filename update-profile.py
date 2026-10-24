"""Refresh a public-only GitHub statistics card using the standard library."""
from datetime import datetime, timezone
from pathlib import Path
from html import escape
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


def metrics_for(repositories):
    public = [repo for repo in repositories if repo.get("private") is False]
    originals = [repo for repo in public if not repo.get("fork", False)]
    return [
        (len(public), "PUBLIC REPOSITORIES"),
        (len(originals), "ORIGINAL REPOSITORIES"),
        (sum(repo["stargazers_count"] for repo in originals), "STARS EARNED"),
        (sum(repo["forks_count"] for repo in originals), "FORKS RECEIVED"),
    ]
def render(repositories, timestamp, mobile=False):
    metrics = metrics_for(repositories)
    timestamp = escape(timestamp)
    width, height = (480, 330) if mobile else (1000, 220)
    cells = []
    for index, (value, label) in enumerate(metrics):
        x = 28 + (index % 2) * 230 if mobile else 32 + index * 240
        y = 100 + (index // 2) * 100 if mobile else 112
        cells.append(f'<text x="{x}" y="{y}" fill="#F0EEEA" font-size="44" font-weight="600">{value:,}</text>')
        cells.append(f'<text x="{x}" y="{y+30}" fill="#A8AAAC" font-size="{12 if mobile else 15}">{label}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Zohair502 public GitHub statistics</title>
<desc id="desc">{'; '.join(f'{label}: {value}' for value, label in metrics)}. Refreshed {timestamp}.</desc>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="8" fill="#14181C" stroke="#303438"/>
<g font-family="Segoe UI,Arial,sans-serif">
<text x="28" y="38" fill="#C8AA72" font-size="14" letter-spacing="2">PUBLIC GITHUB / ZOHAIR502</text>
{''.join(cells)}
<path d="M28 {height-58}H{width-28}" stroke="#303438"/>
<text x="28" y="{height-30}" fill="#9A9EA2" font-size="{12 if mobile else 14}">Updated {timestamp} · Public data only</text>
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
    root = Path(__file__).parent
    (root / "github-stats.svg").write_text(render(repositories, timestamp), encoding="utf-8")
    (root / "assets").mkdir(exist_ok=True)
    (root / "assets/github-stats-mobile.svg").write_text(render(repositories, timestamp, mobile=True), encoding="utf-8")
    print(f"Updated public statistics from {len(repositories)} repositories")


if __name__ == "__main__":
    main()
