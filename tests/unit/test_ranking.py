from src.ranking import append_unscored


def test_mis_002_item_without_vector_ranked_last_by_id():
    scored = [("b.txt", 0.9), ("a.txt", 0.5)]

    ranked = append_unscored(scored, ["a.txt", "b.txt", "z.txt", "c.txt"])

    assert ranked == [("b.txt", 0.9), ("a.txt", 0.5), ("c.txt", None), ("z.txt", None)]


def test_mis_002_every_item_scored_adds_nothing():
    scored = [("a.txt", 0.7)]

    assert append_unscored(scored, ["a.txt"]) == [("a.txt", 0.7)]


def test_mis_002_no_item_scored_ranks_all_by_id():
    assert append_unscored([], ["b.txt", "a.txt"]) == [("a.txt", None), ("b.txt", None)]
