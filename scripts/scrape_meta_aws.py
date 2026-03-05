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
    """Extract recipe versions from git repository with category and path info"""
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
    
    # Find all .bb files in all recipes-* directories
    for recipes_dir in Path(repo_path).glob("recipes-*"):
        if not recipes_dir.is_dir():
            continue
        
        category = recipes_dir.name  # e.g., "recipes-iot"
        
        for bb_file in recipes_dir.rglob("*.bb"):
            # Extract recipe name and version from filename
            # Format: recipename_version.bb
            match = re.match(r"(.+?)_(.+)\.bb$", bb_file.name)
            if match:
                recipe_name = match.group(1)
                recipe_version = match.group(2)
                
                # Get subdirectory path relative to recipes-* directory
                subdir = bb_file.parent.relative_to(recipes_dir)
                
                if recipe_version != "git":
                    recipes[recipe_name] = {
                        "version": recipe_version,
                        "category": category,
                        "path": str(subdir)
                    }
                else:
                    recipes[recipe_name] = {
                        "version": "git",
                        "category": category,
                        "path": str(subdir)
                    }
    
    return recipes


def get_status_indicator(master_ver, next_ver):
    """Return status indicator based on version consistency"""
    # Handle dict format
    if isinstance(master_ver, dict):
        master_ver = master_ver.get("version", "-")
    if isinstance(next_ver, dict):
        next_ver = next_ver.get("version", "-")
    
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
    # Handle dict format
    if isinstance(ver, dict):
        ver = ver.get("version", "-")
    
    if ver == "-" or ver == "":
        return ver
    valid = [v.get("version", "-") if isinstance(v, dict) else v for v in versions if (v.get("version", "-") if isinstance(v, dict) else v) not in ["-", ""]]
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
            '        .category-header { background: #f0f0f0; font-weight: bold; }',
            '        .recipe-path { font-size: 0.75em; color: #666; font-style: italic; }',
            '    </style>',
            '</head>', '<body>', '    <header>',
            '        <h1>meta-aws Recipe Versions</h1>',
            f'        <h2>{branch} vs {branch}-next</h2>',
            '    </header>', '    <main>',
            '        <div class="report-header">',
            '            <p><a href="recipe-versions.html" class="back-link">← Back to Overview</a></p>',
            f'            <p><strong>Last Updated:</strong> {updated}</p>',
            f'            <p><strong>Comparing:</strong> {branch} branch vs {branch}-next branch from meta-aws git repository</p>',
            '            <p><strong>Legend:</strong> 🟢 Newest version | 🟡 Mid version | 🔴 Oldest version (comparing branch vs branch-next)</p>',
            '        </div>',
            '        <table>', '            <thead>', '                <tr>',
            '                    <th>Recipe</th>',
            f'                    <th>{branch}</th>',
            f'                    <th class="next-col">{branch}-next</th>',
            '                </tr>', '            </thead>', '            <tbody>']
    
    # Group recipes by category
    recipes_by_category = {}
    for recipe in all_recipes:
        recipe_info = master_recipes.get(recipe) or next_recipes.get(recipe)
        if recipe_info and isinstance(recipe_info, dict):
            category = recipe_info.get("category", "unknown")
            if category not in recipes_by_category:
                recipes_by_category[category] = []
            recipes_by_category[category].append(recipe)
    
    # Generate rows grouped by category
    for category in sorted(recipes_by_category.keys()):
        # Category header
        html.append(f'                <tr class="category-header">')
        html.append(f'                    <td colspan="3">{category}</td>')
        html.append('                </tr>')
        
        for recipe in sorted(recipes_by_category[category]):
            master_info = master_recipes.get(recipe, {})
            next_info = next_recipes.get(recipe, {})
            
            master_ver = master_info.get("version", "-") if isinstance(master_info, dict) else master_info
            next_ver = next_info.get("version", "-") if isinstance(next_info, dict) else next_info
            recipe_path = master_info.get("path", "") if isinstance(master_info, dict) else ""
            
            versions = [master_ver, next_ver]
            colored = [color_version_html(v, versions) for v in versions]
            
            html.append(f'                <tr id="{recipe}">')
            recipe_display = f'<strong>{recipe}</strong>'
            if recipe_path and recipe_path != ".":
                recipe_display += f'<br><span class="recipe-path">{recipe_path}</span>'
            html.append(f'                    <td>{recipe_display}</td>')
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
    print("        .category-header { background: #f0f0f0; font-weight: bold; }")
    print("        .recipe-path { font-size: 0.75em; color: #666; font-style: italic; }")
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
        "            <p><strong>What this shows:</strong> Version status comparing each release branch "
        "against its -next branch (e.g., master vs master-next). "
        "Click any indicator to see version details.</p>"
    )
    print(
        "            <p><strong>Legend:</strong> "
        "🟢 Versions in sync | "
        "🟡 Newer in -next branch | "
        "🔴 Older in -next branch | "
        "- Not in this release</p>"
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

    # Group recipes by category
    recipes_by_category = {}
    for recipe in all_recipes:
        # Get recipe info from any branch to determine category
        recipe_info = None
        for branch in branches:
            recipe_info = all_data.get(branch, {}).get(recipe)
            if recipe_info:
                break
        
        if recipe_info and isinstance(recipe_info, dict):
            category = recipe_info.get("category", "unknown")
            if category not in recipes_by_category:
                recipes_by_category[category] = []
            recipes_by_category[category].append(recipe)
    
    # Generate rows grouped by category
    for category in sorted(recipes_by_category.keys()):
        # Category header
        print(f'                <tr class="category-header">')
        print(f'                    <td colspan="{len(branches) + 1}">{category}</td>')
        print('                </tr>')
        
        for recipe in sorted(recipes_by_category[category]):
            print("                <tr>")
            
            # Get recipe path from first available branch
            recipe_path = ""
            for branch in branches:
                recipe_info = all_data.get(branch, {}).get(recipe)
                if recipe_info and isinstance(recipe_info, dict):
                    recipe_path = recipe_info.get("path", "")
                    break
            
            recipe_display = f"<strong>{recipe}</strong>"
            if recipe_path and recipe_path != ".":
                recipe_display += f'<br><span class="recipe-path">{recipe_path}</span>'
            
            print(f"                    <td>{recipe_display}</td>")
            
            for branch in branches:
                master_info = all_data.get(branch, {}).get(recipe, {})
                next_info = all_data.get(f"{branch}-next", {}).get(recipe, {})
                
                master_ver = master_info.get("version", "-") if isinstance(master_info, dict) else master_info if master_info else "-"
                next_ver = next_info.get("version", "-") if isinstance(next_info, dict) else next_info if next_info else master_ver
                
                status = get_status_indicator(master_ver, next_ver)
                print(f'                    <td class="status-cell"><a href="recipe-versions-{branch}.html#{recipe}">{status}</a></td>')
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
