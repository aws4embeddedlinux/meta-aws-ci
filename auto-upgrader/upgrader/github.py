import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import click
from github import Github

from upgrader.recipes import (
    CREATE,
    SKIP_BEHIND,
    SKIP_DUPLICATE,
    SUPERSEDE,
    decide,
    recipe_and_version,
)

logger = logging.getLogger(__name__)

#: Login of the account the auto-upgrader creates pull requests as. Only pull
#: requests authored by this account are considered when looking for an existing
#: upgrade, and only they are ever closed as superseded.
BOT_LOGIN = "meta-aws-maintainer"

#: Logins whose activity on a pull request does not count as human review.
BOT_LOGINS = frozenset({BOT_LOGIN, "meta-aws-reviewer", "github-actions"})

UPGRADE_LABEL = "version-upgrade"


@click.command()
@click.option("--branch-file", type=click.Path(exists=True))
@click.option("--target-branch", type=str)
@click.option("--repo", type=str)
@click.option("--delay", type=int)
@click.option(
    "--close-superseded/--no-close-superseded",
    default=True,
    help=(
        "Close an existing open upgrade pull request when this run creates one "
        "for a newer version of the same recipe."
    ),
)
@click.option(
    "--delete-redundant-branches/--no-delete-redundant-branches",
    default=True,
    help=(
        "Delete the pushed branch when no pull request is created for it, and "
        "the branch of any pull request closed as superseded."
    ),
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Report the action for each branch without creating, closing or deleting anything.",
)
@click.argument("branches", nargs=-1)
def create_pulls(
    target_branch: str,
    repo: str,
    delay: Optional[int],
    branch_file: Optional[Path],
    close_superseded: bool,
    delete_redundant_branches: bool,
    dry_run: bool,
    branches: Sequence[str],
) -> None:
    """
    Create pull requests.

    A pull request is only created when the upgrade is not already covered by an
    open pull request. If an open pull request already targets the same version
    of the same recipe on the same base branch, this run skips it -- otherwise
    every scheduled run would open another copy of an upgrade that is waiting to
    merge. If this run has a newer version than the open pull request, the pull
    request is created and the older one is closed as superseded.

    Parameters
    ----------
    target_branch : str
        The branch to create pull requests against.
    repo : str
        The repository to create against. This is the `org/repo` name
        as recoginized by GitHub.
    branch_file : Optional[Path]
        The path to a file which lists branches to create pull requests
        for. Mutually exclusive with branches
    delay : Optional[int]
        Sleep in seconds after each pull request creation to not hit GitHub api rate limit
        and give sstate server time to be filled by the first build.
    close_superseded : bool
        Close an open upgrade pull request that this run supersedes.
    delete_redundant_branches : bool
        Delete branches left without a pull request.
    dry_run : bool
        Report intended actions without performing them.
    branches : Iterable[str]
        A list of branches to create pull requests for. Mutually
        exclusive with branch_file.
    """
    if branch_file is not None:
        logger.debug(f"creating branch list from file {branch_file}")
        with open(branch_file) as f:
            branches = [s.strip() for s in f.readlines() if s.strip()]
    if len(branches) == 0:
        logger.info("no branches to create pulls for")
    else:
        logger.info(f"creating pulls for branches {branches}")
        _create_prs(
            target_branch,
            repo,
            delay,
            branches,
            close_superseded=close_superseded,
            delete_redundant_branches=delete_redundant_branches,
            dry_run=dry_run,
        )


def _pr_recipe_and_version(pull) -> Optional[Tuple[str, str]]:
    """Identify the recipe and target version of an existing pull request."""
    files = [(f.filename, f.status) for f in pull.get_files()]
    return recipe_and_version(files)


def _branch_recipe_and_version(gh_repo, target_branch: str, branch: str):
    """Identify the recipe and target version a pushed branch would upgrade."""
    comparison = gh_repo.compare(target_branch, branch)
    files = [(f.filename, f.status) for f in comparison.files]
    return recipe_and_version(files)


def _has_human_activity(pull) -> bool:
    """Whether anyone other than the automation has reviewed or commented."""
    for review in pull.get_reviews():
        if review.user is not None and review.user.login not in BOT_LOGINS:
            return True
    for comment in pull.get_issue_comments():
        if comment.user is not None and comment.user.login not in BOT_LOGINS:
            return True
    return False


def _open_upgrade_pulls(gh_repo, target_branch: str) -> Dict[str, list]:
    """Map recipe name -> open bot-authored upgrade pull requests for it.

    Pull requests that are not authored by the automation, and those touching
    more than one recipe, are excluded. They are never matched against and never
    closed.
    """
    by_recipe: Dict[str, list] = {}
    for pull in gh_repo.get_pulls(state="open", base=target_branch):
        if pull.user is None or pull.user.login != BOT_LOGIN:
            continue
        identified = _pr_recipe_and_version(pull)
        if identified is None:
            continue
        recipe, version = identified
        by_recipe.setdefault(recipe, []).append((version, pull))
    return by_recipe


def _delete_branch(
    gh_repo, branch: str, dry_run: bool, protected: Optional[frozenset] = None
) -> None:
    """Delete a remote branch.

    Refuses to delete a branch that is still the head of an open pull request:
    deleting such a branch closes that pull request as a side effect.
    """
    if protected and branch in protected:
        logger.warning(
            f"not deleting {branch}: it is the head of an open pull request"
        )
        return
    if dry_run:
        logger.info(f"[dry-run] would delete branch {branch}")
        return
    try:
        gh_repo.get_git_ref(f"heads/{branch}").delete()
        logger.info(f"deleted branch {branch}")
    except Exception as exc:  # noqa: BLE001 - branch may already be gone
        logger.warning(f"could not delete branch {branch}: {exc}")


def _close_as_superseded(
    gh_repo, pull, new_version: str, delete_branch: bool, dry_run: bool
) -> None:
    """Close a pull request that a newer upgrade has superseded."""
    if _has_human_activity(pull):
        logger.warning(
            f"not closing #{pull.number}: it has non-automation review or comment activity"
        )
        return

    body = (
        f"Superseded by a newer upgrade to `{new_version}` of the same recipe on "
        f"`{pull.base.ref}`.\n\nClosed automatically by the auto-upgrader."
    )
    if dry_run:
        logger.info(f"[dry-run] would close #{pull.number} as superseded by {new_version}")
        return

    branch = pull.head.ref
    pull.create_issue_comment(body)
    pull.edit(state="closed")
    logger.info(f"closed #{pull.number} as superseded by {new_version}")
    if delete_branch:
        # Deliberately unprotected: we just closed this pull request, so its
        # head branch is now safe to remove.
        _delete_branch(gh_repo, branch, dry_run)


def _create_prs(
    target_branch: str,
    repo: str,
    delay: int,
    branches: Sequence[str],
    close_superseded: bool = True,
    delete_redundant_branches: bool = True,
    dry_run: bool = False,
) -> None:
    assert "GITHUB_TOKEN" in os.environ, "GITHUB_TOKEN not found in env"
    token = os.environ.get("GITHUB_TOKEN")
    gh = Github(token)
    gh_repo = gh.get_repo(repo)
    upgrade_label = gh_repo.get_label(UPGRADE_LABEL)

    existing = _open_upgrade_pulls(gh_repo, target_branch)
    open_heads = frozenset(
        pull.head.ref for pull in gh_repo.get_pulls(state="open", base=target_branch)
    )
    logger.info(
        f"found open upgrade pull requests for {len(existing)} recipe(s) on {target_branch}"
    )

    for branch in branches:
        identified = _branch_recipe_and_version(gh_repo, target_branch, branch)
        if identified is None:
            # Could not attribute the branch to a single recipe. Create the pull
            # request and let a human look at it rather than silently dropping
            # work.
            logger.warning(
                f"could not identify a single recipe for {branch}; creating pull request unconditionally"
            )
            _do_create(gh_repo, target_branch, branch, upgrade_label, delay, dry_run)
            continue

        recipe, version = identified
        candidates = existing.get(recipe, [])
        # Compare against the highest version already open for this recipe.
        current = max(candidates, key=lambda pair: pair[0]) if candidates else None
        current_version = current[0] if current else None

        action = decide(version, current_version)

        if action == CREATE:
            logger.info(f"{recipe} {version}: no open pull request; creating")
            pull = _do_create(
                gh_repo, target_branch, branch, upgrade_label, delay, dry_run
            )
            if pull is not None:
                existing.setdefault(recipe, []).append((version, pull))

        elif action == SKIP_DUPLICATE:
            logger.info(
                f"{recipe} {version}: already covered by open #{current[1].number}; skipping"
            )
            if delete_redundant_branches:
                _delete_branch(gh_repo, branch, dry_run, open_heads)

        elif action == SUPERSEDE:
            logger.info(
                f"{recipe} {version}: supersedes open #{current[1].number} "
                f"({current_version}); creating"
            )
            pull = _do_create(
                gh_repo, target_branch, branch, upgrade_label, delay, dry_run
            )
            if close_superseded:
                for open_version, open_pull in candidates:
                    _close_as_superseded(
                        gh_repo,
                        open_pull,
                        version,
                        delete_redundant_branches,
                        dry_run,
                    )
            existing[recipe] = [(version, pull)] if pull is not None else []

        elif action == SKIP_BEHIND:
            logger.warning(
                f"{recipe} {version}: open #{current[1].number} already targets "
                f"{current_version}; skipping"
            )
            if delete_redundant_branches:
                _delete_branch(gh_repo, branch, dry_run, open_heads)


def _do_create(gh_repo, target_branch, branch, upgrade_label, delay, dry_run):
    if dry_run:
        logger.info(f"[dry-run] would create pull request for {branch}")
        return None
    pull = gh_repo.create_pull(
        base=target_branch, head=branch, title=branch, body="Automatically created."
    )
    pull.set_labels(upgrade_label)
    if delay:
        time.sleep(delay)
    return pull
