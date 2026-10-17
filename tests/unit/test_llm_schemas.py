import pytest
from pydantic import ValidationError

from src.llm_schemas import CvFactsReply, JobReply


def _job(**overrides):
    fields = {
        "title": "Engineer",
        "employer": "Acme",
        "city": "Berlin",
        "country": "Germany",
        "start": "2020-01",
        "end": "2021-12",
        "is_current": False,
        "description": "Built things.",
    }
    return {**fields, **overrides}


def _facts(**overrides):
    fields = {
        "name": "Jane Roe",
        "current_title": "Engineer",
        "skills": ["Python"],
        "city": "Berlin",
        "country": "Germany",
        "highest_degree": "BSc",
        "jobs": [_job()],
        "education": [],
    }
    return {**fields, **overrides}


def test_ext_009_valid_reply_is_accepted():
    reply = CvFactsReply.model_validate(_facts())

    assert reply.jobs[0].start == "2020-01"
    assert reply.jobs[0].is_current is False


@pytest.mark.parametrize("bad", ["2020", "2020-13", "2020-00", "Jan 2020", "2020-1"])
def test_ext_009_date_not_in_year_month_form_is_rejected(bad):
    with pytest.raises(ValidationError):
        JobReply.model_validate(_job(start=bad))


def test_mis_001_null_date_is_accepted():
    reply = JobReply.model_validate(_job(start=None, end=None))

    assert reply.start is None
    assert reply.end is None


def test_ext_004_field_missing_from_reply_is_rejected():
    fields = _facts()
    del fields["skills"]

    with pytest.raises(ValidationError):
        CvFactsReply.model_validate(fields)


def test_ext_004_extra_field_in_reply_is_rejected():
    with pytest.raises(ValidationError):
        CvFactsReply.model_validate(_facts(salary="1"))
