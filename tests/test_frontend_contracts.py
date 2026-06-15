from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_board_counts_use_dedicated_counter_not_status_dot():
    script = (ROOT / "app/static/app.js").read_text()
    styles = (ROOT / "app/static/styles.css").read_text()
    template = (ROOT / "app/templates/board.html").read_text()

    assert 'class="column-count"' in template
    assert 'data-column-points' in template
    assert 'querySelector(".column-count")' in script
    assert 'querySelector("[data-column-points]")' in script
    assert 'querySelector(".column-head span")' not in script
    assert ".column-head span," not in styles


def test_mention_menu_selection_does_not_close_board_popover():
    script = (ROOT / "app/static/app.js").read_text()

    assert 'event.target.closest(".mention-menu")' in script
    assert "selectMention(input, user)" in script


def test_sprint_chip_stays_visible_before_assignee_chip():
    template = (ROOT / "app/templates/board.html").read_text()
    script = (ROOT / "app/static/app.js").read_text()
    card_script = script.split('card.innerHTML = `', 1)[1].split("`;", 1)[0]

    assert template.index('data-edit="sprint_id"') < template.index('data-edit="assignee_id"')
    assert card_script.index('data-edit="sprint_id"') < card_script.index('data-edit="assignee_id"')


def test_sprint_dates_use_localized_date_formatter():
    script = (ROOT / "app/static/app.js").read_text()
    template = (ROOT / "app/templates/project_sprints.html").read_text()

    assert "function formatDateOnly" in script
    assert "setupLocalDates();" in script
    assert "data-local-date" in template
