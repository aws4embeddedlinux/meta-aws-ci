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


def count_changes(base_recipes, next_recipes):
    changes = 0
    for recipe in base_recipes:
        if recipe in next_recipes and base_recipes[recipe] != next_recipes[recipe]:
            changes += 1
    for recipe in next_recipes:
        if recipe not in base_recipes:
            changes += 1
    return changes


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


def generate_branch_page(branch, base_recipes, next_recipes, all_recipes):
    """Generate detailed page for a specific branch"""
    print(f"Generating {branch} detail page...", file=sys.stderr)
    
    filename = f"docs/recipe-versions-{branch}.html"
    with open(filename, "w") as f:
        f.write("<!DOCTYPE html>\n")
        f.write('<html lang="en">\n<head>\n')
        f.write('    <meta charset="UTF-8">\n')
        f.write('    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        f.write(f"    <title>meta-aws: {branch} Recipe Versions</title>\n")
        f.write('    <link rel="stylesheet" href="style.css">\n')
        f.write("    <style>\n")
        f.write("        .version-latest { font-weight: bold; color: #28a745; }\n")
        f.write("        .version-changed { background: #fff3cd; font-weight: bold; }\n")
        f.write("        .version-new { background: #d4edda; }\n")
        f.write("        .next-col { background: #f8f9fa; font-style: italic; }\n")
        f.write("        .report-header { background: white; padding: 1.5rem; ")
        f.write("margin-bottom: 1rem; border-radius: 8px; }\n")
        f.write("        .back-link { color: #ff9900; text-decoration: none; }\n")
        f.write("        .back-link:hover { text-decoration: underline; }\n")
        f.write("    </style>\n</head>\n<body>\n")
        f.write("    <header>\n")
        f.write(f"        <h1>meta-aws: {branch}</h1>\n")
        f.write("        <h2>Current vs Upcoming (Monday Release)</h2>\n")
        f.write("    </header>\n    <main>\n")
        f.write('        <div class="report-header">\n')
        f.write('            <p><a href="recipe-versions.html" class="back-link">')
        f.write("← Back to All Releases</a></p>\n")
        updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        f.write(f"            <p><strong>Last Updated:</strong> {updated}</p>\n")
        changes = count_changes(base_recipes, next_recipes)
        f.write(f"            <p><strong>Pending Changes:</strong> {changes} recipes ")
        f.write("will update on Monday</p>\n")
        f.write("        </div>\n        <table>\n            <thead>\n")
        f.write("                <tr>\n")
        f.write(f"                    <th>Recipe</th>\n")
        f.write(f"                    <th>{branch}</th>\n")
        f.write(f'                    <th class="next-col">{branch}-next</th>\n')
        f.write("                </tr>\n            </thead>\n            <tbody>\n")
        
        for recipe in sorted(all_recipes):
            base_ver = base_recipes.get(recipe, "-")
            next_ver = next_recipes.get(recipe, "-")
            
            base_class = ""
            next_class = "next-col"
            if base_ver != next_ver:
                if base_ver == "-":
                    base_class = ' class="version-new"'
                    next_class = "next-col version-new"
                else:
                    base_class = ' class="version-changed"'
                    next_class = "next-col version-changed"
            
            f.write("                <tr>\n")
            f.write(f"                    <td><strong>{recipe}</strong></td>\n")
            f.write(f"                    <td{base_class}>{base_ver}</td>\n")
            f.write(f'                    <td class="{next_class}">{next_ver}</td>\n')
            f.write("                </tr>\n")
        
        f.write("            </tbody>\n        </table>\n    </main>\n")
        f.write("    <footer>\n")
        f.write('        <p>Generated by <a href="https://github.com/')
        f.write('aws4embeddedlinux/meta-aws-ci">meta-aws-ci</a></p>\n')
        f.write("    </footer>\n</body>\n</html>\n")


def main():
    print("Fetching current Yocto releases...", file=sys.stderr)
    releases = get_current_releases()
    branches = ["master"] + releases
    print(f"Found releases: {', '.join(branches)}", file=sys.stderr)

    all_data = {}
    next_data = {}

    for branch in branches:
        try:
            print(f"Fetching {branch}...", file=sys.stderr)
            all_data[branch] = get_recipes(branch)
            try:
                next_data[branch] = get_recipes(f"{branch}-next")
            except Exception:
                next_data[branch] = {}
        except Exception as e:
            print(f"Skipping {branch}: {e}", file=sys.stderr)
            continue

    all_recipes = set()
    for recipes in all_data.values():
        all_recipes.update(recipes.keys())
    for recipes in next_data.values():
        all_recipes.update(recipes.keys())

    # Generate per-branch detail pages
    for branch in all_data.keys():
        branch_recipes = set(all_data[branch].keys())
        if branch in next_data:
            branch_recipes.update(next_data[branch].keys())
        generate_branch_page(branch, all_data[branch], next_data.get(branch, {}), branch_recipes)

    # Generate main summary page
    branches = list(all_data.keys())
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
    print("        .next-col { background: #f8f9fa; font-style: italic; }")
    print("        .changes-badge { background: #ffc107; color: #000; ")
    print("padding: 2px 8px; border-radius: 12px; font-size: 0.85em; }")
    print(
        "        .report-header { background: white; "
        "padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; }"
    )
    print("        .back-link { color: #ff9900; text-decoration: none; }")
    print("        .back-link:hover { text-decoration: underline; }")
    print("        .branch-link { color: #0066cc; text-decoration: none; }")
    print("        .branch-link:hover { text-decoration: underline; }")
    print("    </style>")
    print("</head>")
    print("<body>")
    print("    <header>")
    print("        <h1>meta-aws Recipe Versions</h1>")
    print("        <h2>Version Matrix: master + master-next</h2>")
    print("    </header>")
    print("    <main>")
    print('        <div class="report-header">')
    print(
        '            <p><a href="index.html" class="back-link">'
        "← Back to Dashboard</a></p>"
    )
    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"            <p><strong>Last Updated:</strong> {updated}</p>")
    print("            <p><strong>View by Release:</strong> ")
    for i, branch in enumerate(branches):
        changes = count_changes(all_data[branch], next_data.get(branch, {}))
        badge = f' <span class="changes-badge">{changes}</span>' if changes > 0 else ""
        sep = " | " if i > 0 else ""
        print(
            f'{sep}<a href="recipe-versions-{branch}.html" class="branch-link">'
            f"{branch}{badge}</a>",
            end="",
        )
    print("</p>")
    print(
        "            <p><strong>Legend:</strong> 🟢 Latest version | "
        "🟡 Mid-range version | 🔴 Oldest version</p>"
    )
    print("        </div>")
    print("        <table>")
    print("            <thead>")
    print("                <tr>")
    print("                    <th>Recipe</th>")
    print("                    <th>master</th>")
    print('                    <th class="next-col">master-next</th>')
    print("                </tr>")
    print("            </thead>")
    print("            <tbody>")

    master_recipes = all_data.get("master", {})
    master_next_recipes = next_data.get("master", {})
    display_recipes = set(master_recipes.keys()) | set(master_next_recipes.keys())

    for recipe in sorted(display_recipes):
        master_ver = master_recipes.get(recipe, "-")
        master_next_ver = master_next_recipes.get(recipe, "-")
        
        print("                <tr>")
        print(f"                    <td><strong>{recipe}</strong></td>")
        print(f"                    <td>{master_ver}</td>")
        print(f'                    <td class="next-col">{master_next_ver}</td>')
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
