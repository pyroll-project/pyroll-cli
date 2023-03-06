import os
import subprocess
from pyroll.cli.program import main
import click.testing


def test_create_config(tmp_path):
    runner = click.testing.CliRunner()

    os.chdir(tmp_path)
    result = runner.invoke(main, ["create-config", "-nP"])

    assert result.exit_code == 0
    print(result.output)

    f = (tmp_path / "config.toml")
    assert f.exists()
    assert "pyroll.cli" not in f.read_text()

    print(f.read_text())


def test_create_config_with_plugins(tmp_path):
    runner = click.testing.CliRunner()

    os.chdir(tmp_path)
    result = runner.invoke(main, ["create-config"])

    assert result.exit_code == 0
    print(result.output)

    f = (tmp_path / "config.toml")
    assert f.exists()
