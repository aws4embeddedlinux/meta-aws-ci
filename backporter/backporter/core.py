"""Core logic for backporting recipe version upgrades."""

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

RECIPE_NAME_RE = re.compile(r"^(?P<name>[^_]+)_(?P<version>.+)\.bb$")
SRCREV_RE = re.compile(r'^(SRCREV\s*=\s*")([^"]+)(")', re.MULTILINE)
SHA256SUM_RE = re.compile(
    r'^(SRC_URI\[(?P<name>[^\]]+)\.sha256sum\]\s*=\s*")([0-9a-f]+)(")', re.MULTILINE
)


@dataclass
class BackportResult:
    """Result of a backport operation."""

    recipe: str
    target_branch: str
    success: bool
    old_version: Optional[str] = None
    new_version: Optional[str] = None
    branch_name: Optional[str] = None
    message: str = ""


@dataclass
class BackportInput:
    """Input parameters for a backport operation."""

    recipe: str
    version: str
    target_branch: str
    srcrev: Optional[str] = None
    sha256sums: Dict[str, str] = field(default_factory=dict)


def find_recipe_file(layer_path: Path, recipe: str) -> Optional[Path]:
    """
    Find the current .bb file for a recipe in the layer.

    Searches recursively for a file matching `{recipe}_*.bb`.

    Parameters
    ----------
    layer_path : Path
        Root of the Yocto layer.
    recipe : str
        Recipe name (PN), e.g. "python3-botocore".

    Returns
    -------
    Optional[Path]
        Path to the recipe file, or None if not found.
    """
    for root, _, files in os.walk(layer_path):
        for fname in files:
            m = RECIPE_NAME_RE.match(fname)
            if m and m.group("name") == recipe:
                return Path(root) / fname
    return None


def get_recipe_version(recipe_path: Path) -> Optional[str]:
    """
    Extract the version from a recipe filename.

    Parameters
    ----------
    recipe_path : Path
        Path to the .bb file.

    Returns
    -------
    Optional[str]
        The version string, or None if it can't be parsed.
    """
    m = RECIPE_NAME_RE.match(recipe_path.name)
    if m:
        return m.group("version")
    return None


def update_srcrev(content: str, new_srcrev: str) -> str:
    """
    Replace the SRCREV value in recipe content.

    Parameters
    ----------
    content : str
        The recipe file content.
    new_srcrev : str
        The new SRCREV hash.

    Returns
    -------
    str
        Updated content.
    """
    new_content, count = SRCREV_RE.subn(rf"\g<1>{new_srcrev}\3", content)
    if count == 0:
        logger.warning("No SRCREV found in recipe content")
    else:
        logger.info(f"Updated {count} SRCREV occurrence(s)")
    return new_content


def update_sha256sums(content: str, sha256sums: Dict[str, str]) -> str:
    """
    Replace SRC_URI[name.sha256sum] values in recipe content.

    Parameters
    ----------
    content : str
        The recipe file content.
    sha256sums : Dict[str, str]
        Mapping of arch/name to new sha256sum, e.g. {"x86-64": "abc...", "aarch64": "def..."}.

    Returns
    -------
    str
        Updated content.
    """
    for name, new_hash in sha256sums.items():
        pattern = re.compile(
            rf'^(SRC_URI\[{re.escape(name)}\.sha256sum\]\s*=\s*")([0-9a-f]+)(")',
            re.MULTILINE,
        )
        new_content, count = pattern.subn(rf"\g<1>{new_hash}\3", content)
        if count == 0:
            logger.warning(f"No SRC_URI[{name}.sha256sum] found in recipe content")
        else:
            logger.info(f"Updated SRC_URI[{name}.sha256sum]")
            content = new_content
    return content


def run_git(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    """
    Run a git command.

    Parameters
    ----------
    args : List[str]
        Git subcommand and arguments.
    cwd : Path
        Working directory.

    Returns
    -------
    subprocess.CompletedProcess
        The completed process result.

    Raises
    ------
    subprocess.CalledProcessError
        If the git command fails.
    """
    cmd = ["git"] + args
    logger.debug(f"Running: {' '.join(cmd)} (cwd={cwd})")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)


def backport(layer_path: Path, input: BackportInput) -> BackportResult:
    """
    Perform a recipe version backport on a target branch.

    This function:
    1. Checks out the target branch
    2. Finds the current recipe file
    3. Renames it (git mv) to the new version
    4. Updates SRCREV or sha256sum(s)
    5. Commits the change

    Parameters
    ----------
    layer_path : Path
        Path to the layer git repository.
    input : BackportInput
        The backport parameters.

    Returns
    -------
    BackportResult
        The result of the operation.
    """
    recipe = input.recipe
    new_version = input.version
    target_branch = input.target_branch

    # Checkout the target branch
    try:
        run_git(["checkout", target_branch], cwd=layer_path)
    except subprocess.CalledProcessError as e:
        return BackportResult(
            recipe=recipe,
            target_branch=target_branch,
            success=False,
            message=f"Failed to checkout branch '{target_branch}': {e.stderr.strip()}",
        )

    # Find the current recipe file
    recipe_path = find_recipe_file(layer_path, recipe)
    if recipe_path is None:
        return BackportResult(
            recipe=recipe,
            target_branch=target_branch,
            success=False,
            message=f"Recipe '{recipe}' not found on branch '{target_branch}'. Skipping.",
        )

    old_version = get_recipe_version(recipe_path)
    if old_version is None:
        return BackportResult(
            recipe=recipe,
            target_branch=target_branch,
            success=False,
            message=f"Could not parse version from '{recipe_path.name}'.",
        )

    # Skip if already at or ahead of target version
    if old_version == new_version:
        return BackportResult(
            recipe=recipe,
            target_branch=target_branch,
            success=False,
            old_version=old_version,
            new_version=new_version,
            message=f"Recipe already at version {new_version}. Skipping.",
        )

    # Create a new branch for the backport
    branch_name = f"backport/{recipe}_{new_version}_to_{target_branch}"
    try:
        run_git(["checkout", "-b", branch_name], cwd=layer_path)
    except subprocess.CalledProcessError as e:
        return BackportResult(
            recipe=recipe,
            target_branch=target_branch,
            success=False,
            old_version=old_version,
            new_version=new_version,
            message=f"Failed to create branch '{branch_name}': {e.stderr.strip()}",
        )

    # Compute new file path
    new_filename = f"{recipe}_{new_version}.bb"
    new_path = recipe_path.parent / new_filename

    # git mv
    try:
        run_git(
            ["mv", str(recipe_path.relative_to(layer_path)), str(new_path.relative_to(layer_path))],
            cwd=layer_path,
        )
    except subprocess.CalledProcessError as e:
        return BackportResult(
            recipe=recipe,
            target_branch=target_branch,
            success=False,
            old_version=old_version,
            new_version=new_version,
            message=f"git mv failed: {e.stderr.strip()}",
        )

    # Read the file content and update hashes
    content = new_path.read_text()

    if input.srcrev:
        content = update_srcrev(content, input.srcrev)
    elif input.sha256sums:
        content = update_sha256sums(content, input.sha256sums)
    else:
        return BackportResult(
            recipe=recipe,
            target_branch=target_branch,
            success=False,
            old_version=old_version,
            new_version=new_version,
            message="No SRCREV or sha256sums provided. Cannot update hashes.",
        )

    # Write updated content
    new_path.write_text(content)

    # Stage and commit
    run_git(["add", "--all"], cwd=layer_path)

    commit_msg = f"{recipe}: upgrade {old_version} -> {new_version}"
    try:
        run_git(["commit", "-m", commit_msg], cwd=layer_path)
    except subprocess.CalledProcessError as e:
        return BackportResult(
            recipe=recipe,
            target_branch=target_branch,
            success=False,
            old_version=old_version,
            new_version=new_version,
            message=f"git commit failed: {e.stderr.strip()}",
        )

    return BackportResult(
        recipe=recipe,
        target_branch=target_branch,
        success=True,
        old_version=old_version,
        new_version=new_version,
        branch_name=branch_name,
        message=f"Successfully backported {recipe} {old_version} -> {new_version}",
    )
