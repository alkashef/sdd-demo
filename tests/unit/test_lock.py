from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def load_script(name: str) -> ModuleType:
    spec = spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lock_problems(root: Path, requirements: str, constraints: str) -> list[str]:
    (root / "requirements.txt").write_text(requirements, encoding="utf-8")
    (root / "constraints.txt").write_text(constraints, encoding="utf-8")
    check = load_script("check")
    check.ROOT = root
    result: list[str] = check.lock_problems()
    return result


def test_dec_018_lock_check_passes_when_pins_match(tmp_path: Path) -> None:
    requirements = "# direct\npytest==9.1.1\nPython_Dotenv==1.2.4\n"
    constraints = "colorama==0.4.6\npytest==9.1.1\npython-dotenv==1.2.4\n"
    assert lock_problems(tmp_path, requirements, constraints) == []


def test_dec_018_lock_check_fails_when_pin_missing(tmp_path: Path) -> None:
    problems = lock_problems(tmp_path, "ruff==0.17.1\n", "pytest==9.1.1\n")
    assert len(problems) == 1
    assert "`ruff==0.17.1`" in problems[0]
    assert "found nothing" in problems[0]


def test_dec_018_lock_check_fails_when_version_differs(tmp_path: Path) -> None:
    problems = lock_problems(tmp_path, "ruff==0.17.1\n", "ruff==0.16.0\n")
    assert len(problems) == 1
    assert "found 0.16.0" in problems[0]


def test_dec_018_lock_check_fails_when_constraints_file_missing(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("ruff==0.17.1\n", encoding="utf-8")
    check = load_script("check")
    check.ROOT = tmp_path
    assert len(check.lock_problems()) == 1


def test_dec_018_lock_writes_freeze_output_to_constraints(tmp_path: Path) -> None:
    lock = load_script("lock")
    target = tmp_path / "constraints.txt"
    lock.write_constraints(lambda: "pytest==9.1.1\nruff==0.17.1\n", target)
    assert target.read_text(encoding="utf-8") == lock.HEADER + "pytest==9.1.1\nruff==0.17.1\n"
