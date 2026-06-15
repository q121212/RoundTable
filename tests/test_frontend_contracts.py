from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_board_counts_use_dedicated_counter_not_status_dot():
    script = (ROOT / "app/static/app.js").read_text()
    styles = (ROOT / "app/static/styles.css").read_text()
    template = (ROOT / "app/templates/board.html").read_text()

    assert 'class="column-count"' in template
    assert 'querySelector(".column-count")' in script
    assert 'querySelector(".column-head span")' not in script
    assert ".column-head span," not in styles


def test_mention_menu_selection_does_not_close_board_popover():
    script = (ROOT / "app/static/app.js").read_text()

    assert 'event.target.closest(".mention-menu")' in script
    assert "selectMention(input, user)" in script
