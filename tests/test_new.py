import subprocess
from pyroll.cli.program import RES_DIR


def test_new(tmp_path):
    result = subprocess.run(("pyroll", "new"), cwd=tmp_path, text=True)

    print(result.stdout)

    result.check_returncode()

    fi = tmp_path / "input.py"
    fc = tmp_path / "config.yaml"

    assert fi.exists()
    assert fc.exists()

    assert fi.read_text() == (RES_DIR / "input.py").read_text()
