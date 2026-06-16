from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_board_counts_use_dedicated_counter_not_status_dot():
    script = (ROOT / "app/static/app.js").read_text()
    styles = (ROOT / "app/static/styles.css").read_text()
    template = (ROOT / "app/templates/board.html").read_text()
    base_template = (ROOT / "app/templates/base.html").read_text()

    assert 'class="column-count"' in template
    assert 'data-column-points' in template
    assert 'id="main-content"' in base_template
    assert 'class="skip-links"' in base_template
    assert 'data-i18n="nav.skip_board"' in template
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


def test_sprint_dates_use_localized_option_labels():
    script = (ROOT / "app/static/app.js").read_text()
    template = (ROOT / "app/templates/project_sprints.html").read_text()
    board_template = (ROOT / "app/templates/board.html").read_text()
    styles = (ROOT / "app/static/styles.css").read_text()

    assert "function formatDateOnly" in script
    assert "function sprintDisplayLabel" in script
    assert "function compactSprintDateRangeLabel" in script
    assert "function sprintMenuMeta" in script
    assert "function setupSprintRangeLabels" in script
    assert "setupSprintOptionLabels();" in script
    assert "setupSprintRangeLabels();" in script
    assert 'class="sprint-row-details"' in template
    assert 'data-sprint-range' in template
    assert "data-local-date" not in template
    assert "data-sprint-filter-combo" in board_template
    assert "data-sprint-filter-search" in board_template
    assert "data-sprint-filter-create-toggle" in board_template
    assert "data-sprint-quick-create-form" in board_template
    assert "sprint.find_or_create_placeholder" in board_template
    assert "sprint.quick_create_placeholder" in board_template
    assert "sprint.goal_placeholder" in board_template
    assert '<form class="sprint-filter-form"' not in board_template
    assert "/sprints/quick" in script
    assert "new FormData(createForm)" in script
    assert 'data-i18n-tooltip="help.ticket_type"' in board_template
    assert 'data-i18n-tooltip="help.priority"' in board_template
    assert 'data-i18n-tooltip="help.ticket_type"' in script
    assert 'data-i18n-tooltip="help.priority"' in script
    assert 'translate("sprint.filter_modes"' in script
    assert 'translate("sprint.open_sprints"' in script
    assert '"sprint.active": "Active sprints"' in script
    assert '"sprint.active": "Активные спринты"' in script
    assert '"sprint.ticket_count_short": "t"' in script
    assert '"sprint.ticket_count_short": "т"' in script
    assert "popover-sprint-option" in script
    assert ".popover-sprint-option" in styles
    assert ".sprint-filter-option.is-filled" in styles


def test_popover_icons_render_after_menu_enters_dom():
    script = (ROOT / "app/static/app.js").read_text()
    open_popover = script.split("function openPopover", 1)[1].split("function closePopover", 1)[0]

    assert "document.body.appendChild(pop);" in open_popover
    assert "window.requestAnimationFrame(renderIcons);" in open_popover


def test_live_ticket_delete_removes_card_and_refreshes_counts():
    script = (ROOT / "app/static/app.js").read_text()
    live_events = script.split("function setupBoardLiveEvents", 1)[1].split("function applyLiveTicketPage", 1)[0]

    assert 'source.addEventListener("ticket_deleted", handleTicketEvent);' in live_events
    assert 'payload.event === "ticket_deleted"' in live_events
    assert "card.remove();" in live_events
    assert "refreshColumnCounts();" in live_events


def test_board_supports_keyboard_navigation_and_column_collapsing():
    script = (ROOT / "app/static/app.js").read_text()
    template = (ROOT / "app/templates/board.html").read_text()
    styles = (ROOT / "app/static/styles.css").read_text()

    assert 'data-column-toggle' in template
    assert 'aria-controls="column-zone-' in template
    assert 'class="column-collapsed-note"' in template
    assert "function setupColumnCollapsing()" in script
    assert "function onBoardKeyboardInteraction(event)" in script
    assert "function handleTicketKeyboardMove(event, handle)" in script
    assert "function applyStatusFilter(status)" in script
    assert 'translateTemplate("keyboard.ticket_moved"' in script
    assert 'translateTemplate("keyboard.ticket_sorted"' in script
    assert '"column.collapsed": "Collapsed"' in script
    assert '"column.collapsed": "Свернуто"' in script
    assert ".skip-links" in styles
    assert "pointer-events: none;" in styles
    assert ".column-toggle" in styles
    assert ".column-collapsed-note" in styles
    assert ".board-column.is-collapsed .dropzone" in styles
