import importlib
import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import List
import click as click
import pyroll.core
import rtoml
from rich.logging import RichHandler
from rich.pretty import pretty_repr

from .state import State
from ..config import DEFAULT_CONFIG_FILE, GLOBAL_CONFIG_FILE, APP_DIR, JINJA_ENV
from ..rich import console, SUPPRESS_TRACEBACKS


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

    from .. import VERSION
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
