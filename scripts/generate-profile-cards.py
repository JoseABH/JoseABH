"""Generate self-contained README cards from the public GitHub REST API.

Only the Python standard library is required. Failed requests leave the existing
cards intact; no private data or third-party image rendering service is used.
"""

from collections import Counter
from html import escape
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
USERNAME = "JoseABH"
COLORS = ["#38bdf8", "#a78bfa", "#2dd4bf", "#fbbf24", "#fb7185", "#60a5fa", "#e879f9", "#94a3b8"]


def github(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "JoseABH-profile-cards"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(f"https://api.github.com{path}", headers=headers), timeout=30) as response:
        return json.load(response)


def fetch_profile():
    profile = github(f"/users/{USERNAME}")
    repositories = []
    page = 1
    while True:
        batch = github(f"/users/{USERNAME}/repos?type=owner&sort=full_name&per_page=100&page={page}")
        repositories.extend(batch)
        if len(batch) < 100:
            return profile, repositories
        page += 1


def summarize(profile, repositories):
    originals = [repo for repo in repositories if not repo["fork"] and not repo["private"]]
    return {
        "repos": len(originals),
        "stars": sum(repo["stargazers_count"] for repo in originals),
        "forks": sum(repo["forks_count"] for repo in originals),
        "followers": profile["followers"],
        "since": profile["created_at"][:4],
        "languages": Counter(repo["language"] for repo in originals if repo["language"]),
    }


def text(x, y, value, size=16, color="#cbd5e1", weight=400):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}">{escape(str(value))}</text>')


def card(title, description, body, width=480, height=340):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{escape(title)}</title>\n'
            f'<desc id="desc">{escape(description)}</desc>\n'
            f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="16" '
            'fill="#0b1220" stroke="#263449"/>\n'
            '<g font-family="Segoe UI, Arial, sans-serif">\n'
            + text(28, 43, title, 23, "#38bdf8", 700) + "\n" + body + '\n</g>\n</svg>\n')


def render_cards(data):
    stats = text(28, 70, "Public repositories · excluding forks", 13, "#94a3b8")
    for index, (label, value) in enumerate([
        ("Original repositories", data["repos"]),
        ("Stars received", data["stars"]),
        ("Forks received", data["forks"]),
        ("Followers", data["followers"]),
    ]):
        y = 117 + index * 46
        stats += text(28, y, label) + text(380, y, f"{value:,}", 24, "#f8fafc", 700)
    stats += text(28, 314, f'@{USERNAME} · GitHub public data', 12, "#94a3b8")

    counts = sorted(data["languages"].items(), key=lambda item: (-item[1], item[0]))
    total = sum(value for _, value in counts)
    # Keep the chart complete: smaller languages are grouped, never discarded.
    rows = counts if len(counts) <= 8 else counts[:7] + [("Other", sum(n for _, n in counts[7:]))]
    languages = text(28, 70, "Primary language per public, non-fork repository", 12, "#94a3b8")
    for index, (name, count) in enumerate(rows):
        y = 99 + index * 27
        languages += text(28, y, name, 14)
        languages += f'<rect x="170" y="{y - 11}" width="190" height="9" rx="4" fill="#1e293b"/>'
        languages += (f'<rect x="170" y="{y - 11}" width="{190 * count / total:.2f}" '
                      f'height="9" rx="4" fill="{COLORS[index]}"/>')
        languages += text(375, y, f"{count / total:.0%}", 14, "#f8fafc")
    if not rows:
        languages += text(28, 128, "No public language data available.")
    languages += text(28, 325, "Repository share · not code volume or proficiency", 12, "#94a3b8")

    milestones = text(28, 70, "A snapshot of my public development journey", 15, "#94a3b8")
    for index, (value, label) in enumerate([
        (data["since"], "Joined GitHub"),
        (data["repos"], "Original repositories"),
        (len(counts), "Primary languages"),
        (data["stars"], "Stars received"),
    ]):
        x = 28 + index * 234
        milestones += f'<rect x="{x}" y="94" width="214" height="124" rx="12" fill="#111e30"/>'
        milestones += f'<path d="M{x + 18} 113h20l-10 15z" fill="{COLORS[index]}"/>'
        milestones += text(x + 18, 167, value, 32, "#f8fafc", 700)
        milestones += text(x + 18, 198, label, 15)
    milestones += text(28, 248, "Public profile milestones · official GitHub achievements are linked below", 13, "#94a3b8")

    return {
        "github-stats.svg": card("GitHub overview", "Public repository statistics and followers.", stats),
        "github-languages.svg": card("Repositories by language", "Share of repositories by primary language.", languages),
        "github-milestones.svg": card("Public milestones", "Account creation year, repositories, languages and stars.", milestones, 980, 270),
    }


def main():
    # Fetch and render everything before changing any of the published assets.
    profile, repositories = fetch_profile()
    cards = render_cards(summarize(profile, repositories))
    output = ROOT / "assets" / "generated"
    output.mkdir(parents=True, exist_ok=True)
    for filename, content in cards.items():
        target = output / filename
        temporary = target.with_suffix(".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
    print(f"Generated {len(cards)} cards from {len(repositories)} public repositories.")


if __name__ == "__main__":
    main()
