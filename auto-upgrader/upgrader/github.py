import logging
import os
from pathlib import Path
from typing import Iterable, Optional

import click
from github import Github

logger = logging.getLogger(__name__)


@click.command()
@click.option("--branch-file", type=click.Path(exists=True))
@click.option("--target-branch", type=str)
@click.option("--repo", type=str)
@click.argument("branches", nargs=-1)
def create_pulls(
    target_branch: str, repo: str, branch_file: Optional[Path], branches: Iterable[str]
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
    branches : Iterable[str]
        A list of branches to create pull requests for. Mutually
        exclusive with branch_file.
    """
    if branch_file is not None:
        logger.debug(f"creating branch list from file {branch_file}")
        with open(branch_file) as f:
            branches = [s.strip() for s in f.readlines()]
    logger.info(f"creating pulls for branches {branches}")
    _create_prs(target_branch, repo, branches)


def _create_prs(target_branch: str, repo: str, branches: Iterable[str]) -> None:
    assert "GITHUB_TOKEN" in os.environ, "GITHUB_TOKEN not found in env"
    token = os.environ.get("GITHUB_TOKEN")
    gh = Github(token)
    gh_repo = gh.get_repo(repo)
    for branch in branches:
        gh_repo.create_pull(
            base=target_branch, head=branch, title=branch, body="Automatically created."
        )
