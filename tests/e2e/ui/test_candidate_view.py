from playwright.sync_api import Page, expect

VIEW = ".candidate-view"


def _select_first_candidate(page: Page) -> None:
    page.locator("[data-list='candidates'] .nav-item").first.click()
    expect(page.locator(VIEW)).to_be_visible()


def test_cnd_001_ui_selecting_candidate_shows_raw_cv(page):
    _select_first_candidate(page)

    expect(page.locator(f"{VIEW} h1")).to_have_text("Candidate 00")
    expect(page.locator(f"{VIEW} .candidate-view__file")).to_have_text("cv00.txt")
    expect(page.locator(f"{VIEW} .candidate-view__meta")).to_have_text("Analyst")
    expect(page.locator(f"{VIEW} [data-cv-text]")).to_have_text("CV text cv00.txt")


def test_cnd_002_ui_shows_extracted_and_calculated_attributes(page):
    _select_first_candidate(page)

    facts = page.locator(f"{VIEW} .field").all_inner_texts()
    assert [text.split("\n")[0].lower() for text in facts] == [
        "current title",
        "location",
        "highest degree",
        "last job",
        "countries worked",
        "companies",
    ]
    assert "Cairo, Egypt" in facts[1]
    assert "Present" in facts[3]
    assert page.locator(f"{VIEW} .chip").all_inner_texts() == ["SQL"]
    stats = page.locator(f"{VIEW} .stat").all_inner_texts()
    assert [text.split("\n") for text in stats] == [
        ["Total employment", "100 mo"],
        ["Jobs held", "1"],
        ["Average per job", "50.5 mo"],
        ["Employment gaps", "3 mo"],
        ["Since graduation", "80 mo"],
        ["Employed now", "Yes"],
    ]


def test_cnd_003_ui_shows_ranked_jobs_best_first_without_recommendation(page):
    _select_first_candidate(page)

    rows = page.locator(f"{VIEW} .job-row")
    assert rows.count() == 2
    assert rows.nth(0).locator(".job-row__rank").inner_text() == "1"
    assert rows.nth(0).locator(".job-row__title").inner_text() == "Data Analyst"
    assert rows.nth(0).locator(".job-row__file").inner_text() == "j1.txt"
    assert rows.nth(0).locator(".job-row__score").inner_text() == "0.50"
    assert rows.nth(1).locator(".job-row__title").inner_text() == "Engineer"
    assert rows.nth(1).locator(".job-row__score").inner_text() == "0.40"
    assert page.locator(f"{VIEW} .pill").count() == 0
