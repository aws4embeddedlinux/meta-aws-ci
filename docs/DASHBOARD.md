# CI Dashboard Documentation

## Overview

The CI Dashboard provides automated reporting for the aws4embeddedlinux organization. Reports are generated daily via GitHub Actions and published to GitHub Pages.

**Dashboard URL**: https://aws4embeddedlinux.github.io/meta-aws-ci/

## Reports

### 1. Recipe Versions
- **File**: `docs/recipe-versions.html`
- **Script**: `scripts/scrape_meta_aws.py`
- **Workflow**: `.github/workflows/scrape-recipes.yml`
- **Schedule**: Daily at 00:00 UTC
- **Description**: Tracks meta-aws recipe versions across all Yocto releases (master, scarthgap, kirkstone, etc.)
- **Data Source**: layers.openembedded.org

### 2. Issues & Pull Requests
- **File**: `docs/issues.html`
- **Script**: `scripts/report_issues.py`
- **Workflow**: `.github/workflows/report-issues.yml`
- **Schedule**: Daily at 01:00 UTC
- **Description**: Lists all open issues and PRs across all aws4embeddedlinux repositories
- **Data Source**: GitHub API via `gh` CLI

### 3. Security Alerts
- **File**: `docs/security.html`
- **Script**: `scripts/report_security.py`
- **Workflow**: `.github/workflows/report-security.yml`
- **Schedule**: Daily at 02:00 UTC
- **Description**: Summarizes Dependabot security alerts by severity across all repositories
- **Data Source**: GitHub Dependabot API via `gh` CLI

## Tracked Repositories

- aws4embeddedlinux-ci
- meta-aws
- aws4embeddedlinux-ci-examples
- demo-auto-aws-iotfleetwise
- demo-iot-automotive-cloud
- demo-iot-automotive-embeddedlinux-image
- demo-iot-automotive-mcu
- demo-iot-automotive-simulator
- meta-aws-buildbot
- meta-aws-ci
- meta-aws-demos
- meta-aws-ewaol

## Manual Workflow Execution

To manually trigger any report:

1. Go to the [Actions tab](https://github.com/aws4embeddedlinux/meta-aws-ci/actions)
2. Select the workflow (e.g., "Scrape meta-aws recipes")
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

## Adding New Reports

To add a new report to the dashboard:

1. **Create the script** in `scripts/` directory
   - Output HTML to stdout
   - Use existing scripts as templates
   - Include proper error handling

2. **Create the workflow** in `.github/workflows/`
   - Schedule appropriately (stagger times to avoid conflicts)
   - Set `GH_TOKEN` environment variable if using GitHub API
   - Commit output to `docs/` directory

3. **Update dashboard** (`docs/index.html`)
   - Add new card in the dashboard grid
   - Link to the new report HTML file
   - Add JavaScript to check report availability

4. **Update this documentation**
   - Add report details to the Reports section
   - Update any relevant lists

## Troubleshooting

### Workflow Fails
- Check workflow logs in Actions tab
- Verify `gh` CLI has proper permissions
- Ensure Python dependencies are installed

### Report Not Updating
- Check if workflow ran successfully
- Verify commit was pushed (check git history)
- Clear browser cache and reload

### Missing Data
- Some repositories may have restricted access
- Dependabot alerts require appropriate permissions
- External data sources (layers.openembedded.org) may be temporarily unavailable

## Local Development

To test scripts locally:

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Test recipe scraper
python scripts/scrape_meta_aws.py > test-recipes.html

# Test issues report (requires gh CLI authenticated)
python scripts/report_issues.py > test-issues.html

# Test security report (requires gh CLI authenticated)
python scripts/report_security.py > test-security.html
```

## Maintenance

### Updating Repository List

If repositories are added or removed from the organization:

1. Update the `REPOS` list in:
   - `scripts/report_issues.py`
   - `scripts/report_security.py`
2. Update this documentation
3. Commit and push changes

### Modifying Schedules

Edit the `cron` expression in workflow files:
- Format: `minute hour day month weekday`
- Use [crontab.guru](https://crontab.guru/) for help
- Stagger schedules to avoid conflicts

## Architecture

```
meta-aws-ci/
├── docs/                          # GitHub Pages source
│   ├── index.html                 # Dashboard landing page
│   ├── style.css                  # Shared styles
│   ├── recipe-versions.html       # Generated report
│   ├── issues.html                # Generated report
│   └── security.html              # Generated report
├── scripts/                       # Report generators
│   ├── scrape_meta_aws.py
│   ├── report_issues.py
│   ├── report_security.py
│   └── requirements.txt
└── .github/workflows/             # Automation
    ├── scrape-recipes.yml
    ├── report-issues.yml
    └── report-security.yml
```
