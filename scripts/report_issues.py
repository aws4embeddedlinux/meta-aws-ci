#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime, timezone

# Repository list from README.md
REPOS = [
    "aws4embeddedlinux-ci",
    "meta-aws",
    "aws4embeddedlinux-ci-examples",
    "demo-auto-aws-iotfleetwise",
    "demo-iot-automotive-cloud",
    "demo-iot-automotive-embeddedlinux-image",
    "demo-iot-automotive-mcu",
    "demo-iot-automotive-simulator",
    "meta-aws-buildbot",
    "meta-aws-ci",
    "meta-aws-demos",
    "meta-aws-ewaol",
]


def run_gh_command(args):
    """Run gh CLI command and return JSON output"""
    try:
        result = subprocess.run(
            ["gh"] + args, capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout) if result.stdout else []
    except subprocess.CalledProcessError as e:
        print(f"Error running gh command: {e}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return []


def get_repo_data(repo):
    """Get issues and PRs for a repository"""
    print(f"Fetching data for {repo}...", file=sys.stderr)

    issues = run_gh_command(
        [
            "issue",
            "list",
            "--repo",
            f"aws4embeddedlinux/{repo}",
            "--state",
            "open",
            "--json",
            "number,title,createdAt,url",
            "--limit",
            "1000",
        ]
    )

    prs = run_gh_command(
        [
            "pr",
            "list",
            "--repo",
            f"aws4embeddedlinux/{repo}",
            "--state",
            "open",
            "--json",
            "number,title,createdAt,url",
            "--limit",
            "1000",
        ]
    )

    return {
        "repo": repo,
        "issues": issues,
        "prs": prs,
        "issue_count": len(issues),
        "pr_count": len(prs),
    }


def calculate_age_days(created_at):
    """Calculate age in days from ISO timestamp"""
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (now - created).days


def main():
    all_data = []

    for repo in REPOS:
        data = get_repo_data(repo)
        all_data.append(data)

    # Calculate totals
    total_issues = sum(d["issue_count"] for d in all_data)
    total_prs = sum(d["pr_count"] for d in all_data)

    # Generate HTML
    print("<!DOCTYPE html>")
    print('<html lang="en">')
    print("<head>")
    print('    <meta charset="UTF-8">')
    print('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    print("    <title>Issues & Pull Requests</title>")
    print('    <link rel="stylesheet" href="style.css">')
    print("    <style>")
    print(
        "        .summary-cards { display: grid; "
        "grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); "
        "gap: 1rem; margin-bottom: 2rem; }"
    )
    print(
        "        .summary-card { background: white; padding: 1rem; "
        "border-radius: 8px; text-align: center; "
        "border: 1px solid #dee2e6; }"
    )
    print("        .summary-card h3 { font-size: 2rem; color: #ff9900; margin: 0; }")
    print("        .summary-card p { margin: 0.5rem 0 0 0; color: #666; }")
    print(
        "        .repo-section { background: white; padding: 1.5rem; "
        "margin-bottom: 1rem; border-radius: 8px; }"
    )
    print(
        "        .repo-header { display: flex; "
        "justify-content: space-between; align-items: center; "
        "margin-bottom: 1rem; }"
    )
    print(
        "        .repo-name { font-size: 1.25rem; font-weight: bold; "
        "color: #232f3e; }"
    )
    print("        .counts { color: #666; }")
    print("        .item-list { list-style: none; padding: 0; }")
    print(
        "        .item-list li { padding: 0.5rem 0; "
        "border-bottom: 1px solid #f0f0f0; }"
    )
    print("        .item-list li:last-child { border-bottom: none; }")
    print("        .item-link { color: #0366d6; text-decoration: none; }")
    print("        .item-link:hover { text-decoration: underline; }")
    print("        .age { color: #666; font-size: 0.875rem; " "margin-left: 0.5rem; }")
    print("        .no-items { color: #999; font-style: italic; }")
    print("    </style>")
    print("</head>")
    print("<body>")
    print("    <header>")
    print("        <h1>Issues & Pull Requests</h1>")
    print("        <h2>Organization-wide Tracking</h2>")
    print("    </header>")
    print("    <main>")
    print('        <div class="report-header">')
    print(
        '            <p><a href="index.html" class="back-link">'
        "← Back to Dashboard</a></p>"
    )
    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"            <p><strong>Last Updated:</strong> {updated}</p>")
    print("        </div>")
    print('        <div class="summary-cards">')
    print('            <div class="summary-card">')
    print(f"                <h3>{total_issues}</h3>")
    print("                <p>Open Issues</p>")
    print("            </div>")
    print('            <div class="summary-card">')
    print(f"                <h3>{total_prs}</h3>")
    print("                <p>Open Pull Requests</p>")
    print("            </div>")
    print('            <div class="summary-card">')
    print(f"                <h3>{len(REPOS)}</h3>")
    print("                <p>Repositories</p>")
    print("            </div>")
    print("        </div>")

    for data in all_data:
        if data["issue_count"] == 0 and data["pr_count"] == 0:
            continue

        print('        <div class="repo-section">')
        print('            <div class="repo-header">')
        print(f'                <span class="repo-name">{data["repo"]}</span>')
        print(
            f'                <span class="counts">'
            f'{data["issue_count"]} issues, {data["pr_count"]} PRs</span>'
        )
        print("            </div>")

        if data["issues"]:
            print("            <h4>Issues</h4>")
            print('            <ul class="item-list">')
            for issue in sorted(data["issues"], key=lambda x: x["createdAt"]):
                age = calculate_age_days(issue["createdAt"])
                print("                <li>")
                print(
                    f'                    <a href="{issue["url"]}" '
                    f'class="item-link">#{issue["number"]}: '
                    f'{issue["title"]}</a>'
                )
                print(f'                    <span class="age">({age} days old)</span>')
                print("                </li>")
            print("            </ul>")

        if data["prs"]:
            print("            <h4>Pull Requests</h4>")
            print('            <ul class="item-list">')
            for pr in sorted(data["prs"], key=lambda x: x["createdAt"]):
                age = calculate_age_days(pr["createdAt"])
                print("                <li>")
                print(
                    f'                    <a href="{pr["url"]}" '
                    f'class="item-link">#{pr["number"]}: '
                    f'{pr["title"]}</a>'
                )
                print(f'                    <span class="age">({age} days old)</span>')
                print("                </li>")
            print("            </ul>")

        print("        </div>")

    print("    </main>")
    print("    <footer>")
    print(
        "        <p>Generated by "
        '<a href="https://github.com/aws4embeddedlinux/meta-aws-ci">'
        "meta-aws-ci</a></p>"
    )
    print("    </footer>")
    print("</body>")
    print("</html>")


if __name__ == "__main__":
    main()
