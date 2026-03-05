#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

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


def get_recipes_from_git(repo_path, branch="master"):
    """Extract recipe versions from git repository"""
    recipes = {}
    
    # Checkout the branch
    try:
        subprocess.run(
            ["git", "checkout", branch],
            cwd=repo_path,
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        return recipes
    
    # Find all .bb files
    recipes_dir = Path(repo_path) / "recipes-sdk"
    if not recipes_dir.exists():
        return recipes
    
    for bb_file in recipes_dir.rglob("*.bb"):
        # Extract recipe name and version from filename
        # Format: recipename_version.bb
        match = re.match(r"(.+?)_(.+)\.bb$", bb_file.name)
        if match:
            recipe_name = match.group(1)
            recipe_version = match.group(2)
            if recipe_version != "git":
                recipes[recipe_name] = recipe_version
            else:
                recipes[recipe_name] = "git"
    
    return recipes


def get_status_indicator(master_ver, next_ver):
    """Return status indicator based on version consistency"""
    if master_ver == "-" or master_ver == "":
        return '<span style="color: #999;">-</span>'
    if next_ver == "-" or next_ver == "":
        return '<span style="color: #28a745;">🟢</span>'
    if master_ver == next_ver:
        return '<span style="color: #28a745;">🟢</span>'
    try:
        v1 = version.parse(master_ver)
        v2 = version.parse(next_ver)
        if v1 < v2:
            return '<span style="color: #ffc107;">🟡</span>'
        return '<span style="color: #dc3545;">🔴</span>'
    except Exception:
        return '<span style="color: #ffc107;">🟡</span>'


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


def generate_detail_page(branch, all_data, all_recipes, updated):
    """Generate detailed version page for a specific branch"""
    master_recipes = all_data.get(branch, {})
    next_recipes = all_data.get(f"{branch}-next", {})
    
    html = ['<!DOCTYPE html>', '<html lang="en">', '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>meta-aws Recipe Versions - {branch}</title>',
            '    <link rel="stylesheet" href="style.css">',
            '    <style>',
            '        .version-latest { font-weight: bold; color: #28a745; }',
            '        .version-oldest { color: #dc3545; }',
            '        .version-mid { color: #ffc107; }',
            '        .next-col { background: #f8f9fa; font-style: italic; }',
            '        .report-header { background: white; padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; }',
            '        .back-link { color: #ff9900; text-decoration: none; }',
            '        .back-link:hover { text-decoration: underline; }',
            '    </style>',
            '</head>', '<body>', '    <header>',
            '        <h1>meta-aws Recipe Versions</h1>',
            f'        <h2>{branch} vs {branch}-next</h2>',
            '    </header>', '    <main>',
            '        <div class="report-header">',
            '            <p><a href="recipe-versions.html" class="back-link">← Back to Overview</a></p>',
            f'            <p><strong>Last Updated:</strong> {updated}</p>',
            '            <p><strong>Legend:</strong> 🟢 Latest version | 🟡 Mid-range version | 🔴 Oldest version</p>',
            '        </div>',
            '        <table>', '            <thead>', '                <tr>',
            '                    <th>Recipe</th>',
            f'                    <th>{branch}</th>',
            f'                    <th class="next-col">{branch}-next</th>',
            '                </tr>', '            </thead>', '            <tbody>']
    
    for recipe in sorted(all_recipes):
        master_ver = master_recipes.get(recipe, "-")
        next_ver = next_recipes.get(recipe, "-")
        versions = [master_ver, next_ver]
        colored = [color_version_html(v, versions) for v in versions]
        
        html.append('                <tr>')
        html.append(f'                    <td><strong>{recipe}</strong></td>')
        html.append(f'                    <td>{colored[0]}</td>')
        html.append(f'                    <td class="next-col">{colored[1]}</td>')
        html.append('                </tr>')
    
    html.extend(['            </tbody>', '        </table>', '    </main>',
                 '    <footer>',
                 '        <p>Generated by <a href="https://github.com/aws4embeddedlinux/meta-aws-ci">meta-aws-ci</a></p>',
                 '    </footer>', '</body>', '</html>'])
    
    return '\n'.join(html)


def main():
    print("Fetching current Yocto releases...", file=sys.stderr)
    releases = get_current_releases()
    branches = ["master"] + releases
    print(f"Found releases: {', '.join(branches)}", file=sys.stderr)

    all_data = {}
    
    # Clone meta-aws repository to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "meta-aws"
        print(f"Cloning meta-aws repository...", file=sys.stderr)
        subprocess.run(
            ["git", "clone", "--quiet", "https://github.com/aws4embeddedlinux/meta-aws.git", str(repo_path)],
            check=True
        )
        
        for branch in branches:
            for suffix in ["", "-next"]:
                branch_name = f"{branch}{suffix}"
                try:
                    print(f"Fetching {branch_name}...", file=sys.stderr)
                    recipes = get_recipes_from_git(repo_path, branch_name)
                    if recipes:
                        all_data[branch_name] = recipes
                    else:
                        print(f"No recipes found in {branch_name}", file=sys.stderr)
                except Exception as e:
                    print(f"Skipping {branch_name}: {e}", file=sys.stderr)
                    continue

    all_recipes = set()
    for recipes in all_data.values():
        all_recipes.update(recipes.keys())

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Generate detail pages
    docs_dir = Path("docs")
    for branch in branches:
        if branch in all_data:
            detail_html = generate_detail_page(branch, all_data, all_recipes, updated)
            detail_file = docs_dir / f"recipe-versions-{branch}.html"
            detail_file.write_text(detail_html)
            print(f"Generated {detail_file}", file=sys.stderr)

    # Generate main overview page
    print("<!DOCTYPE html>")
    print('<html lang="en">')
    print("<head>")
    print('    <meta charset="UTF-8">')
    print('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    print("    <title>meta-aws Recipe Versions</title>")
    print('    <link rel="stylesheet" href="style.css">')
    print("    <style>")
    print("        .status-cell { text-align: center; font-size: 1.5em; }")
    print("        .status-cell a { text-decoration: none; }")
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
    print("        <h2>Version Status Overview</h2>")
    print("    </header>")
    print("    <main>")
    print('        <div class="report-header">')
    print(
        '            <p><a href="index.html" class="back-link">'
        "← Back to Dashboard</a></p>"
    )
    print(f"            <p><strong>Last Updated:</strong> {updated}</p>")
    print(
        "            <p><strong>Legend:</strong> 🟢 All versions match | "
        "🟡 Minor differences | 🔴 Major differences</p>"
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
        print("                <tr>")
        print(f"                    <td><strong>{recipe}</strong></td>")
        for branch in branches:
            master_ver = all_data.get(branch, {}).get(recipe, "-")
            next_ver = all_data.get(f"{branch}-next", {}).get(recipe, master_ver)
            status = get_status_indicator(master_ver, next_ver)
            print(f'                    <td class="status-cell"><a href="recipe-versions-{branch}.html">{status}</a></td>')
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
