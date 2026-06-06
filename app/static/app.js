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
      "action.unwatch": "Unwatch",
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
      "footer.tagline": "A round table for your tickets.",
      "github.create_project_first": "Create a project first.",
      "github.how_copy": "Paste owner/repo or a GitHub URL. That is enough for webhook-based linking from branches, commits, and PRs.",
      "github.how_title": "How to connect GitHub",
      "github.installation_note": "Installation id is optional and only needed for advanced GitHub App actions such as creating repository autolinks automatically. You can leave it empty.",
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
      "help.member_login": "GitHub login. The user can be added before their first sign-in.",
      "help.priority": "Defaults to Medium. Use Urgent only for work that blocks people now.",
      "help.project_description": "Short context for teammates opening the project later.",
      "help.project_key": "Short uppercase prefix for ticket keys, for example CRM or OPS.",
      "help.project_name": "Human-readable project name shown in the UI.",
      "help.role": "member can edit, viewer can only read, admin can manage project access.",
      "help.status": "Where the ticket currently is on the board.",
      "help.ticket_description": "Add context, acceptance criteria, links, or notes. Markdown-style text is fine.",
      "help.ticket_title": "Short human-readable task name.",
      "language.switch": "Switch language",
      "login.copy": "Sign in with GitHub. Your projects will appear after an admin adds you to them.",
      "login.eyebrow": "Team workspace",
      "login.github": "Continue with GitHub",
      "login.github_missing": "GitHub OAuth is not configured yet.",
      "login.local": "Use temporary local login",
      "login.title": "Welcome to RoundTable",
      "mcp.auth_header": "Use it as the HTTP header",
      "mcp.copy_bearer": "Copy as Bearer",
      "mcp.copied": "Copied",
      "mcp.copy_endpoint": "Copy endpoint",
      "mcp.create": "Create token",
      "mcp.create_token": "Create MCP token",
      "mcp.created": "New token created — copy it now, it is shown only once.",
      "mcp.endpoint": "Endpoint:",
      "mcp.personal_note": "Tokens are personal: a token acts as you, with your own project permissions. Each teammate creates their own.",
      "mcp.empty": "No tokens yet.",
      "mcp.eyebrow": "Automation",
      "mcp.how_copy": "Create a token here, copy it once, then use it in your MCP client as an Authorization: Bearer token.",
      "mcp.how_title": "How MCP tokens work",
      "mcp.revoke": "Revoke",
      "mcp.title": "MCP access",
      "mcp.tokens": "Tokens",
      "mcp.transport_note": "RoundTable exposes a JSON-RPC HTTP endpoint. External clients must trust the HTTPS certificate; self-signed certificates are rejected by many MCP clients.",
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
      "notifications.telegram_copy": "Generate a token, open your configured Telegram bot, and send /start plus that token.",
      "notifications.telegram_generate": "Generate link token",
      "notifications.telegram_help": "Generate a one-time token, then send it to the configured Telegram bot.",
      "notifications.telegram_send": "Send this to your Telegram bot:",
      "notifications.telegram_title": "How to link a phone",
      "notifications.telegram_unlink": "Unlink Telegram",
      "notifications.telegram_webhook": "Bot webhook endpoint:",
      "notifications.test": "Send test",
      "notifications.title": "Notifications",
      "placeholder.comment": "Add an update",
      "placeholder.existing_login": "GitHub login, for example octocat",
      "placeholder.github_repo": "owner/repo or https://github.com/owner/repo",
      "placeholder.installation_id": "installation id",
      "placeholder.project_description": "What this project is for",
      "placeholder.quick_comment": "Optional comment",
      "placeholder.ticket_description": "Optional description",
      "placeholder.ticket_title": "New ticket title",
      "priority.High": "High",
      "priority.Low": "Low",
      "priority.Medium": "Medium",
      "priority.Urgent": "Urgent",
      "projects.access": "Project access",
      "projects.add_member": "Add member",
      "projects.back_to_board": "Back to board",
      "projects.create": "Create project",
      "projects.danger": "Danger zone",
      "projects.delete": "Delete project",
      "projects.delete_confirm": "Delete this project and all its tickets? This cannot be undone.",
      "projects.delete_confirm_key": "Type the project key to confirm:",
      "projects.delete_help": "Deleting a project permanently removes all of its tickets, comments, and history. This cannot be undone.",
      "projects.details": "Project details",
      "projects.empty_copy": "Create the first project and RoundTable will start ticket keys from KEY-1.",
      "projects.empty_title": "No projects yet",
      "projects.eyebrow": "Workspace",
      "projects.available": "Available projects",
      "projects.member_hint": "You can open projects where an admin has added your GitHub login. Project creation is limited to workspace admins.",
      "projects.members": "Members",
      "projects.no_members": "No members yet.",
      "projects.last_admin_badge": "only admin",
      "projects.last_admin_copy": "Add another project admin before removing or demoting the current one.",
      "projects.last_admin_title": "Project needs an admin",
      "projects.remove_member": "Remove",
      "projects.save_details": "Save project",
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
      "theme.switch": "Switch theme",
      "ticket.activity": "Activity",
      "ticket.action.assigned": "assigned",
      "ticket.action.closed": "closed",
      "ticket.action.commented": "commented",
      "ticket.action.project_created": "created project",
      "ticket.action.project_updated": "updated project",
      "ticket.action.reopened": "reopened",
      "ticket.action.status_changed": "moved",
      "ticket.action.ticket_updated": "updated",
      "ticket.action.unwatching": "stopped watching",
      "ticket.action.watching": "started watching",
      "ticket.autosave_error": "Could not save",
      "ticket.autosave_saved": "Saved",
      "ticket.autosave_saving": "Saving...",
      "ticket.comments": "Comments",
      "ticket.details": "Details",
      "ticket.live_connected": "Live updates on",
      "ticket.live_reconnecting": "Reconnecting...",
      "ticket.new": "New ticket",
      "ticket.quick_edit": "Quick edit",
      "ticket.quick_create": "Quick create",
      "ticket.quick_create_help": "Create a ticket fast; details can be edited after opening it.",
      "ticket.save": "Save ticket",
      "ticket.unassigned": "Unassigned",
      "ticket.people": "People",
      "ticket.unwatch": "Unwatch ticket",
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
      "action.unwatch": "Не следить",
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
      "footer.tagline": "Круглый стол для ваших тикетов.",
      "github.create_project_first": "Сначала создайте проект.",
      "github.how_copy": "Вставьте owner/repo или ссылку GitHub. Этого достаточно, чтобы webhook связывал ветки, коммиты и PR с тикетами.",
      "github.how_title": "Как подключить GitHub",
      "github.installation_note": "Installation id необязателен и нужен только для продвинутых действий GitHub App, например автоматического создания autolinks в репозитории. Можно оставить пустым.",
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
      "help.member_login": "GitHub логин. Пользователя можно добавить до первого входа.",
      "help.priority": "По умолчанию Medium. Urgent используйте только для работы, которая прямо сейчас кого-то блокирует.",
      "help.project_description": "Короткий контекст для людей, которые позже откроют проект.",
      "help.project_key": "Короткий uppercase-префикс для ключей тикетов, например CRM или OPS.",
      "help.project_name": "Человеческое название проекта, которое видно в интерфейсе.",
      "help.role": "member может редактировать, viewer только читать, admin управляет доступом к проекту.",
      "help.status": "Где тикет сейчас находится на доске.",
      "help.ticket_description": "Добавьте контекст, критерии приемки, ссылки или заметки. Можно писать markdown-подобный текст.",
      "help.ticket_title": "Короткое человеческое название задачи.",
      "language.switch": "Сменить язык",
      "login.copy": "Войдите через GitHub. Проекты появятся после того, как админ добавит вам доступ.",
      "login.eyebrow": "Командное пространство",
      "login.github": "Войти через GitHub",
      "login.github_missing": "GitHub OAuth пока не настроен.",
      "login.local": "Войти временно локально",
      "login.title": "Добро пожаловать в RoundTable",
      "mcp.auth_header": "Используйте как HTTP-заголовок",
      "mcp.copy_bearer": "Скопировать как Bearer",
      "mcp.copied": "Скопировано",
      "mcp.copy_endpoint": "Скопировать endpoint",
      "mcp.create": "Создать токен",
      "mcp.create_token": "Создать MCP токен",
      "mcp.created": "Новый токен создан — скопируйте сейчас, он показывается только один раз.",
      "mcp.endpoint": "Endpoint:",
      "mcp.personal_note": "Токены персональные: токен действует от вашего имени с вашими правами в проектах. Каждый создаёт свой.",
      "mcp.empty": "Токенов пока нет.",
      "mcp.eyebrow": "Автоматизация",
      "mcp.how_copy": "Создайте токен здесь, скопируйте его один раз, затем используйте в MCP-клиенте как Authorization: Bearer токен.",
      "mcp.how_title": "Как работают MCP токены",
      "mcp.revoke": "Отозвать",
      "mcp.title": "Доступ MCP",
      "mcp.tokens": "Токены",
      "mcp.transport_note": "RoundTable отдаёт JSON-RPC HTTP endpoint. Внешние клиенты должны доверять HTTPS-сертификату; самоподписанные сертификаты многие MCP-клиенты отклоняют.",
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
      "notifications.telegram_copy": "Создайте токен, откройте настроенного Telegram-бота и отправьте /start плюс этот токен.",
      "notifications.telegram_generate": "Создать токен привязки",
      "notifications.telegram_help": "Создайте одноразовый токен и отправьте его настроенному Telegram-боту.",
      "notifications.telegram_send": "Отправьте это вашему Telegram-боту:",
      "notifications.telegram_title": "Как привязать телефон",
      "notifications.telegram_unlink": "Отвязать Telegram",
      "notifications.telegram_webhook": "Webhook endpoint бота:",
      "notifications.test": "Отправить тест",
      "notifications.title": "Уведомления",
      "placeholder.comment": "Добавить обновление",
      "placeholder.existing_login": "GitHub логин, например octocat",
      "placeholder.github_repo": "owner/repo или https://github.com/owner/repo",
      "placeholder.installation_id": "installation id",
      "placeholder.project_description": "Для чего этот проект",
      "placeholder.quick_comment": "Комментарий, если нужен",
      "placeholder.ticket_description": "Описание, если нужно",
      "placeholder.ticket_title": "Название нового тикета",
      "priority.High": "Высокий",
      "priority.Low": "Низкий",
      "priority.Medium": "Средний",
      "priority.Urgent": "Срочный",
      "projects.access": "Доступ к проекту",
      "projects.add_member": "Добавить участника",
      "projects.back_to_board": "Назад к доске",
      "projects.create": "Создать проект",
      "projects.danger": "Опасная зона",
      "projects.delete": "Удалить проект",
      "projects.delete_confirm": "Удалить проект и все его тикеты? Действие необратимо.",
      "projects.delete_confirm_key": "Введите ключ проекта для подтверждения:",
      "projects.delete_help": "Удаление проекта безвозвратно удалит все его тикеты, комментарии и историю. Отменить нельзя.",
      "projects.details": "Детали проекта",
      "projects.empty_copy": "Создайте первый проект, и RoundTable начнет тикеты с KEY-1.",
      "projects.empty_title": "Проектов пока нет",
      "projects.eyebrow": "Рабочее пространство",
      "projects.available": "Доступные проекты",
      "projects.member_hint": "Вы можете открывать проекты, куда админ добавил ваш GitHub логин. Создание проектов доступно только workspace admin.",
      "projects.members": "Участники",
      "projects.no_members": "Участников пока нет.",
      "projects.last_admin_badge": "единственный админ",
      "projects.last_admin_copy": "Добавьте ещё одного администратора проекта, прежде чем удалять или понижать текущего.",
      "projects.last_admin_title": "Проекту нужен администратор",
      "projects.remove_member": "Удалить",
      "projects.save_details": "Сохранить проект",
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
      "theme.switch": "Сменить тему",
      "ticket.activity": "История",
      "ticket.action.assigned": "назначил исполнителя",
      "ticket.action.closed": "закрыл тикет",
      "ticket.action.commented": "оставил комментарий",
      "ticket.action.project_created": "создал проект",
      "ticket.action.project_updated": "обновил проект",
      "ticket.action.reopened": "открыл тикет снова",
      "ticket.action.status_changed": "изменил статус",
      "ticket.action.ticket_updated": "обновил тикет",
      "ticket.action.unwatching": "перестал наблюдать",
      "ticket.action.watching": "начал наблюдать",
      "ticket.autosave_error": "Не удалось сохранить",
      "ticket.autosave_saved": "Сохранено",
      "ticket.autosave_saving": "Сохраняю...",
      "ticket.comments": "Комментарии",
      "ticket.details": "Детали",
      "ticket.live_connected": "Живые обновления включены",
      "ticket.live_reconnecting": "Переподключаюсь...",
      "ticket.new": "Новый тикет",
      "ticket.quick_edit": "Быстро изменить",
      "ticket.quick_create": "Быстрое создание",
      "ticket.quick_create_help": "Создайте тикет быстро; детали можно дописать после открытия.",
      "ticket.save": "Сохранить тикет",
      "ticket.unassigned": "Без исполнителя",
      "ticket.people": "Участники",
      "ticket.unwatch": "Не следить за тикетом",
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
    setupLocalTimes();
    setupActionLabels();
    setupActionDetails();
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
    button.removeAttribute("data-i18n");
    button.textContent = "";
    button.setAttribute("aria-label", translate("theme.switch", currentLang()) || translate(nextKey, currentLang()));
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
        "a, button, input, select, textarea, label, summary, details, .ticket-key, .priority-chip, .assignee-chip, .ticket-title, .ticket-title-input"
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
      autoScrollFrame: null,
      autoScrollSpeed: 0,
      lastClientX: event.clientX,
      lastClientY: event.clientY,
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

  function updateDragAutoScroll(clientX, clientY) {
    if (!dragState || !dragState.started) return;
    const edge = 88;
    const maxSpeed = 18;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
    let speed = 0;
    if (clientY < edge) {
      speed = -Math.ceil(((edge - clientY) / edge) * maxSpeed);
    } else if (clientY > viewportHeight - edge) {
      speed = Math.ceil(((clientY - (viewportHeight - edge)) / edge) * maxSpeed);
    }
    dragState.lastClientX = clientX;
    dragState.lastClientY = clientY;
    dragState.autoScrollSpeed = speed;
    if (!speed) {
      stopDragAutoScroll();
      return;
    }
    if (!dragState.autoScrollFrame) {
      dragState.autoScrollFrame = window.requestAnimationFrame(stepDragAutoScroll);
    }
  }

  function stepDragAutoScroll() {
    if (!dragState || !dragState.started || !dragState.autoScrollSpeed) {
      stopDragAutoScroll();
      return;
    }
    window.scrollBy({ top: dragState.autoScrollSpeed, left: 0, behavior: "auto" });
    moveDragPreview(dragState.lastClientX, dragState.lastClientY);
    updateDragTarget(dragState.lastClientX, dragState.lastClientY);
    dragState.autoScrollFrame = window.requestAnimationFrame(stepDragAutoScroll);
  }

  function stopDragAutoScroll() {
    if (!dragState || !dragState.autoScrollFrame) return;
    window.cancelAnimationFrame(dragState.autoScrollFrame);
    dragState.autoScrollFrame = null;
  }

  async function finishTicketDrag(event) {
    if (!dragState) return;
    const state = dragState;
    stopDragAutoScroll();
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
    stopDragAutoScroll();
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

  function csrfToken() {
    const board = document.querySelector(".board");
    if (board && board.dataset.csrf) return board.dataset.csrf;
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : "";
  }

  async function patchTicket(ticketKey, payload) {
    const response = await fetch(`/api/tickets/${ticketKey}`, {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
        "x-csrf-token": csrfToken(),
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  let activePopover = null;
  let activeChip = null;
  let popoverAnchorScrollY = 0;
  let popoverAnchorWidth = 0;

  function setupChipEditors() {
    document.querySelectorAll(".board").forEach((board) => {
      board.addEventListener("click", (event) => {
        const chip = event.target.closest(".chip-edit");
        if (!chip || !board.contains(chip)) return;
        event.preventDefault();
        if (activePopover && activeChip === chip) {
          closePopover();
          return;
        }
        openPopover(chip);
      });
    });
  }

  function setupBoardTitleEditors() {
    document.querySelectorAll("[data-title-edit]").forEach((button) => {
      button.addEventListener("click", () => startBoardTitleEdit(button));
    });
  }

  function startBoardTitleEdit(button) {
    const card = button.closest(".ticket-card");
    const titleEl = button.querySelector(".ticket-title");
    if (!card || !titleEl || button.classList.contains("is-editing")) return;
    const original = titleEl.textContent.trim();
    button.classList.add("is-editing");
    const input = document.createElement("input");
    input.className = "ticket-title-input";
    input.value = original;
    input.maxLength = 180;
    input.setAttribute("aria-label", translate("field.title", currentLang()) || "Title");
    button.replaceWith(input);
    input.focus();
    input.select();

    let finished = false;
    const restore = (value) => {
      titleEl.textContent = value;
      button.classList.remove("is-editing");
      input.replaceWith(button);
    };
    const save = async () => {
      if (finished) return;
      finished = true;
      const next = input.value.trim();
      if (!next || next === original) {
        restore(original);
        return;
      }
      card.classList.add("is-saving");
      input.disabled = true;
      try {
        const ticket = await patchTicket(card.dataset.ticketKey, { title: next });
        restore(ticket.title || next);
        flashSaved(card);
      } catch (error) {
        window.alert(error.message || "Could not update title");
        restore(original);
      } finally {
        card.classList.remove("is-saving");
      }
    };
    input.addEventListener("blur", save);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        input.blur();
      } else if (event.key === "Escape") {
        finished = true;
        restore(original);
      }
    });
  }

  function boardData(key, fallback) {
    const board = document.querySelector(".board");
    if (!board || !board.dataset[key]) return fallback;
    try {
      return JSON.parse(board.dataset[key]);
    } catch (error) {
      return fallback;
    }
  }

  function openPopover(chip) {
    closePopover();
    const card = chip.closest(".ticket-card");
    const field = chip.dataset.edit;
    const pop = document.createElement("div");
    pop.className = "popover-menu";
    if (field === "comment") {
      buildCommentPopover(pop, card);
    } else if (field === "description") {
      buildDescriptionPopover(pop, card);
    } else {
      buildOptionsPopover(pop, field, card, chip);
    }
    document.body.appendChild(pop);
    positionPopover(pop, chip);
    activePopover = pop;
    activeChip = chip;
    popoverAnchorScrollY = window.scrollY;
    popoverAnchorWidth = window.innerWidth;
    chip.setAttribute("aria-expanded", "true");
    window.setTimeout(() => {
      document.addEventListener("pointerdown", onOutsidePointer, true);
      document.addEventListener("keydown", onPopoverKey, true);
      window.addEventListener("scroll", onPopoverScroll, true);
      window.addEventListener("resize", onPopoverResize);
      const focusable = pop.querySelector("textarea, .popover-option");
      if (focusable) focusable.focus();
    }, 0);
  }

  function closePopover() {
    if (activeChip) activeChip.setAttribute("aria-expanded", "false");
    if (activePopover) activePopover.remove();
    activePopover = null;
    activeChip = null;
    document.removeEventListener("pointerdown", onOutsidePointer, true);
    document.removeEventListener("keydown", onPopoverKey, true);
    window.removeEventListener("scroll", onPopoverScroll, true);
    window.removeEventListener("resize", onPopoverResize);
  }

  // Close only on meaningful scrolling; small scrolls (e.g. mobile keyboard
  // nudging the viewport) just reposition the popover so it stays attached.
  function onPopoverScroll() {
    if (!activePopover || !activeChip) return;
    if (Math.abs(window.scrollY - popoverAnchorScrollY) > 120) {
      closePopover();
    } else {
      positionPopover(activePopover, activeChip);
    }
  }

  // The mobile virtual keyboard fires resize by changing height, not width.
  // Only treat width changes (orientation / real resize) as a reason to close.
  function onPopoverResize() {
    if (!activePopover || !activeChip) return;
    if (window.innerWidth !== popoverAnchorWidth) {
      closePopover();
    } else {
      positionPopover(activePopover, activeChip);
    }
  }

  function onOutsidePointer(event) {
    if (activePopover && !activePopover.contains(event.target) && event.target !== activeChip && !activeChip.contains(event.target)) {
      closePopover();
    }
  }

  function onPopoverKey(event) {
    if (event.key === "Escape") closePopover();
  }

  function positionPopover(pop, chip) {
    const rect = chip.getBoundingClientRect();
    pop.style.position = "fixed";
    pop.style.top = `${rect.bottom + 6}px`;
    let left = rect.left;
    const width = pop.offsetWidth;
    if (left + width > window.innerWidth - 8) left = window.innerWidth - 8 - width;
    if (left < 8) left = 8;
    pop.style.left = `${left}px`;
    const height = pop.offsetHeight;
    if (rect.bottom + 6 + height > window.innerHeight - 8) {
      pop.style.top = `${Math.max(8, rect.top - 6 - height)}px`;
    }
  }

  function buildOptionsPopover(pop, field, card, chip) {
    const current = chip.dataset.value || "";
    let options = [];
    if (field === "status") {
      options = boardData("statuses", []).map((s) => ({ value: s, label: translate(`status.${s}`, currentLang()) || s }));
    } else if (field === "priority") {
      options = boardData("priorities", []).map((p) => ({ value: p, label: translate(`priority.${p}`, currentLang()) || p }));
    } else if (field === "assignee_id") {
      options = [{ value: "", label: translate("ticket.unassigned", currentLang()) || "Unassigned" }];
      boardData("members", []).forEach((m) => options.push({ value: String(m.id), label: m.name || m.login }));
    }
    options.forEach((opt) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "popover-option";
      if (String(opt.value) === String(current)) button.classList.add("is-current");
      button.textContent = opt.label;
      button.addEventListener("click", () => applyFieldChange(card, field, opt.value));
      pop.appendChild(button);
    });
  }

  async function applyFieldChange(card, field, value) {
    const payload = {};
    payload[field] = field === "assignee_id" ? (value ? Number(value) : null) : value;
    closePopover();
    card.classList.add("is-saving");
    try {
      const ticket = await patchTicket(card.dataset.ticketKey, payload);
      applyTicketUpdate(card, ticket);
      flashSaved(card);
    } catch (error) {
      window.alert(error.message || "Could not update ticket");
    } finally {
      card.classList.remove("is-saving");
    }
  }

  function buildCommentPopover(pop, card) {
    pop.classList.add("popover-comment");
    const textarea = document.createElement("textarea");
    textarea.rows = 3;
    textarea.placeholder = translate("placeholder.quick_comment", currentLang()) || "Optional comment";
    const actions = document.createElement("div");
    actions.className = "popover-actions";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "primary tiny";
    button.textContent = translate("action.comment", currentLang()) || "Comment";
    actions.appendChild(button);
    pop.appendChild(textarea);
    pop.appendChild(actions);
    const submit = async () => {
      const body = textarea.value.trim();
      if (!body) return;
      button.disabled = true;
      textarea.disabled = true;
      const formData = new FormData();
      formData.append("body", body);
      card.classList.add("is-saving");
      try {
        const response = await fetch(`/api/tickets/${card.dataset.ticketKey}/comments`, {
          method: "POST",
          headers: { "x-csrf-token": csrfToken() },
          body: formData,
        });
        if (!response.ok) throw new Error(await response.text());
        closePopover();
        flashSaved(card);
      } catch (error) {
        window.alert(error.message || "Could not add comment");
        button.disabled = false;
        textarea.disabled = false;
      } finally {
        card.classList.remove("is-saving");
      }
    };
    button.addEventListener("click", submit);
    textarea.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") submit();
    });
  }

  function buildDescriptionPopover(pop, card) {
    pop.classList.add("popover-desc");
    const textarea = document.createElement("textarea");
    textarea.rows = 6;
    textarea.value = card.dataset.description || "";
    textarea.placeholder = translate("help.ticket_description", currentLang()) || "Description";
    const actions = document.createElement("div");
    actions.className = "popover-actions";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "primary tiny";
    button.textContent = translate("action.save", currentLang()) || "Save";
    actions.appendChild(button);
    pop.appendChild(textarea);
    pop.appendChild(actions);
    const submit = async () => {
      button.disabled = true;
      textarea.disabled = true;
      card.classList.add("is-saving");
      try {
        const ticket = await patchTicket(card.dataset.ticketKey, { description: textarea.value });
        card.dataset.description = ticket && ticket.description != null ? ticket.description : textarea.value;
        closePopover();
        flashSaved(card);
      } catch (error) {
        window.alert(error.message || "Could not save description");
        button.disabled = false;
        textarea.disabled = false;
      } finally {
        card.classList.remove("is-saving");
      }
    };
    button.addEventListener("click", submit);
    textarea.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") submit();
    });
  }

  function applyTicketUpdate(card, ticket) {
    if (!card || !ticket) return;
    card.dataset.ticketKey = ticket.key;
    card.dataset.description = ticket.description || "";
    const keyLink = card.querySelector(".ticket-key");
    if (keyLink) {
      keyLink.href = `/t/${ticket.key}`;
      keyLink.textContent = ticket.key;
    }
    const titleEl = card.querySelector(".ticket-title");
    if (titleEl) titleEl.textContent = ticket.title || "";
    const openLink = card.querySelector(".ticket-open-link");
    if (openLink) openLink.href = `/t/${ticket.key}`;
    updateCardClasses(card, ticket);
    moveCardToStatus(card, ticket.status);
    setChipValue(card, "status", ticket.status, translate(`status.${ticket.status}`, currentLang()) || ticket.status);
    setChipValue(card, "priority", ticket.priority, translate(`priority.${ticket.priority}`, currentLang()) || ticket.priority);
    updateAssigneeChip(card, ticket);
    refreshColumnCounts();
  }

  function setChipValue(card, field, value, label) {
    const chip = card.querySelector(`.chip-edit[data-edit="${field}"]`);
    if (!chip) return;
    chip.dataset.value = value || "";
    const labelEl = chip.querySelector(".chip-label");
    if (labelEl) {
      labelEl.dataset.i18n = field === "status" ? `status.${value}` : `priority.${value}`;
      labelEl.textContent = label;
    }
    if (field === "priority") {
      chip.className = chip.className
        .split(/\s+/)
        .filter((name) => name && !name.startsWith("priority-chip-"))
        .join(" ");
      chip.classList.add(`priority-chip-${String(value).toLowerCase()}`);
    }
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

  function updateAssigneeChip(card, ticket) {
    const chip = card.querySelector('.chip-edit[data-edit="assignee_id"]');
    if (!chip) return;
    chip.dataset.value = ticket.assignee_id ? String(ticket.assignee_id) : "";
    renderAvatar(chip.querySelector(".avatar-dot"), ticket.assignee_avatar_url, ticket.assignee_login);
    const label = chip.querySelector(".assignee-label");
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

  function createTicketCard(ticket) {
    const card = document.createElement("article");
    card.className = "ticket-card";
    card.dataset.ticketKey = ticket.key;
    card.dataset.description = ticket.description || "";
    card.innerHTML = `
      <div class="ticket-card-top">
        <span class="drag-handle" data-icon="grip-vertical" role="button" tabindex="0" aria-label="Move ticket"></span>
      </div>
      <div class="ticket-title-row">
        <a class="ticket-key"></a>
        <button class="ticket-title-edit" type="button" data-title-edit aria-label="Edit title">
          <span class="ticket-title"></span>
        </button>
        <a class="ticket-open-link" data-icon="external-link" aria-label="Open ticket"></a>
      </div>
      <div class="ticket-card-chips">
        <button type="button" class="chip chip-edit chip-status" data-edit="status" aria-haspopup="true">
          <span class="chip-dot" aria-hidden="true"></span>
          <span class="chip-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-priority" data-edit="priority" aria-haspopup="true">
          <span class="chip-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-assignee" data-edit="assignee_id" aria-haspopup="true">
          <span class="avatar-dot" aria-hidden="true"></span>
          <span class="chip-label assignee-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-desc" data-edit="description" data-icon="square-pen" aria-haspopup="true" aria-label="Edit description"></button>
        <button type="button" class="chip chip-edit chip-comment" data-edit="comment" data-icon="message-square-plus" aria-haspopup="true" aria-label="Comment"></button>
      </div>
    `;
    card.addEventListener("pointerdown", startTicketDrag);
    const titleButton = card.querySelector("[data-title-edit]");
    if (titleButton) titleButton.addEventListener("click", () => startBoardTitleEdit(titleButton));
    applyTicketUpdate(card, ticket);
    renderIcons();
    return card;
  }

  function applyLiveTicket(ticket) {
    if (!ticket || !ticket.key) return;
    let card = document.querySelector(`.ticket-card[data-ticket-key="${cssEscape(ticket.key)}"]`);
    if (!card) {
      card = createTicketCard(ticket);
      const zone = document.querySelector(`.dropzone[data-status="${cssEscape(ticket.status)}"]`);
      if (!zone) return;
      zone.prepend(card);
      refreshColumnCounts();
      flashSaved(card);
      return;
    }
    applyTicketUpdate(card, ticket);
  }

  function setupBoardLiveEvents() {
    const liveRoot = document.querySelector(".board[data-events-url], [data-ticket-page][data-events-url]");
    if (!liveRoot || !window.EventSource) return;
    const source = new EventSource(liveRoot.dataset.eventsUrl);
    const handleTicketEvent = (event) => {
      try {
        const payload = JSON.parse(event.data || "{}");
        applyLiveTicket(payload.ticket);
        applyLiveTicketPage(payload);
      } catch (error) {
        // Ignore malformed live events; the next reload/resync will recover.
      }
    };
    source.addEventListener("ticket_created", handleTicketEvent);
    source.addEventListener("ticket_changed", handleTicketEvent);
    source.addEventListener("ticket_commented", handleTicketEvent);
    window.addEventListener("beforeunload", () => source.close());
  }

  function applyLiveTicketPage(payload) {
    const page = document.querySelector("[data-ticket-page]");
    const ticket = payload && payload.ticket;
    if (!page || !ticket || page.dataset.ticketKey !== ticket.key) return;
    const title = document.querySelector("[data-ticket-page-title]");
    if (title) title.textContent = ticket.title || "";
    const form = document.querySelector("[data-ticket-autosave]");
    if (form && document.activeElement && !form.contains(document.activeElement)) {
      setFormValue(form, "title", ticket.title || "");
      setFormValue(form, "description", ticket.description || "");
      setFormValue(form, "status", ticket.status || "");
      setFormValue(form, "priority", ticket.priority || "");
      setFormValue(form, "assignee_id", ticket.assignee_id ? String(ticket.assignee_id) : "");
    }
    prependActivity(payload.action);
  }

  function setFormValue(form, field, value) {
    const control = form.elements[field];
    if (control && control.value !== value) control.value = value;
  }

  function prependActivity(action) {
    if (!action || !action.id) return;
    const list = document.querySelector("[data-activity-list]");
    if (!list || list.querySelector(`[data-action-id="${cssEscape(action.id)}"]`)) return;
    const item = document.createElement("li");
    item.dataset.actionId = action.id;
    const actorLine = document.createElement("span");
    actorLine.className = "profile-line activity-actor";
    const avatar = document.createElement("span");
    avatar.className = "avatar-dot";
    avatar.setAttribute("aria-hidden", "true");
    const actor = document.createElement("strong");
    actor.textContent = action.actor_name || action.actor_login || "System";
    actorLine.append(avatar, actor);
    renderAvatar(avatar, action.actor_avatar_url || "", action.actor_login || "");

    const label = document.createElement("span");
    label.dataset.actionLabel = action.action || "";
    label.textContent = action.action || "";

    const detail = document.createElement("span");
    detail.className = "activity-detail muted";
    detail.dataset.actionField = action.field || "";
    detail.dataset.oldValue = action.old_value || "";
    detail.dataset.newValue = action.new_value || "";

    const time = document.createElement("time");
    time.dataset.localTime = action.created_at || "";
    time.textContent = action.created_at || "";
    item.append(actorLine, label, detail, time);
    list.prepend(item);
    setupActionLabels();
    setupActionDetails();
    setupLocalTimes();
  }

  function setupTicketAutosave() {
    const form = document.querySelector("[data-ticket-autosave]");
    if (!form) return;
    const ticketKey = form.dataset.ticketKey;
    const status = form.querySelector("[data-autosave-status]");
    const fields = ["title", "description", "status", "priority", "assignee_id"];
    const timers = new Map();

    form.addEventListener("submit", (event) => event.preventDefault());

    const setStatus = (key) => {
      if (!status) return;
      status.dataset.i18n = key;
      status.textContent = translate(key, currentLang()) || status.textContent;
      status.dataset.state = key.endsWith("error") ? "error" : key.endsWith("saving") ? "saving" : "saved";
    };

    const fieldValue = (field) => {
      const control = form.elements[field];
      if (!control) return undefined;
      if (field === "assignee_id") return control.value ? Number(control.value) : null;
      return control.value;
    };

    const saveField = async (field) => {
      const payload = {};
      payload[field] = fieldValue(field);
      setStatus("ticket.autosave_saving");
      try {
        const ticket = await patchTicket(ticketKey, payload);
        if (field === "title") {
          const title = document.querySelector("[data-ticket-page-title]");
          if (title) title.textContent = ticket.title || payload.title;
        }
        prependActivity(ticket._action);
        setStatus("ticket.autosave_saved");
      } catch (error) {
        setStatus("ticket.autosave_error");
      }
    };

    fields.forEach((field) => {
      const control = form.elements[field];
      if (!control) return;
      const saveSoon = (delay) => {
        window.clearTimeout(timers.get(field));
        timers.set(field, window.setTimeout(() => saveField(field), delay));
      };
      if (control.tagName === "SELECT") {
        control.addEventListener("change", () => saveSoon(0));
      } else {
        control.addEventListener("input", () => saveSoon(650));
        control.addEventListener("blur", () => saveSoon(0));
      }
    });
  }

  function cssEscape(value) {
    if (window.CSS && window.CSS.escape) return window.CSS.escape(value);
    return String(value).replace(/"/g, '\\"');
  }

  function setupConfirms() {
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        const message = translate(form.dataset.confirm, currentLang()) || "Are you sure?";
        if (!window.confirm(message)) event.preventDefault();
      });
    });
  }

  function setupCopyButtons() {
    document.querySelectorAll("[data-copy-text]").forEach((control) => {
      const copy = async () => {
        const canSwapText = control.tagName === "BUTTON";
        const originalText = control.dataset.i18n
          ? translate(control.dataset.i18n, currentLang())
          : control.textContent;
        try {
          await navigator.clipboard.writeText(control.dataset.copyText || "");
          control.classList.add("is-copied");
          if (canSwapText && control.textContent.trim()) {
            control.textContent = translate("mcp.copied", currentLang()) || "Copied";
          }
          window.setTimeout(() => {
            control.classList.remove("is-copied");
            if (canSwapText && control.textContent.trim() && originalText) control.textContent = originalText;
            renderIcons();
          }, 1100);
          renderIcons();
        } catch (error) {
          window.prompt("Copy", control.dataset.copyText || "");
        }
      };
      control.addEventListener("click", copy);
      control.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        copy();
      });
    });
  }

  function setupLocalTimes() {
    document.querySelectorAll("[data-local-time]").forEach((element) => {
      const value = element.dataset.localTime;
      if (!value) return;
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return;
      element.textContent = new Intl.DateTimeFormat(currentLang() === "ru" ? "ru-RU" : "en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date);
    });
  }

  function setupActionLabels() {
    document.querySelectorAll("[data-action-label]").forEach((element) => {
      const key = `ticket.action.${element.dataset.actionLabel}`;
      const value = translate(key, currentLang());
      if (value) element.textContent = value;
      element.dataset.i18n = key;
    });
  }

  function actionValueLabel(field, value) {
    if (!value) return "";
    if (field === "status") return translate(`status.${value}`, currentLang()) || value;
    if (field === "priority") return translate(`priority.${value}`, currentLang()) || value;
    if (field === "title") return value;
    if (field === "description") return "";
    if (field === "assignee_id") return "";
    return value;
  }

  function setupActionDetails() {
    document.querySelectorAll("[data-action-field]").forEach((element) => {
      const field = element.dataset.actionField || "";
      const oldLabel = actionValueLabel(field, element.dataset.oldValue || "");
      const newLabel = actionValueLabel(field, element.dataset.newValue || "");
      if (oldLabel && newLabel) {
        element.textContent = `· ${oldLabel} → ${newLabel}`;
      } else if (newLabel) {
        element.textContent = `· ${newLabel}`;
      } else if (field === "description" || field === "assignee_id") {
        element.textContent = "";
      } else {
        element.textContent = "";
      }
    });
  }

  function setupMemberRoleForms() {
    document.querySelectorAll(".member-role-form select").forEach((select) => {
      select.addEventListener("change", () => {
        const form = select.closest("form");
        if (form) form.requestSubmit();
      });
    });
  }

  function setupAssigneePickers() {
    document.querySelectorAll("[data-assignee-picker]").forEach((picker) => {
      const current = picker.querySelector("[data-assignee-current]");
      const input = picker.closest("form")?.querySelector('input[name="assignee_id"]');
      if (!current || !input) return;
      current.addEventListener("click", () => {
        document.querySelectorAll(".assignee-picker.is-open").forEach((openPicker) => {
          if (openPicker !== picker) openPicker.classList.remove("is-open");
        });
        picker.classList.toggle("is-open");
      });
      picker.querySelectorAll(".assignee-option").forEach((option) => {
        option.addEventListener("click", () => {
          input.value = option.dataset.assigneeValue || "";
          picker.querySelectorAll(".assignee-option.is-current").forEach((item) => item.classList.remove("is-current"));
          option.classList.add("is-current");
          renderAvatar(current.querySelector(".avatar-dot"), option.dataset.assigneeAvatar || "", option.dataset.assigneeLogin || "");
          const label = current.querySelector("span:last-child");
          if (label) {
            if (input.value) {
              label.removeAttribute("data-i18n");
              label.textContent = option.dataset.assigneeName || option.textContent.trim();
            } else {
              label.dataset.i18n = "ticket.unassigned";
              label.textContent = translate("ticket.unassigned", currentLang()) || "Unassigned";
            }
          }
          picker.classList.remove("is-open");
        });
      });
    });
    document.addEventListener("pointerdown", (event) => {
      if (event.target.closest("[data-assignee-picker]")) return;
      document.querySelectorAll(".assignee-picker.is-open").forEach((picker) => picker.classList.remove("is-open"));
    });
  }

  function setupMenus() {
    document.addEventListener("click", (event) => {
      document.querySelectorAll("details.app-menu[open]").forEach((menu) => {
        if (!menu.contains(event.target)) menu.removeAttribute("open");
      });
    });
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
    setupChipEditors();
    setupBoardTitleEditors();
    setupTicketAutosave();
    setupMenus();
    setupConfirms();
    setupCopyButtons();
    setupLocalTimes();
    setupActionLabels();
    setupActionDetails();
    setupMemberRoleForms();
    setupAssigneePickers();
    setupOpenCreate();
    setupMobileStatusTabs();
    setupTooltips();
    setupBoardLiveEvents();
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
    updateDragAutoScroll(event.clientX, event.clientY);
  });

  window.addEventListener("pointerup", (event) => {
    if (!dragState) return;
    event.preventDefault();
    finishTicketDrag(event);
  });

  window.addEventListener("pointercancel", cancelTicketDrag);
})();
