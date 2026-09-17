"""Pure helpers for identifying and comparing recipe upgrades.

These functions deliberately take plain data rather than PyGithub objects so
that the decision logic can be unit tested without network access or mocks.
"""

import re
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

#: Label applied to pull requests that are blocked on an upstream issue.
#: Kept as a single source of truth so the same string is not repeated across
#: match, apply and comment paths.
BLOCKED_LABEL = "blocked"

#: Body/comment marker that ties a new blocked pull request back to the root
#: pull request that first reported the upstream block. The regex tolerates
#: surrounding whitespace and case so a human note stays discoverable.
BLOCKED_REFERENCE_RE = re.compile(
    r"Blocked by same upstream issue as #(?P<number>\d+)",
    re.IGNORECASE,
)

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


def find_root_reference(texts: Sequence[Optional[str]]) -> Optional[int]:
    """Return the first ``#N`` referenced by a "Blocked by same upstream issue as" marker.

    ``texts`` is the pull request body followed by comment bodies, in order.
    ``None`` entries are ignored so callers can pass ``pull.body`` directly.
    Returns ``None`` if no marker is present.
    """
    for text in texts:
        if not text:
            continue
        match = BLOCKED_REFERENCE_RE.search(text)
        if match:
            return int(match.group("number"))
    return None


def find_root_blocked_pr(
    start_number: int,
    start_texts: Sequence[Optional[str]],
    fetch_texts: Callable[[int], Optional[Sequence[Optional[str]]]],
) -> int:
    """Trace back through "Blocked by same upstream issue as #N" markers to the root.

    Parameters
    ----------
    start_number
        Number of the pull request the trace starts from.
    start_texts
        Body and comment bodies of the starting pull request, in that order.
        A pull request that does not reference an earlier one IS the root, so
        the returned number is ``start_number`` in that case.
    fetch_texts
        Resolver returning the body and comment bodies of a referenced pull
        request, or ``None`` if it cannot be fetched (deleted, private, out of
        scope). When a reference cannot be resolved the referenced number is
        returned unchanged so the operator can still investigate it.

    A cycle in the chain -- a pull request whose reference resolves to one
    already visited -- returns the pull request that closed the cycle rather
    than looping forever.
    """
    visited: Set[int] = set()
    current_number = start_number
    current_texts: Sequence[Optional[str]] = start_texts
    while True:
        if current_number in visited:
            return current_number
        visited.add(current_number)
        reference = find_root_reference(current_texts)
        if reference is None or reference == current_number:
            return current_number
        next_texts = fetch_texts(reference)
        if next_texts is None:
            # Referenced pull request is unreachable -- treat the reference
            # itself as the root so the number stays visible to the operator.
            return reference
        current_number = reference
        current_texts = next_texts


def blocked_comment_for_new_pr(root_number: int) -> str:
    """Comment posted on the new pull request that inherits the upstream block."""
    return f"Blocked by same upstream issue as #{root_number}"


def blocked_supersede_comment(new_number: int, root_number: int) -> str:
    """Closing comment posted on the old blocked pull request being superseded."""
    return (
        f"Superseded by #{new_number} (newer version). "
        f"Upstream block tracked in #{root_number}."
    )
