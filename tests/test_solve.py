from pyroll.cli.program import main
from pyroll.cli.config import RES_DIR
import click.testing
import os

INPUT = (RES_DIR / f"input.py").read_text()


def test_solve(tmp_path):
    (tmp_path / "input.py").write_text(INPUT)
    runner = click.testing.CliRunner()

    os.chdir(tmp_path)
    result = runner.invoke(main, ["input-py", "solve"])
    print(result.output)

    assert result.exit_code == 0
