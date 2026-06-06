(() => {
  let dragState = null;
  const STORAGE_LANG = "roundtable.lang";
  const STORAGE_THEME = "roundtable.theme";
  const STORAGE_BOARD_URL = "roundtable.lastBoardUrl";
  const messages = {
    en: {
      "action.close": "Close",
      "action.comment": "Comment",
      "action.create": "Create",
      "action.drag": "Move ticket",
      "action.mark_closed": "Mark ticket closed",
      "action.move": "Move",
      "action.reopen": "Reopen",
      "action.reopen_ticket": "Reopen ticket",
      "action.save": "Save",
      "action.update": "Update",
      "field.comment": "Comment",
      "field.assignee": "Assignee",
      "field.description": "Description",
      "field.email": "Email",
      "field.github_login": "GitHub login",
      "field.github_repo": "GitHub repo",
      "field.installation_id": "Installation id",
      "field.key": "Key",
      "field.name": "Name",
      "field.optional": "Optional",
      "field.priority": "Priority",
      "field.required": "Required",
      "field.reporter": "Reporter",
      "field.role": "Role",
      "field.status": "Status",
      "field.title": "Title",
      "github.create_project_first": "Create a project first.",
      "github.how_copy": "Paste a repository as owner/repo or a full GitHub URL. Add the installation id only when you want RoundTable to create autolinks through your GitHub App.",
      "github.how_title": "How to connect GitHub",
      "github.integration": "Integration",
      "github.links": "GitHub links",
      "github.repo_links": "Repository links",
      "github.settings": "GitHub settings",
      "github.use_key_prefix": "Use",
      "github.use_key_suffix": "in branches, commits, or PRs to link code.",
      "help.assignee": "Person responsible for the next action. They will receive notifications if enabled.",
      "help.comment": "Visible update for everyone watching the ticket.",
      "help.drag_ticket": "Drag the free area of a card to move it. Links and fields remain editable.",
      "help.github_repo": "Use owner/repo, https://github.com/owner/repo, or git@github.com:owner/repo.git.",
      "help.installation_id": "Numeric GitHub App installation id. Needed for automatic autolink setup; webhooks can still link tickets without it.",
      "help.mcp_token_name": "A label to remember where this token is used, for example Codex laptop.",
      "help.member_login": "Login of a user who already signed in once.",
      "help.priority": "Defaults to Medium. Use Urgent only for work that blocks people now.",
      "help.project_description": "Short context for teammates opening the project later.",
      "help.project_key": "Short uppercase prefix for ticket keys, for example CRM or OPS.",
      "help.project_name": "Human-readable project name shown in the UI.",
      "help.role": "member can edit, viewer can only read, admin can manage project access.",
      "help.status": "Where the ticket currently is on the board.",
      "help.ticket_description": "Add context, acceptance criteria, links, or notes. Markdown-style text is fine.",
      "help.ticket_title": "Short human-readable task name.",
      "language.switch": "Switch language",
      "login.copy": "Use GitHub OAuth in production. Local login is available only when enabled by configuration.",
      "login.eyebrow": "Local ticket tracker",
      "login.github": "Continue with GitHub",
      "login.github_missing": "GitHub OAuth is not configured yet.",
      "login.local": "Use local login",
      "login.title": "Sign in to RoundTable",
      "mcp.create": "Create token",
      "mcp.create_token": "Create MCP token",
      "mcp.created": "New token created. Copy it now:",
      "mcp.endpoint": "Endpoint:",
      "mcp.empty": "No tokens yet.",
      "mcp.eyebrow": "Automation",
      "mcp.how_copy": "Create a token here, copy it once, then use it in your MCP client as an Authorization: Bearer token.",
      "mcp.how_title": "How MCP tokens work",
      "mcp.revoke": "Revoke",
      "mcp.title": "MCP access",
      "mcp.tokens": "Tokens",
      "nav.logout": "Log out",
      "nav.board": "Board",
      "nav.menu": "Menu",
      "nav.notifications": "Notifications",
      "nav.projects": "Projects",
      "nav.settings": "Settings",
      "notifications.channels": "Channels",
      "notifications.eyebrow": "Personal settings",
      "notifications.how_copy": "RoundTable notifies assignees, reporters, and watchers on assignment, status changes, comments, and close/reopen actions.",
      "notifications.how_title": "When notifications are sent",
      "notifications.save": "Save preferences",
      "notifications.telegram_copy": "Generate a token, open your configured Telegram bot, and send /start plus that token. The bot webhook must point to /integrations/telegram/webhook.",
      "notifications.telegram_generate": "Generate link token",
      "notifications.telegram_help": "Generate a one-time token, then send it to the configured Telegram bot.",
      "notifications.telegram_send": "Send this to your Telegram bot:",
      "notifications.telegram_title": "How to link a phone",
      "notifications.telegram_unlink": "Unlink Telegram",
      "notifications.test": "Send test",
      "notifications.title": "Notifications",
      "placeholder.comment": "Add an update",
      "placeholder.existing_login": "Existing user login",
      "placeholder.github_repo": "owner/repo or https://github.com/owner/repo",
      "placeholder.installation_id": "installation id",
      "placeholder.project_description": "What this project is for",
      "placeholder.quick_comment": "Optional comment",
      "placeholder.ticket_title": "New ticket title",
      "priority.High": "High",
      "priority.Low": "Low",
      "priority.Medium": "Medium",
      "priority.Urgent": "Urgent",
      "projects.access": "Project access",
      "projects.add_member": "Add member",
      "projects.back_to_board": "Back to board",
      "projects.create": "Create project",
      "projects.empty_copy": "Create the first project and RoundTable will start ticket keys from KEY-1.",
      "projects.empty_title": "No projects yet",
      "projects.eyebrow": "Workspace",
      "projects.members": "Members",
      "projects.no_members": "No members yet.",
      "projects.settings": "Project settings",
      "projects.title": "Projects",
      "status.all": "All",
      "status.Backlog": "Backlog",
      "status.Closed": "Closed",
      "status.Done": "Done",
      "status.In Progress": "In Progress",
      "status.Review": "Review",
      "status.Todo": "Todo",
      "theme.dark": "Dark",
      "theme.light": "Light",
      "ticket.activity": "Activity",
      "ticket.comments": "Comments",
      "ticket.details": "Details",
      "ticket.new": "New ticket",
      "ticket.quick_edit": "Quick edit",
      "ticket.quick_create": "Quick create",
      "ticket.quick_create_help": "Create a ticket fast; details can be edited after opening it.",
      "ticket.save": "Save ticket",
      "ticket.unassigned": "Unassigned",
      "ticket.watchers": "Watchers",
      "ticket.watch": "Watch ticket",
      "ticket.workflow_help": "These actions change ticket state; they do not close this page.",
    },
    ru: {
      "action.close": "Закрыть",
      "action.comment": "Комментировать",
      "action.create": "Создать",
      "action.drag": "Переместить тикет",
      "action.mark_closed": "Закрыть тикет",
      "action.move": "Переместить",
      "action.reopen": "Открыть снова",
      "action.reopen_ticket": "Открыть тикет снова",
      "action.save": "Сохранить",
      "action.update": "Обновить",
      "field.comment": "Комментарий",
      "field.assignee": "Исполнитель",
      "field.description": "Описание",
      "field.email": "Email",
      "field.github_login": "GitHub логин",
      "field.github_repo": "GitHub репозиторий",
      "field.installation_id": "Installation id",
      "field.key": "Ключ",
      "field.name": "Название",
      "field.optional": "Необязательно",
      "field.priority": "Приоритет",
      "field.required": "Обязательно",
      "field.reporter": "Автор",
      "field.role": "Роль",
      "field.status": "Статус",
      "field.title": "Заголовок",
      "github.create_project_first": "Сначала создайте проект.",
      "github.how_copy": "Вставьте репозиторий как owner/repo или полную ссылку GitHub. Installation id нужен только если RoundTable должен создавать autolinks через GitHub App.",
      "github.how_title": "Как подключить GitHub",
      "github.integration": "Интеграция",
      "github.links": "Связи GitHub",
      "github.repo_links": "Репозитории",
      "github.settings": "Настройки GitHub",
      "github.use_key_prefix": "Используйте",
      "github.use_key_suffix": "в ветках, коммитах или PR, чтобы связать код.",
      "help.assignee": "Человек, который отвечает за следующий шаг. Если уведомления включены, он получит сообщение.",
      "help.comment": "Обновление, которое увидят все наблюдатели тикета.",
      "help.drag_ticket": "Тяните за свободную область карточки, чтобы переместить ее. Ссылки и поля остаются редактируемыми.",
      "help.github_repo": "Можно owner/repo, https://github.com/owner/repo или git@github.com:owner/repo.git.",
      "help.installation_id": "Числовой id установки GitHub App. Нужен для автоматического создания autolink; webhook-связи работают и без него.",
      "help.mcp_token_name": "Метка, чтобы помнить, где используется токен, например Codex laptop.",
      "help.member_login": "Логин пользователя, который уже хотя бы раз вошел в RoundTable.",
      "help.priority": "По умолчанию Medium. Urgent используйте только для работы, которая прямо сейчас кого-то блокирует.",
      "help.project_description": "Короткий контекст для людей, которые позже откроют проект.",
      "help.project_key": "Короткий uppercase-префикс для ключей тикетов, например CRM или OPS.",
      "help.project_name": "Человеческое название проекта, которое видно в интерфейсе.",
      "help.role": "member может редактировать, viewer только читать, admin управляет доступом к проекту.",
      "help.status": "Где тикет сейчас находится на доске.",
      "help.ticket_description": "Добавьте контекст, критерии приемки, ссылки или заметки. Можно писать markdown-подобный текст.",
      "help.ticket_title": "Короткое человеческое название задачи.",
      "language.switch": "Сменить язык",
      "login.copy": "В продакшене используйте GitHub OAuth. Локальный вход доступен только если включен в конфигурации.",
      "login.eyebrow": "Локальный трекер задач",
      "login.github": "Войти через GitHub",
      "login.github_missing": "GitHub OAuth пока не настроен.",
      "login.local": "Войти локально",
      "login.title": "Вход в RoundTable",
      "mcp.create": "Создать токен",
      "mcp.create_token": "Создать MCP токен",
      "mcp.created": "Новый токен создан. Скопируйте его сейчас:",
      "mcp.endpoint": "Endpoint:",
      "mcp.empty": "Токенов пока нет.",
      "mcp.eyebrow": "Автоматизация",
      "mcp.how_copy": "Создайте токен здесь, скопируйте его один раз, затем используйте в MCP-клиенте как Authorization: Bearer токен.",
      "mcp.how_title": "Как работают MCP токены",
      "mcp.revoke": "Отозвать",
      "mcp.title": "Доступ MCP",
      "mcp.tokens": "Токены",
      "nav.logout": "Выйти",
      "nav.board": "Доска",
      "nav.menu": "Меню",
      "nav.notifications": "Уведомления",
      "nav.projects": "Проекты",
      "nav.settings": "Настройки",
      "notifications.channels": "Каналы",
      "notifications.eyebrow": "Личные настройки",
      "notifications.how_copy": "RoundTable уведомляет исполнителей, авторов и наблюдателей при назначении, смене статуса, комментариях, закрытии и переоткрытии.",
      "notifications.how_title": "Когда приходят уведомления",
      "notifications.save": "Сохранить настройки",
      "notifications.telegram_copy": "Создайте токен, откройте настроенного Telegram-бота и отправьте /start плюс этот токен. Webhook бота должен указывать на /integrations/telegram/webhook.",
      "notifications.telegram_generate": "Создать токен привязки",
      "notifications.telegram_help": "Создайте одноразовый токен и отправьте его настроенному Telegram-боту.",
      "notifications.telegram_send": "Отправьте это вашему Telegram-боту:",
      "notifications.telegram_title": "Как привязать телефон",
      "notifications.telegram_unlink": "Отвязать Telegram",
      "notifications.test": "Отправить тест",
      "notifications.title": "Уведомления",
      "placeholder.comment": "Добавить обновление",
      "placeholder.existing_login": "Логин существующего пользователя",
      "placeholder.github_repo": "owner/repo или https://github.com/owner/repo",
      "placeholder.installation_id": "installation id",
      "placeholder.project_description": "Для чего этот проект",
      "placeholder.quick_comment": "Комментарий, если нужен",
      "placeholder.ticket_title": "Название нового тикета",
      "priority.High": "Высокий",
      "priority.Low": "Низкий",
      "priority.Medium": "Средний",
      "priority.Urgent": "Срочный",
      "projects.access": "Доступ к проекту",
      "projects.add_member": "Добавить участника",
      "projects.back_to_board": "Назад к доске",
      "projects.create": "Создать проект",
      "projects.empty_copy": "Создайте первый проект, и RoundTable начнет тикеты с KEY-1.",
      "projects.empty_title": "Проектов пока нет",
      "projects.eyebrow": "Рабочее пространство",
      "projects.members": "Участники",
      "projects.no_members": "Участников пока нет.",
      "projects.settings": "Настройки проекта",
      "projects.title": "Проекты",
      "status.all": "Все",
      "status.Backlog": "Бэклог",
      "status.Closed": "Закрыто",
      "status.Done": "Готово",
      "status.In Progress": "В работе",
      "status.Review": "Ревью",
      "status.Todo": "К выполнению",
      "theme.dark": "Темная",
      "theme.light": "Светлая",
      "ticket.activity": "История",
      "ticket.comments": "Комментарии",
      "ticket.details": "Детали",
      "ticket.new": "Новый тикет",
      "ticket.quick_edit": "Быстро изменить",
      "ticket.quick_create": "Быстрое создание",
      "ticket.quick_create_help": "Создайте тикет быстро; детали можно дописать после открытия.",
      "ticket.save": "Сохранить тикет",
      "ticket.unassigned": "Без исполнителя",
      "ticket.watchers": "Наблюдатели",
      "ticket.watch": "Следить за тикетом",
      "ticket.workflow_help": "Эти действия меняют состояние тикета, а не закрывают страницу.",
    },
  };

  function currentLang() {
    return localStorage.getItem(STORAGE_LANG) || "en";
  }

  function currentTheme() {
    return localStorage.getItem(STORAGE_THEME) || "light";
  }

  function translate(key, lang) {
    return (messages[lang] && messages[lang][key]) || messages.en[key] || "";
  }

  function applyLanguage(lang) {
    localStorage.setItem(STORAGE_LANG, lang);
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((element) => {
      const value = translate(element.dataset.i18n, lang);
      if (value) element.textContent = value;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
      const value = translate(element.dataset.i18nPlaceholder, lang);
      if (value) element.setAttribute("placeholder", value);
    });
    document.querySelectorAll("[data-i18n-tooltip]").forEach((element) => {
      const value = translate(element.dataset.i18nTooltip, lang);
      if (value) element.setAttribute("data-tooltip", value);
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
      const value = translate(element.dataset.i18nAria, lang);
      if (value) element.setAttribute("aria-label", value);
    });
    updateLanguageButton();
    updateThemeButton();
    renderIcons();
  }

  function applyTheme(theme) {
    localStorage.setItem(STORAGE_THEME, theme);
    document.documentElement.dataset.theme = theme;
    updateThemeButton();
    renderIcons();
  }

  function updateThemeButton() {
    const button = document.querySelector("[data-theme-toggle]");
    if (!button) return;
    const nextKey = currentTheme() === "dark" ? "theme.light" : "theme.dark";
    button.dataset.icon = currentTheme() === "dark" ? "sun" : "moon";
    button.dataset.i18n = nextKey;
    button.textContent = translate(nextKey, currentLang());
  }

  function updateLanguageButton() {
    const button = document.querySelector("[data-lang-toggle]");
    if (!button) return;
    button.textContent = currentLang().toUpperCase();
    button.setAttribute("aria-label", translate("language.switch", currentLang()));
  }

  function renderIcons() {
    if (!window.lucide) return;
    document.querySelectorAll("[data-icon], .help-dot").forEach((element) => {
      element.querySelectorAll("svg.icon").forEach((icon) => icon.remove());
      const iconName = element.dataset.icon || "info";
      const placeholder = document.createElement("i");
      placeholder.setAttribute("data-lucide", iconName);
      placeholder.className = "icon";
      element.prepend(placeholder);
      element.classList.add("has-icon");
      if (element.classList.contains("help-dot") && !element.getAttribute("aria-label")) {
        element.setAttribute("aria-label", "Help");
      }
    });
    window.lucide.createIcons({
      attrs: {
        class: "icon",
        "aria-hidden": "true",
      },
    });
  }

  function setupPreferences() {
    applyTheme(currentTheme());
    applyLanguage(currentLang());
    const langButton = document.querySelector("[data-lang-toggle]");
    if (langButton) {
      langButton.addEventListener("click", () => applyLanguage(currentLang() === "ru" ? "en" : "ru"));
    }
    const themeButton = document.querySelector("[data-theme-toggle]");
    if (themeButton) {
      themeButton.addEventListener("click", () => {
        applyTheme(currentTheme() === "dark" ? "light" : "dark");
      });
    }
  }

  function setupLastBoardLinks() {
    const currentProjectUrl = document.body.dataset.currentProjectUrl;
    if (currentProjectUrl) {
      localStorage.setItem(STORAGE_BOARD_URL, currentProjectUrl);
    }
    const boardUrl = localStorage.getItem(STORAGE_BOARD_URL) || "/projects";
    document.querySelectorAll("[data-board-link], [data-home-link]").forEach((link) => {
      link.setAttribute("href", boardUrl);
    });
  }

  function setupBoardDnD() {
    document.querySelectorAll(".ticket-card").forEach((card) => {
      card.addEventListener("pointerdown", startTicketDrag);
    });
  }

  function startTicketDrag(event) {
    if (event.button !== undefined && event.button !== 0) return;
    if (
      event.target.closest(
        "a, button, input, select, textarea, label, summary, details, .ticket-key, .priority-chip, .assignee-chip, .ticket-title"
      )
    ) {
      return;
    }
    const card = event.currentTarget.closest(".ticket-card");
    if (!card) return;
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    dragState = {
      card,
      handle: event.currentTarget,
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      started: false,
    };
  }

  function activateTicketDrag(event) {
    if (!dragState || dragState.started) return;
    const card = dragState.card;
    const rect = card.getBoundingClientRect();
    const placeholder = document.createElement("div");
    placeholder.className = "ticket-placeholder";
    placeholder.style.height = `${rect.height}px`;
    const preview = card.cloneNode(true);
    preview.classList.add("ticket-drag-preview");
    preview.style.width = `${rect.width}px`;
    preview.querySelectorAll("a, button, input, select, textarea").forEach((element) => {
      element.setAttribute("tabindex", "-1");
      if ("disabled" in element) element.disabled = true;
    });
    const hiddenColumns = Array.from(document.querySelectorAll(".board-column.mobile-hidden"));
    hiddenColumns.forEach((column) => {
      column.classList.add("drag-temp-visible");
      column.classList.remove("mobile-hidden");
    });
    card.after(placeholder);
    card.classList.add("drag-source");
    document.body.appendChild(preview);
    Object.assign(dragState, {
      hiddenColumns,
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top,
      placeholder,
      preview,
      currentZone: null,
      started: true,
    });
    document.body.classList.add("is-dragging-ticket");
    moveDragPreview(event.clientX, event.clientY);
  }

  function moveDragPreview(clientX, clientY) {
    if (!dragState) return;
    dragState.preview.style.left = `${clientX - dragState.offsetX}px`;
    dragState.preview.style.top = `${clientY - dragState.offsetY}px`;
  }

  function updateDragTarget(clientX, clientY) {
    if (!dragState) return;
    const target = document.elementFromPoint(clientX, clientY);
    const zone = target ? target.closest(".dropzone") : null;
    document.querySelectorAll(".dropzone.drag-over").forEach((item) => {
      if (item !== zone) item.classList.remove("drag-over");
    });
    if (zone) zone.classList.add("drag-over");
    dragState.currentZone = zone;
  }

  async function finishTicketDrag(event) {
    if (!dragState) return;
    const state = dragState;
    dragState = null;
    if (!state.started) {
      if (state.handle.hasPointerCapture && state.handle.hasPointerCapture(state.pointerId)) {
        state.handle.releasePointerCapture(state.pointerId);
      }
      return;
    }
    document.body.classList.remove("is-dragging-ticket");
    document.querySelectorAll(".dropzone.drag-over").forEach((zone) => zone.classList.remove("drag-over"));
    state.hiddenColumns.forEach((column) => {
      column.classList.remove("drag-temp-visible");
      column.classList.add("mobile-hidden");
    });
    if (state.handle.hasPointerCapture && state.handle.hasPointerCapture(state.pointerId)) {
      state.handle.releasePointerCapture(state.pointerId);
    }
    state.preview.remove();
    const zone = state.currentZone || document.elementFromPoint(event.clientX, event.clientY)?.closest(".dropzone");
    const status = zone ? zone.dataset.status : "";
    const previousZone = state.placeholder.closest(".dropzone");
    const previousStatus = previousZone ? previousZone.dataset.status : "";
    if (!zone || !status || status === previousStatus) {
      state.card.classList.remove("drag-source");
      state.placeholder.replaceWith(state.card);
      return;
    }
    zone.appendChild(state.card);
    state.placeholder.remove();
    state.card.classList.remove("drag-source");
    refreshColumnCounts();
    try {
      const ticket = await patchTicket(state.card.dataset.ticketKey, { status });
      applyTicketUpdate(state.card, ticket);
    } catch (error) {
      if (previousZone) previousZone.appendChild(state.card);
      refreshColumnCounts();
      window.alert(error.message || "Could not move ticket");
    }
  }

  function cancelTicketDrag() {
    if (!dragState) return;
    const state = dragState;
    dragState = null;
    if (!state.started) {
      if (state.handle.hasPointerCapture && state.handle.hasPointerCapture(state.pointerId)) {
        state.handle.releasePointerCapture(state.pointerId);
      }
      return;
    }
    document.body.classList.remove("is-dragging-ticket");
    document.querySelectorAll(".dropzone.drag-over").forEach((zone) => zone.classList.remove("drag-over"));
    state.hiddenColumns.forEach((column) => {
      column.classList.remove("drag-temp-visible");
      column.classList.add("mobile-hidden");
    });
    state.preview.remove();
    state.card.classList.remove("drag-source");
    state.placeholder.replaceWith(state.card);
  }

  async function patchTicket(ticketKey, payload) {
    const board = document.querySelector(".board");
    const csrf = board ? board.dataset.csrf : "";
    const response = await fetch(`/api/tickets/${ticketKey}`, {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
        "x-csrf-token": csrf,
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  function setupInlineTicketControls() {
    document.querySelectorAll("[data-inline-field]").forEach((control) => {
      control.dataset.lastValue = control.value;
      control.addEventListener("change", async () => {
        const card = control.closest(".ticket-card");
        const field = control.dataset.inlineField;
        const previousValue = control.dataset.lastValue || "";
        const payload = {};
        payload[field] = field === "assignee_id" ? (control.value ? Number(control.value) : null) : control.value;
        control.disabled = true;
        card.classList.add("is-saving");
        try {
          const ticket = await patchTicket(control.dataset.ticketKey, payload);
          control.dataset.lastValue = control.value;
          applyTicketUpdate(card, ticket);
          flashSaved(card);
        } catch (error) {
          control.value = previousValue;
          window.alert(error.message || "Could not update ticket");
        } finally {
          control.disabled = false;
          card.classList.remove("is-saving");
        }
      });
    });

    document.querySelectorAll("[data-inline-comment]").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const input = form.querySelector("[name=body]");
        const body = input.value.trim();
        if (!body) return;
        const card = form.closest(".ticket-card");
        const button = form.querySelector("button");
        const formData = new FormData(form);
        input.disabled = true;
        button.disabled = true;
        card.classList.add("is-saving");
        try {
          const response = await fetch(form.action, {
            method: "POST",
            headers: { "x-csrf-token": form.querySelector("[name=csrf_token]").value },
            body: formData,
          });
          if (!response.ok) throw new Error(await response.text());
          input.value = "";
          flashSaved(card);
        } catch (error) {
          window.alert(error.message || "Could not add comment");
        } finally {
          input.disabled = false;
          button.disabled = false;
          card.classList.remove("is-saving");
        }
      });
    });
  }

  function applyTicketUpdate(card, ticket) {
    if (!card || !ticket) return;
    card.dataset.ticketKey = ticket.key;
    updateCardClasses(card, ticket);
    moveCardToStatus(card, ticket.status);
    updateSelect(card, "status", ticket.status);
    updateSelect(card, "priority", ticket.priority);
    updateSelect(card, "assignee_id", ticket.assignee_id ? String(ticket.assignee_id) : "");
    updateAssignee(card, ticket);
    updatePriorityChip(card, ticket);
    refreshColumnCounts();
  }

  function updatePriorityChip(card, ticket) {
    const top = card.querySelector(".ticket-card-top");
    if (!top) return;
    let chip = top.querySelector(".priority-chip");
    const elevated = ticket.priority === "Urgent" || ticket.priority === "High";
    if (!elevated) {
      if (chip) chip.remove();
      return;
    }
    if (!chip) {
      chip = document.createElement("span");
      top.appendChild(chip);
    }
    chip.className = `priority-chip priority-chip-${ticket.priority.toLowerCase()}`;
    chip.dataset.i18n = `priority.${ticket.priority}`;
    chip.textContent = translate(`priority.${ticket.priority}`, currentLang()) || ticket.priority;
  }

  function updateCardClasses(card, ticket) {
    card.className = card.className
      .split(/\s+/)
      .filter((name) => name && !name.startsWith("priority-") && !name.startsWith("status-"))
      .join(" ");
    card.classList.add("ticket-card", `priority-${ticket.priority.toLowerCase()}`, `status-${ticket.status.toLowerCase().replace(/\s+/g, "-")}`);
  }

  function moveCardToStatus(card, status) {
    const zone = document.querySelector(`.dropzone[data-status="${cssEscape(status)}"]`);
    if (zone && !zone.contains(card)) zone.appendChild(card);
  }

  function updateSelect(card, field, value) {
    const select = card.querySelector(`[data-inline-field="${field}"]`);
    if (!select) return;
    select.value = value || "";
    select.dataset.lastValue = select.value;
  }

  function updateAssignee(card, ticket) {
    const chip = card.querySelector(".assignee-chip");
    if (!chip) return;
    const avatar = chip.querySelector(".avatar-dot");
    const label = chip.querySelector(".assignee-label");
    renderAvatar(avatar, ticket.assignee_avatar_url, ticket.assignee_login);
    if (label) {
      if (ticket.assignee_login) {
        label.removeAttribute("data-i18n");
        label.textContent = ticket.assignee_name || ticket.assignee_login;
      } else {
        label.dataset.i18n = "ticket.unassigned";
        label.textContent = translate("ticket.unassigned", currentLang()) || "Unassigned";
      }
    }
  }

  function renderAvatar(container, avatarUrl, login) {
    if (!container) return;
    container.textContent = "";
    if (avatarUrl) {
      const image = document.createElement("img");
      image.src = avatarUrl;
      image.alt = "";
      image.loading = "lazy";
      image.referrerPolicy = "no-referrer";
      container.appendChild(image);
    } else {
      container.textContent = (login || "?").slice(0, 1).toUpperCase();
    }
  }

  function refreshColumnCounts() {
    document.querySelectorAll(".board-column").forEach((column) => {
      const counter = column.querySelector(".column-head span");
      if (counter) counter.textContent = column.querySelectorAll(".ticket-card").length;
    });
  }

  function flashSaved(card) {
    card.classList.add("is-saved");
    window.setTimeout(() => card.classList.remove("is-saved"), 900);
  }

  function cssEscape(value) {
    if (window.CSS && window.CSS.escape) return window.CSS.escape(value);
    return String(value).replace(/"/g, '\\"');
  }

  function setupOpenCreate() {
    document.querySelectorAll("[data-open-create]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        const panel = document.querySelector(".board-create");
        if (panel) panel.open = true;
        const title = document.querySelector("[name=title]");
        if (title) title.focus();
      });
    });
  }

  function setupMobileStatusTabs() {
    const tabs = document.querySelectorAll("[data-status-filter]");
    if (!tabs.length) return;
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const status = tab.dataset.statusFilter;
        tabs.forEach((item) => item.classList.toggle("active", item === tab));
        document.querySelectorAll(".board-column").forEach((column) => {
          const show = status === "all" || column.dataset.status === status;
          column.classList.toggle("mobile-hidden", !show);
        });
      });
    });
  }

  function setupTooltips() {
    document.addEventListener("click", (event) => {
      document.querySelectorAll(".help-dot.tooltip-open").forEach((button) => {
        if (button !== event.target) button.classList.remove("tooltip-open");
      });
      const helpButton = event.target.closest(".help-dot");
      if (helpButton) {
        event.preventDefault();
        helpButton.classList.toggle("tooltip-open");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupLastBoardLinks();
    setupPreferences();
    setupBoardDnD();
    setupInlineTicketControls();
    setupOpenCreate();
    setupMobileStatusTabs();
    setupTooltips();
  });

  window.addEventListener("pointermove", (event) => {
    if (!dragState) return;
    event.preventDefault();
    if (!dragState.started) {
      const distance = Math.hypot(event.clientX - dragState.startX, event.clientY - dragState.startY);
      if (distance < 6) return;
      activateTicketDrag(event);
    }
    moveDragPreview(event.clientX, event.clientY);
    updateDragTarget(event.clientX, event.clientY);
  });

  window.addEventListener("pointerup", (event) => {
    if (!dragState) return;
    event.preventDefault();
    finishTicketDrag(event);
  });

  window.addEventListener("pointercancel", cancelTicketDrag);
})();
