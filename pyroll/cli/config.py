from pathlib import Path

import click as click
import jinja2 as jinja2

RES_DIR = Path(__file__).parent / "res"
DEFAULT_INPUT_PY_FILE = Path("input.py")
DEFAULT_CONFIG_FILE = Path("config.toml")

APP_DIR = Path(click.get_app_dir("pyroll"))
GLOBAL_CONFIG_FILE = APP_DIR / "config.toml"
DEFAULT_HISTORY_FILE = APP_DIR / "shell_history"

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(RES_DIR, encoding="utf-8")
)
