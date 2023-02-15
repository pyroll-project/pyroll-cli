import subprocess
from pyroll.cli.program import RES_DIR


def test_create_input_py(tmp_path):
    result = subprocess.run(("pyroll", "create-input-py"), cwd=tmp_path, text=True)

    print(result.stdout)

    result.check_returncode()

    f = (tmp_path / "input.py")
    assert f.exists()
    assert f.read_text() == (RES_DIR / "input.py").read_text()
