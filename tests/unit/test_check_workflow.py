import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "check.yml"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_dec_018_workflow_runs_on_windows_and_calls_check_script() -> None:
    text = workflow_text()
    assert "runs-on: windows-latest" in text
    assert "python scripts/check.py" in text
    assert "push:" in text
    assert "pull_request:" in text
    assert "python-version: '3.12'" in text


def test_dec_018_workflow_uses_constraints_and_pip_check() -> None:
    text = workflow_text()
    assert "pip install -r requirements.txt -c constraints.txt" in text
    assert "pip check" in text
    assert "npm ci" in text


def test_dec_018_workflow_has_no_secrets() -> None:
    text = workflow_text()
    assert "secrets." not in text
    uses = re.findall(r"uses:\s*(\S+)", text)
    assert uses
    assert all(re.fullmatch(r"[\w./-]+@v\d+\.\d+\.\d+", use) for use in uses)
