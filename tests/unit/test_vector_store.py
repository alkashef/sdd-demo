import pytest

from src.vector_store import VectorStore, create_client


def make_store(name: str) -> VectorStore:
    return VectorStore(create_client(), name)


def test_rnk_001_nearest_returns_items_by_cosine_similarity():
    store = make_store("rnk-001-cosine")
    store.add("same.txt", [1.0, 0.0])
    store.add("diagonal.txt", [1.0, 1.0])
    store.add("opposite.txt", [-1.0, 0.0])

    nearest = store.nearest([2.0, 0.0])

    assert [item_id for item_id, _ in nearest] == ["same.txt", "diagonal.txt", "opposite.txt"]
    assert [score for _, score in nearest] == pytest.approx([1.0, 0.70710678, -1.0], abs=1e-4)


def test_job_002_all_cvs_returned_best_first_ties_by_file_name():
    store = make_store("job-002-cvs")
    store.add("c.txt", [0.0, 1.0])
    store.add("b.txt", [1.0, 0.0])
    store.add("a.txt", [1.0, 0.0])
    store.add("d.txt", [1.0, 1.0])

    nearest = store.nearest([1.0, 0.0])

    assert [item_id for item_id, _ in nearest] == ["a.txt", "b.txt", "d.txt", "c.txt"]


def test_cnd_003_all_jobs_returned_best_first():
    store = make_store("cnd-003-jobs")
    store.add("job-low.txt", [0.0, 1.0])
    store.add("job-high.txt", [1.0, 0.1])

    nearest = store.nearest([1.0, 0.0])

    assert [item_id for item_id, _ in nearest] == ["job-high.txt", "job-low.txt"]
    assert nearest[0][1] > nearest[1][1]


def test_rnk_001_empty_store_returns_no_items():
    assert make_store("rnk-001-empty").nearest([1.0, 0.0]) == []


def test_rnk_001_two_stores_on_one_client_stay_separate():
    client = create_client()
    cvs = VectorStore(client, "rnk-001-separate-cvs")
    jobs = VectorStore(client, "rnk-001-separate-jobs")
    cvs.add("cv.txt", [1.0, 0.0])
    jobs.add("job.txt", [1.0, 0.0])

    assert [item_id for item_id, _ in cvs.nearest([1.0, 0.0])] == ["cv.txt"]
    assert [item_id for item_id, _ in jobs.nearest([1.0, 0.0])] == ["job.txt"]


def test_dec_004_chroma_telemetry_off():
    assert create_client().get_settings().anonymized_telemetry is False
