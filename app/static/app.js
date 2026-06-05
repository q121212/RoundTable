(() => {
  let draggedCard = null;
  const STORAGE_LANG = "roundtable.lang";
  const STORAGE_THEME = "roundtable.theme";
  const messages = {
    en: {
      "action.close": "Close",
      "action.comment": "Comment",
      "action.create": "Create",
      "action.move": "Move",
      "action.reopen": "Reopen",
      "action.save": "Save",
      "field.assignee": "Assignee",
      "field.description": "Description",
      "field.email": "Email",
      "field.github_login": "GitHub login",
      "field.github_repo": "GitHub repo",
      "field.key": "Key",
      "field.name": "Name",
      "field.priority": "Priority",
      "field.reporter": "Reporter",
      "field.status": "Status",
      "field.title": "Title",
      "github.create_project_first": "Create a project first.",
      "github.integration": "Integration",
      "github.links": "GitHub links",
      "github.repo_links": "Repository links",
      "github.settings": "GitHub settings",
      "github.use_key_prefix": "Use",
      "github.use_key_suffix": "in branches, commits, or PRs to link code.",
      "login.copy": "Use GitHub OAuth in production. Local login is available only when enabled by configuration.",
      "login.eyebrow": "Local ticket tracker",
      "login.github": "Continue with GitHub",
      "login.github_missing": "GitHub OAuth is not configured yet.",
      "login.local": "Use local login",
      "login.title": "Sign in to RoundTable",
      "mcp.create": "Create token",
      "mcp.create_token": "Create MCP token",
      "mcp.created": "New token created. Copy it now:",
      "mcp.empty": "No tokens yet.",
      "mcp.eyebrow": "Automation",
      "mcp.revoke": "Revoke",
      "mcp.title": "MCP access",
      "mcp.tokens": "Tokens",
      "nav.logout": "Log out",
      "nav.notifications": "Notifications",
      "nav.projects": "Projects",
      "notifications.channels": "Channels",
      "notifications.eyebrow": "Personal settings",
      "notifications.save": "Save preferences",
      "notifications.telegram_generate": "Generate link token",
      "notifications.telegram_help": "Generate a one-time token, then send it to the configured Telegram bot.",
      "notifications.telegram_send": "Send this to your Telegram bot:",
      "notifications.test": "Send test",
      "notifications.title": "Notifications",
      "placeholder.comment": "Add an update",
      "placeholder.existing_login": "Existing user login",
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
      "ticket.save": "Save ticket",
      "ticket.unassigned": "Unassigned",
      "ticket.watch": "Watch ticket",
    },
    ru: {
      "action.close": "Закрыть",
      "action.comment": "Комментировать",
      "action.create": "Создать",
      "action.move": "Переместить",
      "action.reopen": "Открыть снова",
      "action.save": "Сохранить",
      "field.assignee": "Исполнитель",
      "field.description": "Описание",
      "field.email": "Email",
      "field.github_login": "GitHub логин",
      "field.github_repo": "GitHub репозиторий",
      "field.key": "Ключ",
      "field.name": "Название",
      "field.priority": "Приоритет",
      "field.reporter": "Автор",
      "field.status": "Статус",
      "field.title": "Заголовок",
      "github.create_project_first": "Сначала создайте проект.",
      "github.integration": "Интеграция",
      "github.links": "Связи GitHub",
      "github.repo_links": "Репозитории",
      "github.settings": "Настройки GitHub",
      "github.use_key_prefix": "Используйте",
      "github.use_key_suffix": "в ветках, коммитах или PR, чтобы связать код.",
      "login.copy": "В продакшене используйте GitHub OAuth. Локальный вход доступен только если включен в конфигурации.",
      "login.eyebrow": "Локальный трекер задач",
      "login.github": "Войти через GitHub",
      "login.github_missing": "GitHub OAuth пока не настроен.",
      "login.local": "Войти локально",
      "login.title": "Вход в RoundTable",
      "mcp.create": "Создать токен",
      "mcp.create_token": "Создать MCP токен",
      "mcp.created": "Новый токен создан. Скопируйте его сейчас:",
      "mcp.empty": "Токенов пока нет.",
      "mcp.eyebrow": "Автоматизация",
      "mcp.revoke": "Отозвать",
      "mcp.title": "Доступ MCP",
      "mcp.tokens": "Токены",
      "nav.logout": "Выйти",
      "nav.notifications": "Уведомления",
      "nav.projects": "Проекты",
      "notifications.channels": "Каналы",
      "notifications.eyebrow": "Личные настройки",
      "notifications.save": "Сохранить настройки",
      "notifications.telegram_generate": "Создать токен привязки",
      "notifications.telegram_help": "Создайте одноразовый токен и отправьте его настроенному Telegram-боту.",
      "notifications.telegram_send": "Отправьте это вашему Telegram-боту:",
      "notifications.test": "Отправить тест",
      "notifications.title": "Уведомления",
      "placeholder.comment": "Добавить обновление",
      "placeholder.existing_login": "Логин существующего пользователя",
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
      "ticket.save": "Сохранить тикет",
      "ticket.unassigned": "Без исполнителя",
      "ticket.watch": "Следить за тикетом",
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
    document.querySelectorAll(".ticket-card[draggable=true]").forEach((card) => {
      card.addEventListener("dragstart", () => {
        draggedCard = card;
        card.classList.add("dragging");
      });
      card.addEventListener("dragend", () => {
        card.classList.remove("dragging");
        draggedCard = null;
      });
    });

    document.querySelectorAll(".dropzone").forEach((zone) => {
      zone.addEventListener("dragover", (event) => {
        event.preventDefault();
        zone.classList.add("drag-over");
      });
      zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
      zone.addEventListener("drop", async (event) => {
        event.preventDefault();
        zone.classList.remove("drag-over");
        if (!draggedCard) return;
        const ticketKey = draggedCard.dataset.ticketKey;
        const status = zone.dataset.status;
        zone.appendChild(draggedCard);
        await patchTicket(ticketKey, { status });
        window.location.reload();
      });
    });
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

  document.addEventListener("DOMContentLoaded", () => {
    setupPreferences();
    setupBoardDnD();
    setupMobileStatusTabs();
  });
})();
