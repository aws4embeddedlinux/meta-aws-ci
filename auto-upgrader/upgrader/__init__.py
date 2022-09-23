import logging

import click

from .github import create_pulls
from .updates import check_for_updates, find_recipes, update

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """A tool for automating recipe upgrades in meta-aws."""
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("upgrader.log")
    stream_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    stream_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(stream_format)
    file_handler.setFormatter(file_format)

    # Add handlers to the logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    pass


cli.add_command(create_pulls)
cli.add_command(find_recipes)
cli.add_command(check_for_updates)
cli.add_command(update)

if __name__ == "__main__":
    cli()
