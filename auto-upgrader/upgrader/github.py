import logging
import os
import time
from pathlib import Path
from typing import Optional, Sequence

import click
from github import Github

logger = logging.getLogger(__name__)


@click.command()
@click.option("--branch-file", type=click.Path(exists=True))
@click.option("--target-branch", type=str)
@click.option("--repo", type=str)
@click.option("--delay", type=int)
@click.argument("branches", nargs=-1)
def create_pulls(
    target_branch: str,
    repo: str,
    delay: Optional[int],
    branch_file: Optional[Path],
    branches: Sequence[str],
) -> None:
    """
    Create pull requests.

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
    branches : Iterable[str]
        A list of branches to create pull requests for. Mutually
        exclusive with branch_file.
    """
    if branch_file is not None:
        logger.debug(f"creating branch list from file {branch_file}")
        with open(branch_file) as f:
            branches = [s.strip() for s in f.readlines()]
    if len(branches) == 0:
        logger.info("no branches to create pulls for")
    else:
        logger.info(f"creating pulls for branches {branches}")
        _create_prs(target_branch, repo, delay, branches)


def _create_prs(target_branch: str, repo: str, delay: int, branches: Sequence[str]) -> None:
    assert "GITHUB_TOKEN" in os.environ, "GITHUB_TOKEN not found in env"
    token = os.environ.get("GITHUB_TOKEN")
    gh = Github(token)
    gh_repo = gh.get_repo(repo)
    upgrade_label = gh_repo.get_label("version-upgrade")
    for branch in branches:
        pull = gh_repo.create_pull(
            base=target_branch, head=branch, title=branch, body="Automatically created."
        )
        pull.set_labels(upgrade_label)
        if delay:
            time.sleep(delay)
