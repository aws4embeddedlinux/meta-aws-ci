"""Pure helpers for identifying and comparing recipe upgrades.

These functions deliberately take plain data rather than PyGithub objects so
that the decision logic can be unit tested without network access or mocks.
"""

import re
from typing import Dict, List, Optional, Sequence, Set, Tuple

# recipes-<category>/<dir>/<name>_<version>.bb  (also .bbappend)
RECIPE_FILE_RE = re.compile(
    r"(?:^|/)(?P<name>[A-Za-z0-9][A-Za-z0-9.+\-]*)_(?P<version>[^/_]+?)\.bb(?:append)?$"
)

# Preference order when a change touches several revisions of one recipe. An
# upgrade shows the new file as added/renamed and the old one as removed, so the
# added/renamed entry is the authoritative target version.
_STATUS_PREFERENCE = ("added", "renamed", "copied", "changed", "modified")

VersionKey = List[Tuple[int, int, str]]


def version_key(version: str) -> VersionKey:
    """Return a natural-sort key for a recipe version string.

    Splits on the separators BitBake versions use (``.``, ``_``, ``-``, ``+``)
    and compares numeric components numerically so that ``1.43.9`` sorts below
    ``1.43.10``.

    Versions with no digits at all -- ``_git.bb`` recipes, whose PV is derived
    from SRCREV -- have no comparable ordering. They all collapse to the same
    lowest key, which makes any two of them compare equal. Callers therefore
    fall back to recency for those recipes.
    """
    if not re.search(r"\d", version):
        return [(0, 0, "")]
    key: VersionKey = []
    for part in re.split(r"[._\-+]", version):
        if part.isdigit():
            key.append((1, int(part), ""))
        elif part:
            key.append((0, 0, part))
    return key


def recipe_and_version(
    files: Sequence[Tuple[str, str]],
) -> Optional[Tuple[str, str]]:
    """Identify the single recipe and target version a change describes.

    Parameters
    ----------
    files
        ``(filename, status)`` pairs, as reported by the GitHub compare and
        pull request file APIs. ``status`` is e.g. ``added``, ``removed``,
        ``modified``, ``renamed``.

    Returns
    -------
    ``(recipe, version)``, or ``None`` when the change touches no recipe file
    or touches more than one distinct recipe. Returning ``None`` for the
    multi-recipe case is deliberate: release fast-forward merges and layer-wide
    hygiene changes must never be treated as recipe upgrades, and so must never
    be matched against or closed.
    """
    by_status: Dict[str, Dict[str, Set[str]]] = {}
    for filename, status in files:
        match = RECIPE_FILE_RE.search(filename)
        if not match:
            continue
        bucket = by_status.setdefault(status, {})
        bucket.setdefault(match.group("name"), set()).add(match.group("version"))

    found: Dict[str, Set[str]] = {}
    for status in _STATUS_PREFERENCE:
        if by_status.get(status):
            found = by_status[status]
            break
    if not found:
        # Nothing in the preferred statuses (e.g. only 'removed'); fall back to
        # everything we saw so a deletion-only change is still identifiable.
        for bucket in by_status.values():
            for name, versions in bucket.items():
                found.setdefault(name, set()).update(versions)

    if len(found) != 1:
        return None

    name, versions = next(iter(found.items()))
    return name, max(versions, key=version_key)


# Decisions returned by ``decide``.
CREATE = "create"  # no open PR for this recipe -- create as normal
SKIP_DUPLICATE = "skip-duplicate"  # open PR already targets this same version
SUPERSEDE = "supersede"  # our version is newer -- create, then close the stale PR
SKIP_BEHIND = "skip-behind"  # open PR targets a newer version -- do not regress


def decide(candidate_version: str, existing_version: Optional[str]) -> str:
    """Decide what to do about a candidate upgrade.

    ``existing_version`` is the target version of the open pull request already
    covering this recipe on this base branch, or ``None`` if there is none.

    Equal versions are treated as duplicates rather than as supersessions. The
    auto-upgrader compares the recipe as committed on the target branch against
    upstream, so while an upgrade PR sits unmerged the same upgrade is
    rediscovered on every run. Skipping the duplicate is what stops that
    feedback loop.
    """
    if existing_version is None:
        return CREATE

    candidate = version_key(candidate_version)
    existing = version_key(existing_version)

    if candidate == existing:
        return SKIP_DUPLICATE
    if candidate > existing:
        return SUPERSEDE
    return SKIP_BEHIND
