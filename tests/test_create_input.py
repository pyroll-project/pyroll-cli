import os
from pyroll.cli.program import main
from pyroll.cli.config import RES_DIR
import click.testing


def test_create_input_py(tmp_path):
    runner = click.testing.CliRunner()

    os.chdir(tmp_path)
    result = runner.invoke(main, ["create-input-py"])

    assert result.exit_code == 0
    print(result.output)

    f = (tmp_path / "input.py")
    assert f.exists()
    assert f.read_text() == (RES_DIR / "input.py").read_text()
