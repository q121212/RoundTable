(() => {
  let dragState = null;
  const STORAGE_LANG = "roundtable.lang";
  const STORAGE_THEME = "roundtable.theme";
  const messages = {
    en: {
      "action.close": "Close",
      "action.comment": "Comment",
      "action.create": "Create",
      "action.drag": "Drag",
      "action.mark_closed": "Mark ticket closed",
      "action.move": "Move",
      "action.reopen": "Reopen",
      "action.reopen_ticket": "Reopen ticket",
      "action.save": "Save",
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
      "help.drag_ticket": "Drag with mouse or finger to another status.",
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
      "nav.notifications": "Notifications",
      "nav.projects": "Projects",
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
      "placeholder.ticket_title": "New ticket title",
      "priority.High": "High",
      "priority.Low": "Low",
      "priority.Medium": "Medium",
      "priority.Urgent": "Urgent",
      "projects.access": "Project access",
      "projects.add_member": "Add member",
      "projects.create": "Create project",
      "projects.empty_copy": "Create the first project and RoundTable will start ticket keys from KEY-1.",
      "projects.empty_title": "No projects yet",
      "projects.eyebrow": "Workspace",
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
      "ticket.quick_create": "Quick create",
      "ticket.quick_create_help": "Create a ticket fast; details can be edited after opening it.",
      "ticket.save": "Save ticket",
      "ticket.unassigned": "Unassigned",
      "ticket.watch": "Watch ticket",
      "ticket.workflow_help": "These actions change ticket state; they do not close this page.",
    },
    ru: {
      "action.close": "Закрыть",
      "action.comment": "Комментировать",
      "action.create": "Создать",
      "action.drag": "Тащить",
      "action.mark_closed": "Закрыть тикет",
      "action.move": "Переместить",
      "action.reopen": "Открыть снова",
      "action.reopen_ticket": "Открыть тикет снова",
      "action.save": "Сохранить",
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
      "help.drag_ticket": "Перетащите мышью или пальцем в другой статус.",
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
      "nav.notifications": "Уведомления",
      "nav.projects": "Проекты",
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
      "placeholder.ticket_title": "Название нового тикета",
      "priority.High": "Высокий",
      "priority.Low": "Низкий",
      "priority.Medium": "Средний",
      "priority.Urgent": "Срочный",
      "projects.access": "Доступ к проекту",
      "projects.add_member": "Добавить участника",
      "projects.create": "Создать проект",
      "projects.empty_copy": "Создайте первый проект, и RoundTable начнет тикеты с KEY-1.",
      "projects.empty_title": "Проектов пока нет",
      "projects.eyebrow": "Рабочее пространство",
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
      "ticket.quick_create": "Быстрое создание",
      "ticket.quick_create_help": "Создайте тикет быстро; детали можно дописать после открытия.",
      "ticket.save": "Сохранить тикет",
      "ticket.unassigned": "Без исполнителя",
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
    document.querySelectorAll("[data-lang-option]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.langOption === lang));
    });
    updateThemeButton();
  }

  function applyTheme(theme) {
    localStorage.setItem(STORAGE_THEME, theme);
    document.documentElement.dataset.theme = theme;
    updateThemeButton();
  }

  function updateThemeButton() {
    const button = document.querySelector("[data-theme-toggle]");
    if (!button) return;
    const nextKey = currentTheme() === "dark" ? "theme.light" : "theme.dark";
    button.dataset.i18n = nextKey;
    button.textContent = translate(nextKey, currentLang());
  }

  function setupPreferences() {
    applyTheme(currentTheme());
    applyLanguage(currentLang());
    document.querySelectorAll("[data-lang-option]").forEach((button) => {
      button.addEventListener("click", () => applyLanguage(button.dataset.langOption));
    });
    const themeButton = document.querySelector("[data-theme-toggle]");
    if (themeButton) {
      themeButton.addEventListener("click", () => {
        applyTheme(currentTheme() === "dark" ? "light" : "dark");
      });
    }
  }

  function setupBoardDnD() {
    document.querySelectorAll(".drag-handle").forEach((handle) => {
      handle.addEventListener("pointerdown", startTicketDrag);
    });
  }

  function startTicketDrag(event) {
    if (event.button !== undefined && event.button !== 0) return;
    const card = event.currentTarget.closest(".ticket-card");
    if (!card) return;
    event.preventDefault();
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
    dragState = {
      card,
      currentZone: null,
      handle: event.currentTarget,
      hiddenColumns,
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top,
      placeholder,
      pointerId: event.pointerId,
      preview,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
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
    if (!zone || !status) {
      state.card.classList.remove("drag-source");
      state.placeholder.replaceWith(state.card);
      return;
    }
    zone.appendChild(state.card);
    state.placeholder.remove();
    state.card.classList.remove("drag-source");
    try {
      await patchTicket(state.card.dataset.ticketKey, { status });
      window.location.reload();
    } catch (error) {
      window.alert(error.message || "Could not move ticket");
      window.location.reload();
    }
  }

  function cancelTicketDrag() {
    if (!dragState) return;
    const state = dragState;
    dragState = null;
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
      if (event.target.matches(".help-dot")) {
        event.preventDefault();
        event.target.classList.toggle("tooltip-open");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupPreferences();
    setupBoardDnD();
    setupMobileStatusTabs();
    setupTooltips();
  });

  window.addEventListener("pointermove", (event) => {
    if (!dragState) return;
    event.preventDefault();
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
