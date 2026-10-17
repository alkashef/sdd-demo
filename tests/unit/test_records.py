from src.records import Document, Recommendation, YearMonth


def test_design_3_records_are_frozen_so_they_can_be_hashed() -> None:
    assert len({YearMonth(2026, 10), YearMonth(2026, 10)}) == 1
    assert hash(Document(doc_id="cv1.txt", text="text")) == hash(
        Document(doc_id="cv1.txt", text="text")
    )


def test_design_3_records_compare_by_value() -> None:
    assert Recommendation(interview=True, reason="fits") != Recommendation(
        interview=False, reason="fits"
    )
