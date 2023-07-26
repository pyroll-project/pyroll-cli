import importlib.util
import logging.config
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import List
from importlib.metadata import entry_points

import click
import click_repl
import jinja2
import rtoml
from .rich import console, SUPPRESS_TRACEBACKS
from rich.logging import RichHandler
from rich.pretty import pretty_repr
from prompt_toolkit.history import FileHistory

import pyroll.core
from pyroll.core import Profile, PassSequence

from pathlib import Path

RES_DIR = Path(__file__).parent / "res"
DEFAULT_INPUT_PY_FILE = Path("input.py")
DEFAULT_CONFIG_FILE = Path("config.toml")

APP_DIR = Path(click.get_app_dir("pyroll"))
GLOBAL_CONFIG_FILE = APP_DIR / "config.toml"
DEFAULT_HISTORY_FILE = APP_DIR / "shell_history"

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(RES_DIR, encoding="utf-8")
)


def run_cli():
    commands = entry_points(group="pyroll.cli.commands")

    for c in commands:
        main.add_command(c.load())

    main()


@dataclass
class State:
    sequence: PassSequence = field(default_factory=lambda: None)
    in_profile: Profile = field(default_factory=lambda: None)
    config: dict = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: None)


@click.group(chain=True)
@click.pass_context
@click.option("--config-file", "-c", default=DEFAULT_CONFIG_FILE, help="The configuration TOML file.",
              type=click.Path(dir_okay=False, path_type=Path))
@click.option("--global-config/--no-global-config", "-C/-nC", default=True, help="Whether use the global config file.")
@click.option("--plugin", "-p", multiple=True, default=[])
@click.option(
    "-d", "--dir",
    help="Change the working directory to the specified one.",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=".", show_default=True
)
def main(ctx: click.Context, config_file: Path, global_config: bool, plugin: List[str], dir: Path):
    if ctx.obj:
        return

    from . import VERSION
    console.print(f"This is [green]PyRolL CLI v{VERSION}[/green] using [b]PyRolL Core v{pyroll.core.VERSION}[/b].\n",
                  highlight=False)

    state = State()
    ctx.obj = state

    dir.mkdir(exist_ok=True)
    os.chdir(dir)

    config = dict(pyroll=dict())

    if global_config:
        if not GLOBAL_CONFIG_FILE.exists():
            APP_DIR.mkdir(exist_ok=True)
            template = JINJA_ENV.get_template("config.toml")
            result = template.render(plugins=[], config_constants={})
            GLOBAL_CONFIG_FILE.write_text(result, encoding='utf-8')
            console.print(f"Created global config file: {GLOBAL_CONFIG_FILE}")
        else:
            console.print(f"Using global config file: {GLOBAL_CONFIG_FILE}")

        config.update(rtoml.load(GLOBAL_CONFIG_FILE))

    if config_file.exists():
        console.print(f"Using local config file: {config_file.resolve()}")
        config.update(rtoml.load(config_file))

    state.config = config

    if "logging" in config:
        console.print("Configured logging from config.")

        # parse module names for traceback suppression
        for n, h in config["logging"]["handlers"].items():
            if "tracebacks_suppress" in h:
                h["tracebacks_suppress"] = [_try_parse_module_suppression(s) for s in h["tracebacks_suppress"]]

        logging.config.dictConfig(config["logging"])
    else:
        console.print("Using default logging.")
        logging.basicConfig(
            level="INFO", format='[bold]%(name)s:[/bold] %(message)s', datefmt="[%X]",
            handlers=[RichHandler(markup=True, rich_tracebacks=True, tracebacks_suppress=SUPPRESS_TRACEBACKS)]
        )
    console.print()

    state.logger = logging.getLogger("pyroll.cli")

    plugins = list(plugin)
    if "plugins" in config["pyroll"]:
        plugins += list(config["pyroll"]["plugins"])

    for p in plugins:
        try:
            importlib.import_module(p)
        except ImportError:
            state.logger.exception(f"Failed to import the plugin: '%s'", p)
            raise

    if plugins:
        state.logger.info(f"Loaded plugins: %s", pretty_repr(plugins))

    for n, v in config["pyroll"].items():
        full_name = f"pyroll.{n}"
        if isinstance(v, dict) and full_name in sys.modules:
            module = sys.modules.get(full_name, None)
            if module:
                config = getattr(module, "Config", None)
                if config:
                    config.update(v)


def _try_parse_module_suppression(key: str):
    try:
        m = importlib.import_module(key)
        p = Path(m.__file__).resolve()
        if p.name == "__init__.py":
            return str(p.parent)
        return str(p)
    except ImportError:
        return key


@main.command()
@click.option(
    "-f", "--file",
    help="File to load from.",
    type=click.Path(exists=True, dir_okay=False, writable=False, path_type=Path),
    default=DEFAULT_INPUT_PY_FILE, show_default=True
)
@click.pass_obj
def input_py(state: State, file: Path):
    """
    Reads input data from the Python script FILE.
    The script must define two attributes:

    in_profile:\t\tProfile object defining the entry shape in the first pass
    sequence:\titerable of Unit objects (RollPass or Transport) defining the pass sequence
    """

    state.logger.info(f"Reading input from: %s", file.absolute())

    try:
        spec = importlib.util.spec_from_file_location("__pyroll_input__", file)
        module = importlib.util.module_from_spec(spec)
        sys.modules["__pyroll_input__"] = module
        spec.loader.exec_module(module)
        sequence = getattr(module, "sequence")
        state.sequence = sequence if isinstance(sequence, PassSequence) else PassSequence(sequence)
        state.in_profile = getattr(module, "in_profile")
    except Exception as e:
        state.logger.exception("Error during reading of input file.", exc_info=e)
        raise

    state.logger.info(f"Finished reading input.")

    state.logger.info("Loaded in profile: %s", pretty_repr(state.in_profile))
    state.logger.info("Loaded pass sequence: %s", pretty_repr(state.sequence))


@main.command()
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


@main.command()
@click.option(
    "-f", "--file",
    help="File to write to.",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_CONFIG_FILE, show_default=True
)
@click.option(
    "-P/-nP", "--include-plugins/--no-include-plugins",
    help="Whether to include a list of all installed plugins. "
         "As plugins are considered: all packages in the 'pyroll' namespace package except 'core'.",
    default=True
)
@click.option(
    "-C/-nC", "--include-config-constants/--no-include-config-constants",
    help="Whether to include tables of config constants found in installed plugins. "
         "As plugins are considered: all packages in the 'pyroll' namespace package except 'core'.",
    default=True
)
@click.pass_obj
def create_config(state: State, file: Path, include_plugins: bool, include_config_constants: bool):
    """Creates a standard config in FILE that can be used with the -c option."""
    if file.exists():
        click.confirm(f"File {file} already exists, overwrite?", abort=True)

    template = JINJA_ENV.get_template("config.toml")

    import pkgutil

    if include_plugins:
        plugins = [
            "pyroll." + module.name
            for module in pkgutil.iter_modules(pyroll.__path__)
            if module.name not in ["core", "cli", "report", "export"]
        ]
    else:
        plugins = []

    if include_config_constants:
        def _gen_modules():
            modules = [
                "pyroll." + m.name
                for m in pkgutil.iter_modules(pyroll.__path__)
            ]
            for m in modules:
                try:
                    module = importlib.import_module(m)
                    sys.modules[m] = module
                    yield module
                except ImportError:
                    continue

        def _convert(value: object):
            if isinstance(value, Path):
                return str(value)
            return value

        def _gen_values(module):
            config = getattr(module, "Config", None)
            if config:
                for n in config.to_dict():
                    v = getattr(config, n)
                    try:
                        yield rtoml.dumps({n: _convert(v)})
                    except rtoml.TomlSerializationError:
                        state.logger.error(f"Could not serialize '{module.__name__}.{n}'. Skipping.")
                        continue

        config_constants = {
            m.__name__: values
            for m in _gen_modules()
            if (values := list(_gen_values(m)))
        }
    else:
        config_constants = dict()

    result = template.render(
        plugins=plugins,
        config_constants=config_constants,
    )
    file.write_text(result, encoding='utf-8')
    state.logger.info(f"Created config file: %s", file.absolute())


@main.command()
@click.option(
    "-f", "--file",
    help="File to write to.",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_INPUT_PY_FILE, show_default=True
)
@click.pass_obj
def create_input_py(state: State, file: Path):
    """Creates a sample input script in FILE that can be loaded using input-py command."""
    if file.exists():
        click.confirm(f"File {file} already exists, overwrite?", abort=True)

    content = (RES_DIR / f"input.py").read_text()
    file.write_text(content, encoding='utf-8')
    state.logger.info(f"Created input file in: {file.absolute()}")


@main.command()
@click.option(
    "-d", "--dir",
    help="Path to the project directory.",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=".", show_default=True
)
@click.pass_context
def new(ctx: click.Context, dir: Path):
    """
    Creates a new PyRoll simulation project in the directory specified by -d/--dir.
    The directory will be created if not already existing.
    Creates a config.toml and an input.py in the specified directory.
    This command is basically a shortcut for
    "pyroll -c <dir>/config.yaml create-config -P -C -f "<dir>/config.toml create-input-py -f <dir>/input.py"
    in a fresh or existing directory.
    """

    dir.mkdir(exist_ok=True)

    ctx.invoke(create_config, include_plugins=True, file=dir / DEFAULT_CONFIG_FILE)
    ctx.invoke(create_input_py, file=dir / DEFAULT_INPUT_PY_FILE)


@main.command()
@click.option(
    "--history-file",
    help="File to read/write the shell history to.",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_HISTORY_FILE, show_default=True
)
@click.pass_context
def shell(ctx, history_file):
    """Opens a shell or REPL (Read Evaluate Print Loop) for interactive usage."""

    @main.command
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
