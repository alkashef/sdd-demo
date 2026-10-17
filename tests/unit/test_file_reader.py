from pathlib import Path

import pytest

from src.file_reader import read_documents, read_text
from src.records import Document


def test_ext_001_reads_each_cv_file_in_folder(tmp_path: Path):
    (tmp_path / "b.txt").write_text("Second CV", encoding="utf-8")
    (tmp_path / "a.txt").write_text("First CV", encoding="utf-8")
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / "sub.txt").mkdir()

    documents = read_documents(tmp_path)

    assert documents == [Document("a.txt", "First CV"), Document("b.txt", "Second CV")]


def test_job_001_reads_each_job_description_file_in_folder(tmp_path: Path):
    (tmp_path / "job-2.txt").write_text("Welder wanted", encoding="utf-8")
    (tmp_path / "job-1.txt").write_text("Baker wanted — café", encoding="utf-8")

    documents = read_documents(tmp_path)

    assert documents == [
        Document("job-1.txt", "Baker wanted — café"),
        Document("job-2.txt", "Welder wanted"),
    ]


def test_ext_001_missing_folder_stops_with_clear_message(tmp_path: Path):
    missing = tmp_path / "no-such-folder"

    with pytest.raises(FileNotFoundError, match="no-such-folder"):
        read_documents(missing)


def test_dec_017_reads_prompt_and_evaluation_files_as_text(tmp_path: Path):
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Extract the facts.\nSecond line.", encoding="utf-8")

    assert read_text(prompt) == "Extract the facts.\nSecond line."


def test_dec_017_missing_file_stops_with_clear_message(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match=r"absent\.tsv"):
        read_text(tmp_path / "absent.tsv")
