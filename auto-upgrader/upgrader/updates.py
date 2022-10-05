import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from upgrader.proc import run

logger = logging.getLogger(__name__)

RECIPE_NAME_RE = r"^(?P<name>[^_]+)_(?P<version>.+).bb$"

EXCLUDE: List[str] = []  # TODO: Allow this to be passed as an argument.
# e.g. w/ click https://click.palletsprojects.com/en/8.1.x/options/#multiple-options

BRANCH_FILE = "branches.txt"


@click.command()
@click.option("--root", type=click.Path(exists=True))
def find_recipes(root: Path) -> List[str]:
    """
    Find recipe bitbake files in a layer.

    Parameters
    ----------
    root : Path
        The path to the root of the layer.

    Returns
    -------
    List[str]
        The list of recipes by PN. e.g. boto3_1.25.66.bb becomes boto3
    """
    return _find_recipes(root)


def _find_recipes(root: Path) -> List[str]:
    recipes = set()
    for top, _, files in os.walk(root):
        for fname in files:
            m = re.search(RECIPE_NAME_RE, fname)
            if m:
                if all([m.group("name").find(x) for x in EXCLUDE]):
                    logger.info(f"selecting recipe {top}/{fname}")
                    recipes.add(m.group("name"))
                else:
                    logger.info(f"excluding recipe {top}/{fname}")
            if not m and fname.endswith(".bb"):
                logger.warn(f"possible recipe did not match: {fname}")
    return list(recipes)


@click.command()
@click.option("--recipe", type=str)
def check_for_updates(recipe: str) -> bool:
    """
    Check for updates for a recipe using devtool.

    Parameters
    ----------
    recipe : str
        The PN of the recipe to check.
    """
    return _check_for_updates(recipe) is not None


def _check_for_updates(recipe: str) -> Optional[dict]:
    (_, stderr, _) = run(f"devtool check-upgrade-status {recipe}")
    update_re = r"INFO:\s+" + recipe + r"\s+([^\s]+)\s+([^\s]+)"
    m = re.search(update_re, stderr)
    if m:
        logger.info(f"Update for {recipe}:\t{m.group(1)}\t->\t{m.group(2)}")
        return {"recipe": recipe, "previous_version": m.group(1), "next_version": m.group(2)}
    else:
        logger.info(f"No update found for {recipe}.")
        return None


@click.command()
@click.option("--layer-path", type=click.Path(exists=True))
@click.option("--target-branch", type=str, default="master-next")
def update(layer_path: Path, target_branch: str) -> None:
    """
    Update recipes in a layer with devtool.

    Parameters
    ----------
    layer_path : Path
        The path to the root of the layer.
    target_branch : str
        The branch to check for updates on.
    """
    logger.info("checking for recipe updates...")
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    Path(BRANCH_FILE).touch()

    # TODO(glimsdal): Convert Any to Union[str, NewType of upgrade]
    result: Dict[str, List[Any]] = {"success": list(), "fail": list(), "no_upgrade": list()}

    run(f"git -C {layer_path} checkout {target_branch}")

    # Find all recipes
    all_recipes = _find_recipes(layer_path)

    # Find just upgradable recipes
    upgradable_recipes = list()
    for recipe in all_recipes:
        upgrade = _check_for_updates(recipe)
        if upgrade:
            upgradable_recipes.append(upgrade)
        else:
            result["no_upgrade"].append(recipe)

    for upgrade in upgradable_recipes:
        # Skip if ref is ^{}
        if upgrade.get("next_version") == "^{}":
            logger.error(f"error getting ref for {upgrade.get('recipe')}")
            result["fail"].append(upgrade)
            continue

        run(f"git -C {layer_path} checkout {target_branch}")

        # Attempt upgrade
        (_, _, ret) = run(f"devtool upgrade {upgrade.get('recipe')}")
        if ret != 0:
            logger.warn(f"upgrading {upgrade.get('recipe')} failed. return code was {ret}")
            result["fail"].append(upgrade)
            continue

        # Create new branch
        new_branch = f"{date}_{target_branch}_{upgrade.get('recipe')}"
        commit_msg = (
            f"{upgrade.get('recipe')}: upgrade {upgrade.get('previous_version')} "
            f"-> {upgrade.get('next_version')}"
        )
        run(f"git -C {layer_path} checkout -b {new_branch} {target_branch}")

        # Finalize recipe
        (_, _, ret) = run(
            f"devtool finish --force --force-patch-refresh {upgrade.get('recipe')} {layer_path}"
        )
        if ret != 0:
            logger.warn(f"finishing {upgrade.get('recipe')} failed. return code was {ret}")
            result["fail"].append(upgrade)
            continue

        # Commit upgrade
        run(f"git -C {layer_path} add --all")
        run(f'git -C {layer_path} commit -a -m "{commit_msg}"')

        with open(BRANCH_FILE, "a") as f:
            f.write(new_branch + "\n")
        result["success"].append(upgrade)

    with open("result.json", "w") as f:
        json.dump(result, f)
