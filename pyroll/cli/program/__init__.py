from importlib.metadata import entry_points

from .main import main

from . import input

main.add_command(input.input_py)

from . import create

main.add_command(create.create_input_py)
main.add_command(create.create_config)
main.add_command(create.create_project)

from . import shell

main.add_command(shell.shell)
main.add_command(shell.reset)

from . import solve

main.add_command(solve.solve)

from . import edit

main.add_command(edit.edit)


def _add_extension_commands():
    commands = entry_points(group="pyroll.cli.commands")

    for c in commands:
        main.add_command(c.load())


def run_cli(args=None):
    _add_extension_commands()
    main(args)
