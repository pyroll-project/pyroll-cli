import subprocess
from pyroll.cli.program import RES_DIR

INPUT = (RES_DIR / f"input.py").read_text()


def test_solve(tmp_path):
    (tmp_path / "input.py").write_text(INPUT)

    result = subprocess.run(("pyroll", "input-py", "solve"), cwd=tmp_path, text=True)

    print(result.stdout)

    result.check_returncode()
