import importlib.util
import logging.config
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List
from importlib.metadata import entry_points

import click
import yaml

import pyroll.core
from pyroll.core import Profile, PassSequence

from pathlib import Path

RES_DIR = Path(__file__).parent / "res"
DEFAULT_INPUT_PY_FILE = "input.py"
DEFAULT_CONFIG_FILE = "config.yaml"


def run_cli():
    commands = entry_points(group="pyroll.cli.commands")

    for c in commands:
        main.add_command(c.load())

    main()


@dataclass
class State:
    sequence: PassSequence = field(default_factory=list)
    in_profile: Profile = field(default_factory=lambda: None)
    config: dict = field(default_factory=dict)


@click.group(chain=True)
@click.pass_context
@click.option("--config-file", "-c", default=DEFAULT_CONFIG_FILE, help="The configuration YAML file.",
              type=click.Path())
@click.option("--plugin", "-p", multiple=True, default=[])
@click.option(
    "-d", "--dir",
    help="Change the working directory to the specified one.",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=".", show_default=True
)
def main(ctx: click.Context, config_file: Path, plugin: List[str], dir: Path):
    state = State()
    ctx.obj = state

    dir.mkdir(exist_ok=True)
    os.chdir(dir)

    config_dir = Path(click.get_app_dir("pyroll"))
    base_config_file = config_dir / "config.yaml"

    if not base_config_file.exists():
        config_dir.mkdir(exist_ok=True)
        base_config_file.write_text((Path(__file__).parent / "res" / "config.yaml").read_text())

    config = yaml.safe_load(base_config_file.read_text())

    if Path(config_file).exists():
        config.update(yaml.safe_load(Path(config_file).read_text()))

    state.config = config

    if "logging" in config:
        logging.config.dictConfig(config["logging"])
    else:
        logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s', stream=sys.stdout)

    log = logging.getLogger("pyroll.cli")

    plugins = list(plugin)
    if "plugins" in config:
        plugins += list(config["plugins"])

    for p in plugins:
        try:
            importlib.import_module(p)
        except ImportError:
            log.exception(f"Failed to import the plugin '{p}'.")
            raise

    if plugins:
        log.info(f"Loaded plugins: {plugins}.")


@main.command()
@click.option(
    "-f", "--file",
    help="File to load from.",
    type=click.Path(exists=True, dir_okay=False, writable=False, path_type=Path),
    default=DEFAULT_INPUT_PY_FILE, show_default=True
)
@click.pass_obj
@click.pass_context
def input_py(ctx, state: State, file: Path):
    """
    Reads input data from the Python script FILE.
    The script must define two attributes:

    in_profile:\t\tProfile object defining the entry shape in the first pass
    sequence:\titerable of Unit objects (RollPass or Transport) defining the pass sequence
    """

    log = logging.getLogger(__name__)
    log.info(f"Reading input from: {file.absolute()}")

    try:
        spec = importlib.util.spec_from_file_location("__pyroll_input__", file)
        module = importlib.util.module_from_spec(spec)
        sys.modules["__pyroll_input__"] = module
        spec.loader.exec_module(module)
        sequence = getattr(module, "sequence")
        state.sequence = sequence if isinstance(sequence, PassSequence) else PassSequence(sequence)
        state.in_profile = getattr(module, "in_profile")
    except:
        log.exception("Error during reading of input file.")
        raise

    log.info(f"Finished reading input.")


@main.command()
@click.pass_obj
def solve(state):
    """Runs the solution procedure on all loaded roll passes."""
    log = logging.getLogger(__name__)

    log.info("Starting solution process...")
    state.sequence.solve(state.in_profile)
    log.info("Finished solution process.")


@main.command()
@click.option(
    "-f", "--file",
    help="File to write to.",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_CONFIG_FILE, show_default=True
)
@click.option(
    "-p", "--include-plugins",
    help="Whether to include a list of all installed plugins. "
         "As plugins are considered: top-level packages whose name is starting with 'pyroll_' and "
         "all packages in the 'pyroll' namespace package except 'core', 'ui' and 'utils'.",
    type=click.BOOL,
    default=True, show_default=True
)
def create_config(file: Path, include_plugins: bool):
    """Creates a standard config in FILE that can be used with the -c option."""
    log = logging.getLogger(__name__)

    if file.exists():
        click.confirm(f"File {file} already exists, overwrite?", abort=True)

    content = (RES_DIR / "config.yaml").read_text()

    if include_plugins:
        import pkgutil
        plugins = [
                      module.name
                      for module in pkgutil.iter_modules()
                      if module.name.startswith("pyroll_")
                  ] + [
                      "pyroll." + module.name
                      for module in pkgutil.iter_modules(pyroll.__path__)
                      if module.name not in ["core", "ui", "utils"]
                  ]

        plugins_itemized = "\n".join([f"  - {p}" for p in plugins])
        if plugins_itemized:
            content = re.sub(r"plugins:(.*)\n\s*\[\]", rf"plugins:\g<1>\n{plugins_itemized}", content)

    file.write_text(content, encoding='utf-8')
    log.info(f"Created config file in: {file.absolute()}")


@main.command()
@click.option(
    "-f", "--file",
    help="File to write to.",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_INPUT_PY_FILE, show_default=True
)
def create_input_py(file: Path):
    """Creates a sample input script in FILE that can be loaded using input-py command."""
    log = logging.getLogger(__name__)

    if file.exists():
        click.confirm(f"File {file} already exists, overwrite?", abort=True)

    content = (RES_DIR / f"input.py").read_text()
    file.write_text(content, encoding='utf-8')
    log.info(f"Created input file in: {file.absolute()}")


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
    Creates a config.yaml and an input.py in the specified directory.
    This command is basically a shortcut for
    "pyroll -c <dir>/config.yaml create-config -p -f "<dir>/config.yaml create-input-py -k min -f <dir>/input.py"
    in a fresh or existing directory.
    """

    dir.mkdir(exist_ok=True)

    ctx.invoke(create_config, include_plugins=True, file=dir / DEFAULT_CONFIG_FILE)
    ctx.invoke(create_input_py, file=dir / DEFAULT_INPUT_PY_FILE)
