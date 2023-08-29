from pathlib import Path

import click as click

from .main import main
from .state import State
from ..rich import console
from ..config import DEFAULT_HISTORY_FILE

import click_repl
from prompt_toolkit.history import FileHistory


@click.command()
@click.option(
    "--history-file",
    help="File to read/write the shell history to.",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_HISTORY_FILE, show_default=True
)
@click.pass_context
def shell(ctx, history_file):
    """Opens a shell or REPL (Read Evaluate Print Loop) for interactive usage."""

    @click.command
    def exit():
        """Exits the shell or REPL."""
        click_repl.exit()

    main.add_command(exit)

    console.print(
        "Launching interactive shell mode.\n"
        "Enter PyRolL CLI subcommands as you wish, state is maintained between evaluations.\n"
        "Global options (-c/--config-file, -C/--global-config, -p/--plugin, ...) do [b]not[/b] work from here, "
        "specify them when lauching `pyroll shell`.\n\n"
        "Type [b]--help[/b] for help on available subcommands.\n"
        "Type [b]exit[/b] to leave the shell.",
        highlight=False
    )

    prompt_kwargs = dict(
        history=FileHistory(str(history_file.resolve())),
        message=[("bold", "\npyroll ")]
    )
    click_repl.repl(ctx, prompt_kwargs=prompt_kwargs)


@click.command()
@click.pass_obj
@click.option(
    "-y/-n", "--yes/--no",
    help="Confirm to reset without prompt.",
    default=False,
)
def reset(state: State, yes):
    """Reset the state of the simulation data."""
    if yes or click.confirm("Reset simulation state?"):
        state.logger.info("Reset simulation state.")
        state.in_profile = None
        state.sequence = None
