#!/usr/bin/env python3
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from packaging import version


def get_current_releases():
    url = "https://www.yoctoproject.org/development/releases/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    releases = []
    current_section = soup.find("div", id="current")
    if current_section:
        table = current_section.find("table")
        if table:
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if cols:
                    codename = cols[0].text.strip().lower()
                    if codename:
                        releases.append(codename)
    return releases


def get_recipes(branch="master"):
    url = f"https://layers.openembedded.org/layerindex/branch/{branch}/layer/meta-aws/"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    recipes = {}

    for row in soup.select("table.table tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 2:
            recipe = cols[0].text.strip()
            ver = cols[1].text.strip()
            if recipe and not any(
                month in recipe
                for month in [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ]
            ):
                recipes[recipe] = ver

    return recipes


def color_version_html(ver, versions):
    if ver == "-" or ver == "":
        return ver
    valid = [v for v in versions if v != "-" and v != ""]
    if len(set(valid)) <= 1:
        return ver
    try:
        unique = sorted(set(valid), key=lambda x: version.parse(x), reverse=True)
    except Exception:
        return ver
    if ver == unique[0]:
        return f'<span class="version-latest">🟢 {ver}</span>'
    elif ver == unique[-1]:
        return f'<span class="version-oldest">🔴 {ver}</span>'
    else:
        return f'<span class="version-mid">🟡 {ver}</span>'


def main():
    print("Fetching current Yocto releases...", file=sys.stderr)
    releases = get_current_releases()
    branches = ["master"] + releases
    print(f"Found releases: {', '.join(branches)}", file=sys.stderr)

    all_data = {}

    for branch in branches:
        try:
            print(f"Fetching {branch}...", file=sys.stderr)
            all_data[branch] = get_recipes(branch)
        except Exception as e:
            print(f"Skipping {branch}: {e}", file=sys.stderr)
            continue

    all_recipes = set()
    for recipes in all_data.values():
        all_recipes.update(recipes.keys())

    branches = list(all_data.keys())

    # Generate HTML
    print("<!DOCTYPE html>")
    print('<html lang="en">')
    print("<head>")
    print('    <meta charset="UTF-8">')
    print('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    print("    <title>meta-aws Recipe Versions</title>")
    print('    <link rel="stylesheet" href="style.css">')
    print("    <style>")
    print("        .version-latest { font-weight: bold; color: #28a745; }")
    print("        .version-oldest { color: #dc3545; }")
    print("        .version-mid { color: #ffc107; }")
    print(
        "        .report-header { background: white; "
        "padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; }"
    )
    print("        .back-link { color: #ff9900; text-decoration: none; }")
    print("        .back-link:hover { text-decoration: underline; }")
    print("    </style>")
    print("</head>")
    print("<body>")
    print("    <header>")
    print("        <h1>meta-aws Recipe Versions</h1>")
    print("        <h2>Version Matrix Across Yocto Releases</h2>")
    print("    </header>")
    print("    <main>")
    print('        <div class="report-header">')
    print(
        '            <p><a href="index.html" class="back-link">'
        "← Back to Dashboard</a></p>"
    )
    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"            <p><strong>Last Updated:</strong> {updated}</p>")
    print(
        "            <p><strong>Legend:</strong> 🟢 Latest version | "
        "🟡 Mid-range version | 🔴 Oldest version</p>"
    )
    print("        </div>")
    print("        <table>")
    print("            <thead>")
    print("                <tr>")
    print("                    <th>Recipe</th>")
    for branch in branches:
        print(f"                    <th>{branch}</th>")
    print("                </tr>")
    print("            </thead>")
    print("            <tbody>")

    for recipe in sorted(all_recipes):
        versions = [all_data[branch].get(recipe, "-") for branch in branches]
        colored = [color_version_html(v, versions) for v in versions]
        print("                <tr>")
        print(f"                    <td><strong>{recipe}</strong></td>")
        for ver in colored:
            print(f"                    <td>{ver}</td>")
        print("                </tr>")

    print("            </tbody>")
    print("        </table>")
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
