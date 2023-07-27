import importlib
import sys
from pathlib import Path

import click as click
import rtoml

from .state import State
from ..config import DEFAULT_CONFIG_FILE, JINJA_ENV, DEFAULT_INPUT_PY_FILE, RES_DIR
import pyroll.core


@click.command()
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


@click.command()
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


@click.command()
@click.option(
    "-d", "--dir",
    help="Path to the project directory.",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=".", show_default=True
)
@click.pass_context
def create_project(ctx: click.Context, dir: Path):
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
