from playwright.sync_api import Page, expect

CARD = ".candidate-card"


def _select_first_job(page: Page) -> None:
    page.locator("[data-list='jobs'] .nav-item").first.click()
    expect(page.locator(CARD).first).to_be_visible()


def test_job_002_ui_selecting_job_shows_ranked_candidates_best_first(page):
    _select_first_job(page)

    assert page.locator(CARD).count() == 40
    assert page.locator(f"{CARD} .candidate-card__rank").first.inner_text() == "1"
    assert page.locator(f"{CARD} .candidate-card__name").first.inner_text() == "Candidate 00"
    assert page.locator(f"{CARD} .candidate-card__score").first.inner_text() == "0.90"
    assert page.locator(f"{CARD} .candidate-card__score").nth(1).inner_text() == "0.89"
    assert page.locator(f"{CARD} .candidate-card__file").first.inner_text() == "cv00.txt"
    expect(page.locator(".job-view h1")).to_have_text("Data Analyst")
    expect(page.locator(".job-view__meta")).to_have_text("All 40 candidates, best match first.")


def test_job_003_ui_job_text_panel_sits_above_the_cards(page):
    _select_first_job(page)

    panel = page.locator(".job-view__text")
    assert panel.get_attribute("open") is not None
    expect(panel.locator("summary")).to_have_text("Job description text")
    expect(panel.locator(".doc")).to_contain_text("We need numbers.")
    panel_box = panel.bounding_box()
    card_box = page.locator(CARD).first.bounding_box()
    assert panel_box["y"] + panel_box["height"] <= card_box["y"]


def test_rnk_003_ui_card_shows_extracted_and_calculated_attributes(page):
    _select_first_job(page)

    card = page.locator(CARD).first
    facts = card.locator(".field").all_inner_texts()
    assert [text.split("\n")[0].lower() for text in facts] == [
        "current title",
        "location",
        "highest degree",
        "last job",
        "countries worked",
        "companies",
    ]
    assert "Analyst" in facts[0]
    assert "Cairo, Egypt" in facts[1]
    assert "Acme" in facts[3]
    assert "Present" in facts[3]
    assert card.locator(".chip").all_inner_texts() == ["SQL"]
    stats = card.locator(".stat").all_inner_texts()
    assert [text.split("\n") for text in stats] == [
        ["Total employment", "100 mo"],
        ["Jobs held", "1"],
        ["Average per job", "50.5 mo"],
        ["Employment gaps", "3 mo"],
        ["Since graduation", "80 mo"],
        ["Employed now", "Yes"],
    ]


def test_rec_001_ui_card_shows_recommendation_pill_and_reason(page):
    _select_first_job(page)

    first, second = page.locator(CARD).nth(0), page.locator(CARD).nth(1)
    expect(first.locator(".pill")).to_have_text("Interview")
    expect(first.locator(".candidate-card__reason")).to_have_text("Strong fit for the role.")
    expect(second.locator(".pill")).to_have_text("Skip")
    expect(second.locator(".candidate-card__reason")).to_have_text("No analytics experience.")


def test_dec_019_ui_card_folds_to_its_summary_line(page):
    _select_first_job(page)
    card = page.locator(CARD).first
    body = card.locator(".candidate-card__body")
    expect(body).to_be_visible()

    card.locator("summary").click()

    expect(body).to_be_hidden()
    expect(card.locator(".candidate-card__name")).to_be_visible()
    expect(card.locator(".candidate-card__score")).to_be_visible()
