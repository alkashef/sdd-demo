"""Build the sample folder `data/sample/` from the raw TalentCLEF Task A files.

Copies the selected job descriptions and CVs unchanged (with a `.txt` extension added) and writes
`ground_truth.tsv` and `ATTRIBUTION.txt`. Does NOT modify the raw files, and writes nothing when
a job has fewer than three labeled CVs among the selected ones. Implements DEC-010.

Usage:
    python scripts/build_sample.py RAW OUT --jobs ID [ID ...] --cvs ID [ID ...]

RAW is the folder that holds `queries/`, `corpus/` and `qrels.tsv`, for example
`data/TaskA/development/en`. OUT is the sample folder, for example `data/sample`.
"""

import argparse
import shutil
from collections.abc import Sequence
from pathlib import Path

MIN_LABELED_CVS = 3
ATTRIBUTION = (
    "Data: TalentCLEF 2026 Task A, version 0.3.0 (English development set).\n"
    "DOI: 10.5281/zenodo.19652670\n"
    "License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)\n"
    "The files are copied unchanged, with a .txt extension added.\n"
)


def read_pairs(qrels: Path, jobs: Sequence[str], cvs: Sequence[str]) -> list[tuple[str, str]]:
    """Return the relevant (job, CV) pairs of `qrels` whose job and CV are both selected."""
    pairs: list[tuple[str, str]] = []
    for line in qrels.read_text(encoding="utf-8").splitlines():
        job, _, cv, relevance = line.split()
        if relevance == "1" and job in jobs and cv in cvs:
            pairs.append((job, cv))
    return pairs


def build_sample(raw: Path, out: Path, jobs: Sequence[str], cvs: Sequence[str]) -> None:
    """Write the sample files into `out`.

    Args:
        raw: Folder with `queries/`, `corpus/` and `qrels.tsv`. Only read.
        out: Folder to write `job_descriptions/`, `cvs/`, `ground_truth.tsv`, `ATTRIBUTION.txt`.
        jobs: IDs of the selected job descriptions.
        cvs: IDs of the selected CVs.

    Raises:
        ValueError: A selected job has fewer than three labeled CVs among the selected ones.
    """
    pairs = read_pairs(raw / "qrels.tsv", jobs, cvs)
    for job in jobs:
        count = sum(1 for pair_job, _ in pairs if pair_job == job)
        if count < MIN_LABELED_CVS:
            message = f"Job {job} has {count} labeled CVs; at least {MIN_LABELED_CVS} are needed."
            raise ValueError(message)
    for folder, source, ids in (("job_descriptions", "queries", jobs), ("cvs", "corpus", cvs)):
        (out / folder).mkdir(parents=True, exist_ok=True)
        for item in ids:
            shutil.copyfile(raw / source / item, out / folder / f"{item}.txt")
    ordered = [pair for job in jobs for pair in pairs if pair[0] == job]
    rows = ["job_id\tcv_id", *(f"{job}\t{cv}" for job, cv in ordered)]
    (out / "ground_truth.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (out / "ATTRIBUTION.txt").write_text(ATTRIBUTION, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the arguments and build the sample."""
    parser = argparse.ArgumentParser(description="Build the sample folder from raw TalentCLEF.")
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--jobs", nargs="+", required=True)
    parser.add_argument("--cvs", nargs="+", required=True)
    args = parser.parse_args(argv)
    build_sample(args.raw, args.out, args.jobs, args.cvs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
