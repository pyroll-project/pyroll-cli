import sys

import click as click

from .state import State
from ..rich import console


@click.command()
@click.pass_obj
def solve(state: State):
    """Runs the solution procedure on all loaded roll passes."""
    if state.sequence is None:
        state.logger.critical("No pass sequence loaded. Use a command like 'input-py' to load a pass sequence.")
        sys.exit(1)
    if state.in_profile is None:
        state.logger.critical("No pass sequence loaded. Use a command like 'input-py' to load a pass sequence.")
        sys.exit(1)

    with console.status("[bold green]Running solution process..."):
        try:
            state.logger.info("Starting solution process...")
            state.sequence.solve(state.in_profile)
            state.logger.info("Finished solution process.")
        except RuntimeError as e:
            state.logger.exception("Solution process failed with error:", exc_info=e)
