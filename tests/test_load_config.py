import os
from pathlib import Path

import click.testing
from pyroll.core import Config

from pyroll.cli.program import main

CONFIG = """                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
[pyroll]
plugins = [# list of plugin packages to load
]

# configuration constants for core and plugin packages

[pyroll.core]
ROLL_PASS_AUTO_ROTATION = false
DEFAULT_MAX_ITERATION_COUNT = 50

[logging] # configuration for the logging standard library package
version = 1

formatters.console.format = '[%(levelname)s] %(name)s: %(message)s'
formatters.file.format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

[logging.handlers.console]
class = "logging.StreamHandler"
level = "INFO"
formatter = "console"
stream = "ext://sys.stdout"

[logging.handlers.file]
class = "logging.FileHandler"
level = "DEBUG"
formatter = "file"
filename = "pyroll.log"

[logging.root]
level = "WARNING"
handlers = ["console", "file"]

[logging.loggers.pyroll]
level = "DEBUG"
"""


def test_load_config(tmp_path: Path):
    runner = click.testing.CliRunner()

    os.chdir(tmp_path)
    fc = tmp_path / "config.toml"

    fc.write_text(CONFIG)

    try:
        result = runner.invoke(main, ["create-config"], input="y")

        assert result.exit_code == 0
        print(result.output)

        assert Config.ROLL_PASS_AUTO_ROTATION is False
        assert Config.DEFAULT_MAX_ITERATION_COUNT == 50

    finally:
        del Config.ROLL_PASS_AUTO_ROTATION
        del Config.DEFAULT_MAX_ITERATION_COUNT
