from .program import main
from importlib.metadata import entry_points

if __name__ == "__main__":
    commands = entry_points(group="pyroll.cli.commands")

    for c in commands:
        main.add_command(c.load())

    main()
