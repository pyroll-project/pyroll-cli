import subprocess
from pyroll.cli.program import RES_DIR


def test_create_config(tmp_path):
    result = subprocess.run(("pyroll", "create-config", "-p", "false"), cwd=tmp_path, text=True)

    print(result.stdout)

    result.check_returncode()

    f = (tmp_path / "config.yaml")
    assert f.exists()
    assert f.read_text() == (RES_DIR / "config.yaml").read_text()


def test_create_config_with_plugins(tmp_path):
    result = subprocess.run(("pyroll", "create-config"), cwd=tmp_path, text=True)

    print(result.stdout)

    result.check_returncode()

    f = (tmp_path / "config.yaml")
    assert f.exists()
    assert "pyroll.cli" in f.read_text()
