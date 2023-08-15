from pathlib import Path
import click as click

from .state import State


@click.command()
@click.option(
    "-f", "--file",
    help="File to edit.",
    type=click.Path(dir_okay=False, path_type=Path, resolve_path=True),
    prompt=True
)
@click.pass_obj
def edit(state: State, file: Path):
    """Open and edit a specified file in a text editor."""
    last_change = file.stat().st_ctime if file.exists() else 0

    click.edit(filename=str(file))

    if file.stat().st_ctime - last_change > 0:
        state.logger.info("File successfully edited: %s", file)
