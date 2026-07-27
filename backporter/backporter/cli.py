"""CLI interface for the backporter tool."""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from backporter.core import BackportInput, backport

logger = logging.getLogger("backporter")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
def cli(verbose: bool) -> None:
    """Backport recipe version upgrades to release branches."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


@cli.command()
@click.option("--recipe", required=True, help="Recipe name (PN), e.g. 'python3-botocore'.")
@click.option("--version", required=True, help="New version to upgrade to.")
@click.option("--target-branch", required=True, help="Branch to backport to, e.g. 'wrynose-next'.")
@click.option("--srcrev", default=None, help="New SRCREV hash (for git-based recipes).")
@click.option(
    "--sha256sum",
    multiple=True,
    help="sha256sum in 'name=hash' format (repeatable). E.g. --sha256sum x86-64=abc123",
)
@click.option(
    "--layer-path",
    type=click.Path(exists=True),
    required=True,
    help="Path to the layer git repository.",
)
@click.option("--push/--no-push", default=False, help="Push the branch to origin after commit.")
def upgrade(
    recipe: str,
    version: str,
    target_branch: str,
    srcrev: Optional[str],
    sha256sum: tuple,
    layer_path: str,
    push: bool,
) -> None:
    """
    Backport a single recipe version upgrade to a target branch.

    Either --srcrev or one or more --sha256sum must be provided.

    Examples:

        # SRCREV-based recipe
        backporter upgrade --recipe python3-botocore --version 1.43.55 \\
            --srcrev b71d5637f58df4bc61953b80902b3c040c7af889 \\
            --target-branch wrynose-next --layer-path ./meta-aws

        # sha256sum-based recipe (multiple architectures)
        backporter upgrade --recipe corretto-21-bin --version 21.0.11.10.1 \\
            --sha256sum "x86-64=1d03a3bd..." --sha256sum "aarch64=90a07c1c..." \\
            --target-branch scarthgap-next --layer-path ./meta-aws
    """
    # Parse sha256sums
    sha256sums = {}
    for entry in sha256sum:
        if "=" not in entry:
            click.echo(f"ERROR: --sha256sum must be in 'name=hash' format, got: {entry}", err=True)
            sys.exit(1)
        name, hash_value = entry.split("=", 1)
        sha256sums[name] = hash_value

    # Validate that we have either srcrev or sha256sums
    if not srcrev and not sha256sums:
        click.echo("ERROR: Either --srcrev or --sha256sum must be provided.", err=True)
        sys.exit(1)

    input = BackportInput(
        recipe=recipe,
        version=version,
        target_branch=target_branch,
        srcrev=srcrev,
        sha256sums=sha256sums,
    )

    path = Path(layer_path)
    result = backport(path, input)

    if result.success:
        click.echo(f"✓ {result.message}")
        click.echo(f"  Branch: {result.branch_name}")

        if push:
            from backporter.core import run_git

            try:
                run_git(["push", "-u", "origin", result.branch_name], cwd=path)
                click.echo(f"  Pushed to origin/{result.branch_name}")
            except Exception as e:
                click.echo(f"  WARNING: Push failed: {e}", err=True)
                sys.exit(1)
    else:
        click.echo(f"⊘ {result.message}")
        sys.exit(
            0
            if "not found" in result.message.lower() or "skipping" in result.message.lower()
            else 1
        )


@cli.command()
@click.option(
    "--commit",
    required=True,
    help="Git commit SHA or ref to extract upgrade info from.",
)
@click.option(
    "--layer-path",
    type=click.Path(exists=True),
    required=True,
    help="Path to the layer git repository.",
)
def parse_commit(commit: str, layer_path: str) -> None:
    """
    Parse a merged upgrade commit and output the recipe, version, and hashes as JSON.

    Useful for extracting backport inputs from a master-next merge event.
    """
    from backporter.parser import parse_upgrade_commit

    path = Path(layer_path)
    result = parse_upgrade_commit(path, commit)

    if result is None:
        click.echo("ERROR: Could not parse upgrade info from commit.", err=True)
        sys.exit(1)

    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    cli()
