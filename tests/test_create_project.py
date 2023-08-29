from pyroll.cli.program import main
from pyroll.cli.config import RES_DIR
import click.testing
import os


def test_create_project(tmp_path):
    runner = click.testing.CliRunner()

    os.chdir(tmp_path)
    result = runner.invoke(main, ["create-project"])

    assert result.exit_code == 0
    print(result.output)

    fi = tmp_path / "input.py"
    fc = tmp_path / "config.toml"

    assert fi.exists()
    assert fc.exists()

    assert fi.read_text() == (RES_DIR / "input.py").read_text()
