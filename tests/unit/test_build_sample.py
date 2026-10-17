from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"

JOBS = ["J1", "J2"]
CVS = ["C1", "C2", "C3", "C4", "C5", "C6"]
QRELS = (
    "J1\t0\tC1\t1\nJ1\t0\tC2\t1\nJ1\t0\tC3\t1\nJ1\t0\tC9\t1\n"
    "J2\t0\tC4\t1\nJ2\t0\tC5\t1\nJ2\t0\tC6\t1\nJ2\t0\tC1\t1\n"
)


def load_script() -> ModuleType:
    spec = spec_from_file_location("build_sample", SCRIPTS / "build_sample.py")
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_raw(root: Path, qrels: str = QRELS) -> Path:
    raw = root / "raw"
    (raw / "queries").mkdir(parents=True)
    (raw / "corpus").mkdir()
    for job in [*JOBS, "J3"]:
        (raw / "queries" / job).write_text(f"job {job}", encoding="utf-8")
    for cv in [*CVS, "C9"]:
        (raw / "corpus" / cv).write_text(f"cv {cv}", encoding="utf-8")
    (raw / "qrels.tsv").write_text(qrels, encoding="utf-8")
    return raw


def test_dec_010_builds_selected_jobs_and_cvs_into_output_folder(tmp_path: Path) -> None:
    raw = make_raw(tmp_path)
    out = tmp_path / "out"
    load_script().build_sample(raw, out, JOBS, CVS)
    assert sorted(p.name for p in (out / "job_descriptions").iterdir()) == ["J1.txt", "J2.txt"]
    assert sorted(p.name for p in (out / "cvs").iterdir()) == [f"{cv}.txt" for cv in CVS]
    assert (out / "cvs" / "C1.txt").read_text(encoding="utf-8") == "cv C1"
    assert (out / "job_descriptions" / "J2.txt").read_text(encoding="utf-8") == "job J2"
    assert "CC BY 4.0" in (out / "ATTRIBUTION.txt").read_text(encoding="utf-8")


def test_dec_010_each_job_has_at_least_three_labeled_cvs(tmp_path: Path) -> None:
    raw = make_raw(tmp_path)
    out = tmp_path / "out"
    with pytest.raises(ValueError, match="J1"):
        load_script().build_sample(raw, out, JOBS, ["C1", "C2", "C4", "C5", "C6"])
    assert not out.exists()


def test_dec_010_writes_ground_truth_for_selected_pairs(tmp_path: Path) -> None:
    raw = make_raw(tmp_path)
    out = tmp_path / "out"
    load_script().build_sample(raw, out, JOBS, CVS)
    lines = (out / "ground_truth.tsv").read_text(encoding="utf-8").splitlines()
    assert lines == [
        "job_id\tcv_id",
        "J1\tC1",
        "J1\tC2",
        "J1\tC3",
        "J2\tC4",
        "J2\tC5",
        "J2\tC6",
        "J2\tC1",
    ]


def test_dec_010_raw_files_are_not_modified(tmp_path: Path) -> None:
    raw = make_raw(tmp_path)
    before = {p: p.read_bytes() for p in raw.rglob("*") if p.is_file()}
    load_script().build_sample(raw, tmp_path / "out", JOBS, CVS)
    after = {p: p.read_bytes() for p in raw.rglob("*") if p.is_file()}
    assert after == before
