from playwright.sync_api import Page, expect

PANEL = "[data-failures]"
CARD = ".candidate-card"


def _select_first_job(page: Page) -> None:
    page.locator("[data-list='jobs'] .nav-item").first.click()
    expect(page.locator(CARD).first).to_be_visible()


def test_err_001_ui_failure_panel_names_the_cause(failed_page):
    panel = failed_page.locator(PANEL)

    expect(panel).to_be_visible()
    expect(panel).to_contain_text("cv00.txt")
    expect(panel).to_contain_text("extraction failed, request timed out")
    expect(panel).to_contain_text("j1.txt + cv00.txt")
    expect(panel).to_contain_text("recommendation failed, request timed out")
    assert failed_page.locator(f"{PANEL} li").count() == 2


def test_err_001_ui_failure_panel_is_hidden_without_failures(page):
    expect(page.locator("[data-list='jobs'] .nav-item").first).to_be_visible()

    expect(page.locator(PANEL)).to_be_hidden()


def test_err_002_ui_keeps_lists_and_raw_texts_when_calls_failed(failed_page):
    expect(failed_page.locator("[data-list='jobs'] .nav-item").first).to_be_visible()
    assert failed_page.locator("[data-list='candidates'] .nav-item").count() == 2
    _select_first_job(failed_page)

    assert failed_page.locator(CARD).count() == 2
    assert failed_page.locator(f"{CARD} .candidate-card__score").first.inner_text() == "0.80"
    expect(failed_page.locator(".job-view__text .doc")).to_contain_text("We need numbers.")
    failed_page.locator("[data-list='candidates'] .nav-item").first.click()
    expect(failed_page.locator("[data-cv-text]")).to_have_text("Raw text zero")


def test_err_002_ui_failed_recommendation_shows_not_available_pill(failed_page):
    _select_first_job(failed_page)

    row = failed_page.locator(CARD).first.locator("[data-recommendation]")
    expect(row.locator(".pill")).to_have_text("Not available")
    assert "pill--unavailable" in row.locator(".pill").get_attribute("class")
    expect(row.locator(".candidate-card__reason")).to_have_text(
        "The recommendation could not be generated."
    )


def test_mis_001_ui_shows_not_available_for_missing_value(failed_page):
    _select_first_job(failed_page)

    card = failed_page.locator(CARD).first
    values = card.locator(".field__value").all_inner_texts()
    assert values == ["Not available"] * 6
    assert card.locator(".stat__value").all_inner_texts() == ["Not available"] * 6


def test_mis_002_ui_candidate_without_name_stays_listed_by_file_name(failed_page):
    expect(failed_page.locator("[data-list='candidates'] .nav-item").first).to_be_visible()

    labels = failed_page.locator("[data-list='candidates'] .nav-item__label").all_inner_texts()
    assert labels == ["cv00.txt", "cv01.txt"]
    _select_first_job(failed_page)
    names = failed_page.locator(f"{CARD} .candidate-card__name").all_inner_texts()
    assert names == ["cv00.txt", "cv01.txt"]


def test_dec_015_ui_unknown_end_shows_not_available_not_present(failed_page):
    _select_first_job(failed_page)

    last_job = failed_page.locator(CARD).nth(1).locator(".field").nth(3)
    assert "Jan 2018" in last_job.inner_text()
    assert last_job.inner_text().endswith("Not available")
    assert "Present" not in last_job.inner_text()


def test_dec_015_ui_current_job_shows_present(page):
    _select_first_job(page)

    last_job = page.locator(CARD).first.locator(".field").nth(3)
    assert "Jun 2019" in last_job.inner_text()
    assert last_job.inner_text().endswith("Present")
