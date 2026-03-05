#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime

# Repository list
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


def run_gh_api(endpoint):
    """Run gh API command and return JSON output"""
    try:
        result = subprocess.run(
            ["gh", "api", endpoint], capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout) if result.stdout else []
    except subprocess.CalledProcessError as e:
        print(f"Error running gh api: {e}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return []


def get_security_alerts(repo):
    """Get Dependabot alerts for a repository"""
    print(f"Fetching security alerts for {repo}...", file=sys.stderr)

    alerts = run_gh_api(f"/repos/aws4embeddedlinux/{repo}/dependabot/alerts?state=open")

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for alert in alerts:
        severity = alert.get("security_advisory", {}).get("severity", "unknown").lower()
        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "repo": repo,
        "total": len(alerts),
        "critical": severity_counts["critical"],
        "high": severity_counts["high"],
        "medium": severity_counts["medium"],
        "low": severity_counts["low"],
        "alerts": alerts,
    }


def main():
    all_data = []

    for repo in REPOS:
        data = get_security_alerts(repo)
        all_data.append(data)

    # Calculate totals
    total_alerts = sum(d["total"] for d in all_data)
    total_critical = sum(d["critical"] for d in all_data)
    total_high = sum(d["high"] for d in all_data)
    total_medium = sum(d["medium"] for d in all_data)
    total_low = sum(d["low"] for d in all_data)

    # Generate HTML
    print("<!DOCTYPE html>")
    print('<html lang="en">')
    print("<head>")
    print('    <meta charset="UTF-8">')
    print('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    print("    <title>Security Alerts</title>")
    print('    <link rel="stylesheet" href="style.css">')
    print("    <style>")
    print(
        "        .summary-cards { display: grid; "
        "grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); "
        "gap: 1rem; margin-bottom: 2rem; }"
    )
    print(
        "        .summary-card { background: white; padding: 1rem; "
        "border-radius: 8px; text-align: center; "
        "border: 1px solid #dee2e6; }"
    )
    print("        .summary-card h3 { font-size: 2rem; margin: 0; }")
    print("        .summary-card p { margin: 0.5rem 0 0 0; color: #666; }")
    print("        .critical { color: #dc3545; }")
    print("        .high { color: #fd7e14; }")
    print("        .medium { color: #ffc107; }")
    print("        .low { color: #6c757d; }")
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
    print(
        "        .severity-badge { display: inline-block; "
        "padding: 0.25rem 0.5rem; border-radius: 4px; "
        "font-size: 0.875rem; margin-right: 0.5rem; }"
    )
    print("        .severity-badge.critical { background: #dc3545; color: white; }")
    print("        .severity-badge.high { background: #fd7e14; color: white; }")
    print("        .severity-badge.medium { background: #ffc107; color: black; }")
    print("        .severity-badge.low { background: #6c757d; color: white; }")
    print("        .no-alerts { color: #28a745; font-weight: bold; }")
    print("    </style>")
    print("</head>")
    print("<body>")
    print("    <header>")
    print("        <h1>Security Alerts</h1>")
    print("        <h2>Dependabot Vulnerability Summary</h2>")
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
    print(f"                <h3>{total_alerts}</h3>")
    print("                <p>Total Alerts</p>")
    print("            </div>")
    print('            <div class="summary-card">')
    print(f'                <h3 class="critical">{total_critical}</h3>')
    print("                <p>Critical</p>")
    print("            </div>")
    print('            <div class="summary-card">')
    print(f'                <h3 class="high">{total_high}</h3>')
    print("                <p>High</p>")
    print("            </div>")
    print('            <div class="summary-card">')
    print(f'                <h3 class="medium">{total_medium}</h3>')
    print("                <p>Medium</p>")
    print("            </div>")
    print('            <div class="summary-card">')
    print(f'                <h3 class="low">{total_low}</h3>')
    print("                <p>Low</p>")
    print("            </div>")
    print("        </div>")

    for data in all_data:
        print('        <div class="repo-section">')
        print('            <div class="repo-header">')
        print(f'                <span class="repo-name">{data["repo"]}</span>')

        if data["total"] == 0:
            print('                <span class="no-alerts">✓ No alerts</span>')
        else:
            print("                <div>")
            if data["critical"] > 0:
                print(
                    f'                    <span class="severity-badge critical">'
                    f'Critical: {data["critical"]}</span>'
                )
            if data["high"] > 0:
                print(
                    f'                    <span class="severity-badge high">'
                    f'High: {data["high"]}</span>'
                )
            if data["medium"] > 0:
                print(
                    f'                    <span class="severity-badge medium">'
                    f'Medium: {data["medium"]}</span>'
                )
            if data["low"] > 0:
                print(
                    f'                    <span class="severity-badge low">'
                    f'Low: {data["low"]}</span>'
                )
            print("                </div>")

        print("            </div>")
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
