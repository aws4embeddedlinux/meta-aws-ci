"""Parse merged upgrade commits to extract backport inputs."""

import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Matches commit messages like: "python3-botocore: upgrade 1.43.53 -> 1.43.55"
COMMIT_MSG_RE = re.compile(
    r"^(?P<recipe>[^:]+):\s+upgrade\s+(?P<old_version>\S+)\s*->\s*(?P<new_version>\S+)"
)

# Matches SRCREV changes in diffs
SRCREV_DIFF_RE = re.compile(r'^\+SRCREV\s*=\s*"([0-9a-f]+)"', re.MULTILINE)

# Matches SRC_URI[name.sha256sum] changes in diffs
SHA256SUM_DIFF_RE = re.compile(
    r'^\+SRC_URI\[(?P<name>[^\]]+)\.sha256sum\]\s*=\s*"(?P<hash>[0-9a-f]+)"', re.MULTILINE
)


def parse_upgrade_commit(layer_path: Path, commit_ref: str) -> Optional[Dict[str, Any]]:
    """
    Parse a commit to extract recipe upgrade information.

    Parameters
    ----------
    layer_path : Path
        Path to the git repository.
    commit_ref : str
        Git commit reference (SHA, branch, HEAD, etc.).

    Returns
    -------
    Optional[Dict[str, Any]]
        Dictionary with keys: recipe, version, srcrev (or sha256sums), old_version.
        Returns None if the commit is not a parseable upgrade.
    """
    # Get commit message
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s", commit_ref],
            cwd=layer_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        logger.error(f"Failed to read commit {commit_ref}")
        return None

    message = result.stdout.strip()
    m = COMMIT_MSG_RE.match(message)
    if not m:
        logger.info(f"Commit message does not match upgrade pattern: {message}")
        return None

    recipe = m.group("recipe")
    old_version = m.group("old_version")
    new_version = m.group("new_version")

    # Get the diff to extract new hashes
    try:
        result = subprocess.run(
            ["git", "show", commit_ref, "--", "*.bb"],
            cwd=layer_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        logger.error(f"Failed to get diff for commit {commit_ref}")
        return None

    diff = result.stdout

    # Try to find SRCREV
    srcrev_match = SRCREV_DIFF_RE.search(diff)

    # Try to find sha256sums
    sha256sum_matches = SHA256SUM_DIFF_RE.findall(diff)

    output: Dict[str, Any] = {
        "recipe": recipe,
        "version": new_version,
        "old_version": old_version,
    }

    if srcrev_match:
        output["srcrev"] = srcrev_match.group(1)
    elif sha256sum_matches:
        output["sha256sums"] = {name: hash_val for name, hash_val in sha256sum_matches}
    else:
        logger.warning(f"No SRCREV or sha256sum found in diff for {recipe}")
        return None

    return output
