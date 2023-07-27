from importlib.metadata import entry_points

from .main import main


def run_cli():
    _add_default_commands()
    _add_extension_commands()
    main()


def _add_default_commands():
    from . import input
    main.add_command(input.input_py)

    from . import create
    main.add_command(create.create_input_py)
    main.add_command(create.create_config)
    main.add_command(create.create_project)

    from . import shell
    main.add_command(shell.shell)

    from . import solve
    main.add_command(solve.solve)


def _add_extension_commands():
    commands = entry_points(group="pyroll.cli.commands")

    for c in commands:
        main.add_command(c.load())
