from playwright.sync_api import Page, expect

MUTED_COLOR = "rgb(90, 96, 128)"


def _labels(page: Page, list_name: str) -> list[str]:
    return page.locator(f"[data-list='{list_name}'] .nav-item__label").all_inner_texts()


def test_lst_001_ui_lists_job_descriptions(page):
    expect(page.locator("[data-list='jobs'] .nav-item__label").first).to_be_visible()

    assert _labels(page, "jobs") == ["Data Analyst", "Engineer"]
    assert page.locator("[data-list='jobs'] .nav-item__file").all_inner_texts() == [
        "j1.txt",
        "j2.txt",
    ]


def test_lst_002_ui_lists_candidates(page):
    expect(page.locator("[data-list='candidates'] .nav-item__label").first).to_be_visible()

    names = _labels(page, "candidates")
    assert len(names) == 40
    assert names[:2] == ["Candidate 00", "Candidate 01"]
    assert page.locator("[data-list='candidates'] .nav-item__file").first.inner_text() == "cv00.txt"


def test_lst_001_ui_header_counts_both_lists(page):
    expect(page.locator(".app-header__counts")).to_have_text("40 candidates · 2 job descriptions")


def test_dec_019_ui_header_stays_at_top_when_page_scrolls(page):
    expect(page.locator("[data-list='candidates'] .nav-item").first).to_be_visible()

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    assert page.evaluate("window.scrollY") > 0
    assert page.locator(".app-header").bounding_box()["y"] == 0


def test_dec_019_ui_file_name_sits_below_name_in_smaller_size(page):
    label = page.locator("[data-list='jobs'] .nav-item__label").first
    file_name = page.locator("[data-list='jobs'] .nav-item__file").first
    expect(label).to_be_visible()

    label_box, file_box = label.bounding_box(), file_name.bounding_box()
    assert file_box["y"] >= label_box["y"] + label_box["height"]
    assert file_box["x"] == label_box["x"]
    assert file_name.evaluate("e => getComputedStyle(e).fontSize") == "12px"
    assert label.evaluate("e => getComputedStyle(e).fontSize") == "14px"
    assert file_name.evaluate("e => getComputedStyle(e).color") == MUTED_COLOR


def test_lst_001_ui_selecting_an_item_marks_it_selected(page):
    item = page.locator("[data-list='jobs'] .nav-item").nth(1)
    expect(item).to_be_visible()

    item.click()

    expect(item).to_have_class("nav-item nav-item--selected")
    assert page.locator(".nav-item--selected").count() == 1
