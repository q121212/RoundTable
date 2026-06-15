(() => {
  let dragState = null;
  const STORAGE_LANG = "roundtable.lang";
  const STORAGE_THEME = "roundtable.theme";
  const STORAGE_BOARD_URL = "roundtable.lastBoardUrl";
  const STORAGE_SOUND_MODE = "roundtable.soundMode";
  const STORAGE_SOUND_THEME = "roundtable.soundTheme";
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
      "action.remove": "Remove",
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
      "field.sprint": "Sprint",
      "field.status": "Status",
      "field.ticket_type": "Type",
      "field.link_type": "Link type",
      "field.target_ticket": "Target ticket",
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
      "help.ticket_type": "Type of work. Epics are bigger containers; tasks, bugs, and stories are regular tickets.",
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
      "mcp.never_used": "Never used",
      "mcp.revoke": "Revoke",
      "mcp.title": "MCP access",
      "mcp.tokens": "Tokens",
      "mcp.transport_note": "RoundTable exposes a JSON-RPC HTTP endpoint. External clients must trust the HTTPS certificate; self-signed certificates are rejected by many MCP clients.",
      "link.blocked_by": "blocked by",
      "link.blocks": "blocks",
      "link.duplicates": "duplicates",
      "link.parent": "parent of",
      "link.relates": "relates to",
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
      "placeholder.target_ticket": "GT-12 or part of title",
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
      "projects.settings_access": "Access",
      "projects.settings_board": "Board",
      "projects.settings_danger": "Danger",
      "projects.settings_project": "Project",
      "projects.statuses": "Board statuses",
      "projects.statuses_help": "Only selected statuses appear on the board and in ticket status menus. Move tickets out before disabling a status.",
      "projects.statuses_selected": "Statuses used by this project",
      "projects.save_statuses": "Save statuses",
      "projects.ticket_types_help": "Selected types are available when creating and editing tickets. Move existing tickets before disabling a type.",
      "projects.ticket_types_selected": "Ticket types used by this project",
      "projects.save_board_settings": "Save board settings",
      "projects.title": "Projects",
      "sound.copy": "Short local sounds for board events. Different event types use different cues.",
      "sound.events_copy": "New tickets, comments, assignments, status changes, Done/Closed, and ticket links.",
      "sound.events_title": "Events with sound",
      "sound.focused": "Focused",
      "sound.off": "Off",
      "sound.soft": "Soft",
      "sound.test": "Test sound",
      "sound.theme_bright": "Bright",
      "sound.theme_round": "Round",
      "sound.title": "Sounds on this device",
      "sprint.activate": "Activate",
      "sprint.active": "Active",
      "sprint.all": "All sprints",
      "sprint.backlog": "No sprint",
      "sprint.close": "Close",
      "sprint.closed": "Closed",
      "sprint.create": "Create sprint",
      "sprint.empty": "No sprints yet.",
      "sprint.ends_on": "Ends",
      "sprint.goal": "Goal",
      "sprint.manage": "Sprint planning",
      "sprint.manage_link": "Manage sprints",
      "sprint.none": "No sprint",
      "sprint.planned": "Planned",
      "sprint.sprints": "Sprints",
      "sprint.starts_on": "Starts",
      "sprint.status": "Status",
      "sprint.ticket_count": "tickets",
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
      "ticket.action.linked": "linked ticket",
      "ticket.action.project_created": "created project",
      "ticket.action.project_updated": "updated project",
      "ticket.action.github_linked": "linked GitHub",
      "ticket.action.reordered": "reordered",
      "ticket.action.reopened": "reopened",
      "ticket.action.sprint_changed": "changed sprint",
      "ticket.action.status_changed": "moved",
      "ticket.action.ticket_created": "created ticket",
      "ticket.action.ticket_updated": "updated",
      "ticket.action.type_changed": "changed type",
      "ticket.action.unlinked": "removed ticket link",
      "ticket.action.unwatching": "stopped watching",
      "ticket.action.watching": "started watching",
      "ticket.autosave_error": "Could not save",
      "ticket.autosave_saved": "Saved",
      "ticket.autosave_saving": "Saving...",
      "ticket.comments": "Comments",
      "ticket.details": "Details",
      "ticket.live_connected": "Live updates on",
      "ticket.live_reconnecting": "Reconnecting...",
      "ticket.add_link": "Link ticket",
      "ticket.links": "Ticket links",
      "ticket.new": "New ticket",
      "ticket.no_links": "No linked tickets yet.",
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
      "type.Bug": "Bug",
      "type.Epic": "Epic",
      "type.Story": "Story",
      "type.Task": "Task",
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
      "action.remove": "Удалить",
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
      "field.sprint": "Спринт",
      "field.status": "Статус",
      "field.ticket_type": "Тип",
      "field.link_type": "Тип связи",
      "field.target_ticket": "Связанный тикет",
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
      "help.ticket_type": "Тип работы. Эпик — крупный контейнер; задачи, баги и истории — обычные тикеты.",
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
      "mcp.never_used": "Не использовался",
      "mcp.revoke": "Отозвать",
      "mcp.title": "Доступ MCP",
      "mcp.tokens": "Токены",
      "mcp.transport_note": "RoundTable отдаёт JSON-RPC HTTP endpoint. Внешние клиенты должны доверять HTTPS-сертификату; самоподписанные сертификаты многие MCP-клиенты отклоняют.",
      "link.blocked_by": "заблокирован",
      "link.blocks": "блокирует",
      "link.duplicates": "дублирует",
      "link.parent": "родитель для",
      "link.relates": "связан с",
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
      "placeholder.target_ticket": "GT-12 или часть названия",
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
      "projects.settings_access": "Доступ",
      "projects.settings_board": "Доска",
      "projects.settings_danger": "Опасная зона",
      "projects.settings_project": "Проект",
      "projects.statuses": "Статусы доски",
      "projects.statuses_help": "На доске и в меню тикетов будут только выбранные статусы. Перед отключением статуса перенесите из него тикеты.",
      "projects.statuses_selected": "Статусы этого проекта",
      "projects.save_statuses": "Сохранить статусы",
      "projects.ticket_types_help": "Выбранные типы доступны при создании и редактировании тикетов. Перед отключением типа переведите существующие тикеты.",
      "projects.ticket_types_selected": "Типы тикетов этого проекта",
      "projects.save_board_settings": "Сохранить настройки доски",
      "projects.title": "Проекты",
      "sound.copy": "Короткие локальные звуки для событий доски. Для разных типов событий используются разные сигналы.",
      "sound.events_copy": "Новые тикеты, комментарии, назначения, смена статуса, Done/Closed и связи тикетов.",
      "sound.events_title": "Какие события звучат",
      "sound.focused": "Важное",
      "sound.off": "Выкл",
      "sound.soft": "Мягко",
      "sound.test": "Проверить звук",
      "sound.theme_bright": "Яркая",
      "sound.theme_round": "Мягкая",
      "sound.title": "Звуки на этом устройстве",
      "sprint.activate": "Активировать",
      "sprint.active": "Активный",
      "sprint.all": "Все спринты",
      "sprint.backlog": "Без спринта",
      "sprint.close": "Закрыть",
      "sprint.closed": "Закрыт",
      "sprint.create": "Создать спринт",
      "sprint.empty": "Спринтов пока нет.",
      "sprint.ends_on": "Конец",
      "sprint.goal": "Цель",
      "sprint.manage": "Планирование спринтов",
      "sprint.manage_link": "Управлять спринтами",
      "sprint.none": "Без спринта",
      "sprint.planned": "План",
      "sprint.sprints": "Спринты",
      "sprint.starts_on": "Начало",
      "sprint.status": "Статус",
      "sprint.ticket_count": "тикетов",
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
      "ticket.action.linked": "связал тикет",
      "ticket.action.project_created": "создал проект",
      "ticket.action.project_updated": "обновил проект",
      "ticket.action.github_linked": "связал GitHub",
      "ticket.action.reordered": "изменил порядок",
      "ticket.action.reopened": "открыл тикет снова",
      "ticket.action.sprint_changed": "изменил спринт",
      "ticket.action.status_changed": "изменил статус",
      "ticket.action.ticket_created": "создал тикет",
      "ticket.action.ticket_updated": "обновил тикет",
      "ticket.action.type_changed": "изменил тип",
      "ticket.action.unlinked": "удалил связь",
      "ticket.action.unwatching": "перестал наблюдать",
      "ticket.action.watching": "начал наблюдать",
      "ticket.autosave_error": "Не удалось сохранить",
      "ticket.autosave_saved": "Сохранено",
      "ticket.autosave_saving": "Сохраняю...",
      "ticket.comments": "Комментарии",
      "ticket.details": "Детали",
      "ticket.live_connected": "Живые обновления включены",
      "ticket.live_reconnecting": "Переподключаюсь...",
      "ticket.add_link": "Связать тикет",
      "ticket.links": "Связи тикета",
      "ticket.new": "Новый тикет",
      "ticket.no_links": "Связанных тикетов пока нет.",
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
      "type.Bug": "Баг",
      "type.Epic": "Эпик",
      "type.Story": "История",
      "type.Task": "Задача",
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

  function ticketTypeIcon(type) {
    return {
      Task: "circle-check",
      Epic: "layers-3",
      Bug: "bug",
      Story: "book-open",
    }[type] || "circle-dot";
  }

  function ticketTypeClass(type) {
    return `type-${String(type || "Task").toLowerCase()}`;
  }

  let audioContext = null;

  function currentSoundMode() {
    return localStorage.getItem(STORAGE_SOUND_MODE) || "off";
  }

  function currentSoundTheme() {
    return localStorage.getItem(STORAGE_SOUND_THEME) || "round";
  }

  function setSoundMode(mode) {
    const value = ["off", "soft", "focused"].includes(mode) ? mode : "off";
    localStorage.setItem(STORAGE_SOUND_MODE, value);
    updateSoundControls();
  }

  function setSoundTheme(theme) {
    const value = ["round", "bright"].includes(theme) ? theme : "round";
    localStorage.setItem(STORAGE_SOUND_THEME, value);
    updateSoundControls();
  }

  function updateSoundControls() {
    document.querySelectorAll("[data-sound-mode]").forEach((button) => {
      button.classList.toggle("active", button.dataset.soundMode === currentSoundMode());
      button.setAttribute("aria-pressed", button.dataset.soundMode === currentSoundMode() ? "true" : "false");
    });
    document.querySelectorAll("[data-sound-theme]").forEach((button) => {
      button.classList.toggle("active", button.dataset.soundTheme === currentSoundTheme());
      button.setAttribute("aria-pressed", button.dataset.soundTheme === currentSoundTheme() ? "true" : "false");
    });
  }

  function setupSoundPreferences() {
    updateSoundControls();
    document.querySelectorAll("[data-sound-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        setSoundMode(button.dataset.soundMode || "off");
        if (currentSoundMode() !== "off") playTicketSound({ event: "test" }, true);
      });
    });
    document.querySelectorAll("[data-sound-test]").forEach((button) => {
      button.addEventListener("click", () => playTicketSound({ event: "test" }, true));
    });
    document.querySelectorAll("[data-sound-theme]").forEach((button) => {
      button.addEventListener("click", () => {
        setSoundTheme(button.dataset.soundTheme || "round");
        if (currentSoundMode() !== "off") playTicketSound({ event: "test" }, true);
      });
    });
    document.addEventListener(
      "pointerdown",
      () => {
        if (currentSoundMode() !== "off") ensureAudioContext();
      },
      { once: true }
    );
  }

  function ensureAudioContext() {
    if (!window.AudioContext && !window.webkitAudioContext) return null;
    if (!audioContext) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioContext = new AudioContextClass();
    }
    if (audioContext.state === "suspended") audioContext.resume();
    return audioContext;
  }

  function soundKind(payload) {
    const action = payload && payload.action ? payload.action.action : "";
    const ticket = payload && payload.ticket ? payload.ticket : {};
    if (payload && payload.event === "test") return "test";
    if (action === "closed" || action === "reopened" || ticket.status === "Done" || ticket.status === "Closed") return "success";
    if (action === "status_changed") return "status";
    if (action === "commented" || payload.event === "ticket_commented") return "comment";
    if (action === "assigned") return "assigned";
    if (payload.event === "ticket_created" || action === "ticket_created") return "created";
    if (payload.event === "ticket_linked" || payload.event === "ticket_unlinked" || action === "linked" || action === "unlinked") return "linked";
    return "changed";
  }

  function shouldPlayTicketSound(payload, forced = false) {
    const mode = currentSoundMode();
    if (mode === "off" && !forced) return false;
    if (forced) return true;
    if (mode === "soft") return true;
    const ticket = payload && payload.ticket ? payload.ticket : {};
    const action = payload && payload.action ? payload.action : {};
    const userId = document.body.dataset.userId || "";
    if (!userId) return false;
    const ticketPage = document.querySelector("[data-ticket-page]");
    if (ticketPage && ticketPage.dataset.ticketKey === ticket.key) return true;
    if (ticket.assignee_id && String(ticket.assignee_id) === userId) return true;
    if (action.action === "assigned" && String(action.new_value || "") === userId) return true;
    return false;
  }

  function playTone(ctx, start, frequency, duration, gainValue, type = "sine") {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(frequency, start);
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(gainValue, start + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    osc.connect(gain).connect(ctx.destination);
    osc.start(start);
    osc.stop(start + duration + 0.02);
  }

  function playTicketSound(payload, forced = false) {
    if (!shouldPlayTicketSound(payload, forced)) return;
    const ctx = ensureAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime + 0.01;
    const bright = currentSoundTheme() === "bright";
    const volume = bright ? 0.045 : 0.035;
    const kind = soundKind(payload);
    if (bright && kind === "success") {
      playTone(ctx, now, 659.25, 0.08, volume, "triangle");
      playTone(ctx, now + 0.08, 987.77, 0.11, volume * 0.8, "triangle");
      playTone(ctx, now + 0.16, 1318.51, 0.12, volume * 0.55, "sine");
    } else if (kind === "success") {
      playTone(ctx, now, 523.25, 0.12, volume, "sine");
      playTone(ctx, now + 0.07, 659.25, 0.14, volume * 0.9, "sine");
      playTone(ctx, now + 0.14, 783.99, 0.18, volume * 0.8, "triangle");
    } else if (bright && kind === "status") {
      playTone(ctx, now, 493.88, 0.05, volume * 0.9, "square");
      playTone(ctx, now + 0.07, 739.99, 0.08, volume * 0.6, "triangle");
    } else if (kind === "status") {
      playTone(ctx, now, 392, 0.09, volume, "triangle");
      playTone(ctx, now + 0.08, 587.33, 0.12, volume * 0.85, "triangle");
    } else if (bright && kind === "comment") {
      playTone(ctx, now, 880, 0.035, volume * 0.55, "sine");
      playTone(ctx, now + 0.055, 880, 0.035, volume * 0.5, "sine");
      playTone(ctx, now + 0.11, 1174.66, 0.045, volume * 0.45, "sine");
    } else if (kind === "comment") {
      playTone(ctx, now, 740, 0.06, volume * 0.65, "sine");
      playTone(ctx, now + 0.09, 660, 0.08, volume * 0.55, "sine");
    } else if (bright && kind === "assigned") {
      playTone(ctx, now, 392, 0.08, volume * 0.8, "sawtooth");
      playTone(ctx, now + 0.09, 523.25, 0.09, volume * 0.65, "triangle");
    } else if (kind === "assigned") {
      playTone(ctx, now, 330, 0.11, volume * 0.9, "triangle");
      playTone(ctx, now + 0.1, 440, 0.12, volume * 0.75, "triangle");
    } else if (bright && kind === "created") {
      playTone(ctx, now, 1046.5, 0.04, volume * 0.55, "sine");
      playTone(ctx, now + 0.045, 1567.98, 0.06, volume * 0.4, "sine");
    } else if (kind === "created") {
      playTone(ctx, now, 880, 0.06, volume * 0.55, "sine");
      playTone(ctx, now + 0.05, 1174.66, 0.08, volume * 0.45, "sine");
    } else if (bright && kind === "linked") {
      playTone(ctx, now, 698.46, 0.035, volume * 0.4, "square");
      playTone(ctx, now + 0.045, 523.25, 0.035, volume * 0.32, "square");
    } else if (kind === "linked") {
      playTone(ctx, now, 494, 0.04, volume * 0.45, "square");
    } else {
      playTone(ctx, now, 440, 0.08, volume * 0.55, "sine");
    }
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
      originalZone: card.closest(".dropzone"),
      originalAfterKey: ticketKeyBefore(card),
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
    if (zone && dragState.placeholder) {
      const before = cardBeforePointer(zone, clientY);
      if (before) {
        zone.insertBefore(dragState.placeholder, before);
      } else {
        zone.appendChild(dragState.placeholder);
      }
    }
  }

  function cardBeforePointer(zone, clientY) {
    const cards = Array.from(zone.querySelectorAll(".ticket-card:not(.drag-source)"));
    return cards.find((card) => {
      const rect = card.getBoundingClientRect();
      return clientY < rect.top + rect.height / 2;
    }) || null;
  }

  function ticketKeyBefore(element) {
    let previous = element.previousElementSibling;
    while (previous) {
      if (previous.classList && previous.classList.contains("ticket-card") && !previous.classList.contains("drag-source")) {
        return previous.dataset.ticketKey || "";
      }
      previous = previous.previousElementSibling;
    }
    return "";
  }

  function restoreCardPosition(card, zone, afterKey) {
    if (!zone) return;
    if (!afterKey) {
      zone.insertBefore(card, zone.querySelector(".ticket-card"));
      return;
    }
    const previous = zone.querySelector(`.ticket-card[data-ticket-key="${cssEscape(afterKey)}"]`);
    if (previous && previous.nextSibling) {
      zone.insertBefore(card, previous.nextSibling);
    } else {
      zone.appendChild(card);
    }
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
    const previousZone = state.originalZone;
    const previousStatus = previousZone ? previousZone.dataset.status : "";
    const afterKey = ticketKeyBefore(state.placeholder);
    if (!zone || !status) {
      state.card.classList.remove("drag-source");
      restoreCardPosition(state.card, previousZone, state.originalAfterKey);
      state.placeholder.remove();
      refreshColumnCounts();
      return;
    }
    state.placeholder.replaceWith(state.card);
    state.card.classList.remove("drag-source");
    refreshColumnCounts();
    if (status === previousStatus && afterKey === state.originalAfterKey) return;
    try {
      const ticket = await patchTicket(state.card.dataset.ticketKey, { status, position_after_key: afterKey });
      applyTicketUpdate(state.card, ticket);
    } catch (error) {
      restoreCardPosition(state.card, previousZone, state.originalAfterKey);
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
    restoreCardPosition(state.card, state.originalZone, state.originalAfterKey);
    state.placeholder.remove();
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

  // Mobile keyboards and touch-dragging can scroll the viewport while a popover
  // is open. Keep it open and attached; explicit outside taps still close it.
  function onPopoverScroll() {
    if (!activePopover || !activeChip) return;
    positionPopover(activePopover, activeChip);
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
    } else if (field === "ticket_type") {
      options = boardData("ticketTypes", []).map((t) => ({
        value: t,
        label: translate(`type.${t}`, currentLang()) || t,
        icon: ticketTypeIcon(t),
      }));
    } else if (field === "priority") {
      options = boardData("priorities", []).map((p) => ({ value: p, label: translate(`priority.${p}`, currentLang()) || p }));
    } else if (field === "sprint_id") {
      options = [{ value: "", label: translate("sprint.none", currentLang()) || "No sprint" }];
      boardData("sprints", [])
        .filter((s) => s.status !== "closed")
        .forEach((s) => options.push({ value: String(s.id), label: s.name }));
    } else if (field === "assignee_id") {
      options = [{ value: "", label: translate("ticket.unassigned", currentLang()) || "Unassigned" }];
      boardData("members", []).forEach((m) => options.push({ value: String(m.id), label: m.name || m.login }));
    }
    options.forEach((opt) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "popover-option";
      if (String(opt.value) === String(current)) button.classList.add("is-current");
      if (opt.icon) {
        const icon = document.createElement("span");
        icon.className = `type-icon ${ticketTypeClass(opt.value)}`;
        icon.dataset.icon = opt.icon;
        icon.setAttribute("aria-hidden", "true");
        button.appendChild(icon);
      }
      const label = document.createElement("span");
      label.textContent = opt.label;
      button.appendChild(label);
      button.addEventListener("click", () => applyFieldChange(card, field, opt.value));
      pop.appendChild(button);
    });
    renderIcons();
  }

  async function applyFieldChange(card, field, value) {
    const payload = {};
    payload[field] = field === "assignee_id" || field === "sprint_id" ? (value ? Number(value) : null) : value;
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
    setChipValue(card, "ticket_type", ticket.ticket_type, translate(`type.${ticket.ticket_type}`, currentLang()) || ticket.ticket_type);
    setChipValue(card, "status", ticket.status, translate(`status.${ticket.status}`, currentLang()) || ticket.status);
    setChipValue(card, "priority", ticket.priority, translate(`priority.${ticket.priority}`, currentLang()) || ticket.priority);
    setChipValue(card, "sprint_id", ticket.sprint_id ? String(ticket.sprint_id) : "", ticket.sprint_name || translate("sprint.none", currentLang()) || "No sprint");
    updateAssigneeChip(card, ticket);
    updateLinkedTickets(card, ticket);
    refreshColumnCounts();
    renderIcons();
  }

  function setChipValue(card, field, value, label) {
    const chip = card.querySelector(`.chip-edit[data-edit="${field}"]`);
    if (!chip) return;
    chip.dataset.value = value || "";
    const labelEl = chip.querySelector(".chip-label");
    if (labelEl) {
      if (field === "status") labelEl.dataset.i18n = `status.${value}`;
      if (field === "priority") labelEl.dataset.i18n = `priority.${value}`;
      if (field === "ticket_type") labelEl.dataset.i18n = `type.${value}`;
      if (field === "sprint_id" && !value) labelEl.dataset.i18n = "sprint.none";
      if (field === "sprint_id" && value) labelEl.removeAttribute("data-i18n");
      labelEl.textContent = label;
    }
    if (field === "priority") {
      chip.className = chip.className
        .split(/\s+/)
        .filter((name) => name && !name.startsWith("priority-chip-"))
        .join(" ");
      chip.classList.add(`priority-chip-${String(value).toLowerCase()}`);
    }
    if (field === "ticket_type") {
      const icon = chip.querySelector(".type-icon");
      if (icon) {
        icon.className = `type-icon ${ticketTypeClass(value)}`;
        icon.dataset.icon = ticketTypeIcon(value);
      }
    }
  }

  function updateCardClasses(card, ticket) {
    card.className = card.className
      .split(/\s+/)
      .filter((name) => name && !name.startsWith("priority-") && !name.startsWith("status-") && !name.startsWith("type-"))
      .join(" ");
    card.classList.add("ticket-card", `priority-${ticket.priority.toLowerCase()}`, `status-${ticket.status.toLowerCase().replace(/\s+/g, "-")}`, `type-${String(ticket.ticket_type || "Task").toLowerCase()}`);
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

  function updateLinkedTickets(card, ticket) {
    const links = card.querySelector(".ticket-card-links");
    if (!links) return;
    const linked = Array.isArray(ticket.linked_tickets) ? ticket.linked_tickets : [];
    links.innerHTML = "";
    links.classList.toggle("is-empty", linked.length === 0);
    if (!linked.length) return;
    const icon = document.createElement("span");
    icon.className = "ticket-links-icon";
    icon.dataset.icon = "link";
    icon.setAttribute("aria-hidden", "true");
    links.appendChild(icon);
    linked.slice(0, 3).forEach((item) => {
      const pill = document.createElement("a");
      pill.className = "linked-ticket-pill";
      pill.href = `/t/${item.other_key}`;
      pill.textContent = item.other_key;
      if (item.other_title) pill.title = item.other_title;
      links.appendChild(pill);
    });
    if (linked.length > 3) {
      const more = document.createElement("span");
      more.className = "linked-ticket-more";
      more.textContent = `+${linked.length - 3}`;
      links.appendChild(more);
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
        <button type="button" class="chip chip-edit chip-type" data-edit="ticket_type" aria-haspopup="true">
          <span class="type-icon" aria-hidden="true"></span>
          <span class="chip-label"></span>
        </button>
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
        <button type="button" class="chip chip-edit chip-sprint" data-edit="sprint_id" aria-haspopup="true">
          <span class="chip-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-desc" data-edit="description" data-icon="square-pen" aria-haspopup="true" aria-label="Edit description"></button>
        <button type="button" class="chip chip-edit chip-comment" data-edit="comment" data-icon="message-square-plus" aria-haspopup="true" aria-label="Comment"></button>
      </div>
      <div class="ticket-card-links is-empty"></div>
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
        payload.event = payload.event || event.type;
        applyLiveTicket(payload.ticket);
        applyLiveTicketPage(payload);
        playTicketSound(payload);
      } catch (error) {
        // Ignore malformed live events; the next reload/resync will recover.
      }
    };
    source.addEventListener("ticket_created", handleTicketEvent);
    source.addEventListener("ticket_changed", handleTicketEvent);
    source.addEventListener("ticket_commented", handleTicketEvent);
    source.addEventListener("ticket_linked", handleTicketEvent);
    source.addEventListener("ticket_unlinked", handleTicketEvent);
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
      setFormValue(form, "sprint_id", ticket.sprint_id ? String(ticket.sprint_id) : "");
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
    const fields = ["title", "description", "ticket_type", "status", "priority", "assignee_id", "sprint_id"];
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
      if (field === "assignee_id" || field === "sprint_id") return control.value ? Number(control.value) : null;
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
      if (control.tagName === "SELECT" || control.type === "hidden") {
        control.addEventListener("change", () => saveSoon(0));
      } else {
        control.addEventListener("input", () => saveSoon(650));
        control.addEventListener("blur", () => saveSoon(0));
      }
    });
  }

  function setupTypePickers() {
    document.querySelectorAll("[data-type-picker]").forEach((picker) => {
      const field = picker.parentElement ? picker.parentElement.querySelector('input[name="ticket_type"]') : null;
      const toggle = picker.querySelector("[data-type-toggle]");
      const menu = picker.querySelector(".type-picker-menu");
      const selectedIcon = picker.querySelector("[data-selected-type-icon]");
      const selectedLabel = picker.querySelector("[data-selected-type-label]");
      if (!field) return;
      const update = (value, notify = false) => {
        field.value = value;
        picker.querySelectorAll("[data-type-value]").forEach((button) => {
          const selected = button.dataset.typeValue === value;
          button.classList.toggle("is-selected", selected);
          button.setAttribute("aria-selected", selected ? "true" : "false");
        });
        if (selectedIcon) {
          selectedIcon.className = `type-icon ${ticketTypeClass(value)}`;
          selectedIcon.dataset.icon = ticketTypeIcon(value);
        }
        if (selectedLabel) {
          selectedLabel.dataset.i18n = `type.${value}`;
          selectedLabel.textContent = translate(`type.${value}`, currentLang()) || value;
        }
        renderIcons();
        if (notify) field.dispatchEvent(new Event("change", { bubbles: true }));
      };
      const close = () => {
        picker.classList.remove("is-open");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
      };
      if (toggle) {
        toggle.addEventListener("click", (event) => {
          event.stopPropagation();
          const isOpen = picker.classList.toggle("is-open");
          toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });
        toggle.addEventListener("keydown", (event) => {
          if (event.key !== "ArrowDown" && event.key !== "Enter" && event.key !== " ") return;
          event.preventDefault();
          picker.classList.add("is-open");
          toggle.setAttribute("aria-expanded", "true");
          const current = menu && menu.querySelector(".type-choice.is-selected");
          if (current) current.focus();
        });
      }
      picker.querySelectorAll("[data-type-value]").forEach((button) => {
        button.addEventListener("click", () => {
          update(button.dataset.typeValue || "Task", true);
          close();
        });
        button.addEventListener("keydown", (event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            close();
            if (toggle) toggle.focus();
          }
        });
      });
      update(field.value || "Task");
    });
    document.addEventListener("click", (event) => {
      document.querySelectorAll("[data-type-picker].is-open").forEach((picker) => {
        if (picker.contains(event.target)) return;
        picker.classList.remove("is-open");
        const toggle = picker.querySelector("[data-type-toggle]");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  function setupTicketSearchInputs() {
    document.querySelectorAll("[data-ticket-search]").forEach((search) => {
      const input = search.querySelector("[data-ticket-search-input]");
      const valueField = search.querySelector("[data-ticket-search-value]");
      const results = search.querySelector("[data-ticket-search-results]");
      const form = search.closest("form");
      if (!input || !valueField || !results) return;
      let timer = null;
      let controller = null;
      let options = [];

      const close = () => {
        search.classList.remove("is-open");
        results.innerHTML = "";
      };

      const selectTicket = (ticket) => {
        valueField.value = ticket.key;
        input.value = `${ticket.key} · ${ticket.title}`;
        input.dataset.selectedKey = ticket.key;
        close();
      };

      const renderResults = (tickets) => {
        options = tickets;
        results.innerHTML = "";
        if (!tickets.length) {
          close();
          return;
        }
        tickets.forEach((ticket, index) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "ticket-search-option";
          button.setAttribute("role", "option");
          button.dataset.ticketKey = ticket.key;
          const badge = document.createElement("span");
          badge.className = "field-badge ticket-type-badge";
          const icon = document.createElement("span");
          icon.className = `type-icon ${ticketTypeClass(ticket.ticket_type)}`;
          icon.dataset.icon = ticketTypeIcon(ticket.ticket_type);
          icon.setAttribute("aria-hidden", "true");
          const key = document.createElement("span");
          key.textContent = ticket.key;
          const title = document.createElement("span");
          title.textContent = ticket.title;
          badge.append(icon, key);
          button.append(badge, title);
          if (index === 0) button.classList.add("is-active");
          button.addEventListener("click", () => selectTicket(ticket));
          results.appendChild(button);
        });
        search.classList.add("is-open");
        renderIcons();
      };

      const runSearch = async () => {
        const query = input.value.trim();
        valueField.value = "";
        input.dataset.selectedKey = "";
        if (!query) {
          close();
          return;
        }
        if (/^[A-Z][A-Z0-9]{1,9}-\d+$/i.test(query)) {
          valueField.value = query.toUpperCase();
        }
        if (controller) controller.abort();
        controller = new AbortController();
        const url = new URL(search.dataset.searchUrl || "", window.location.origin);
        url.searchParams.set("q", query);
        url.searchParams.set("exclude", search.dataset.excludeKey || "");
        try {
          const response = await fetch(url, { signal: controller.signal });
          if (!response.ok) throw new Error("search failed");
          const data = await response.json();
          renderResults(Array.isArray(data.tickets) ? data.tickets : []);
        } catch (error) {
          if (error.name !== "AbortError") close();
        }
      };

      input.addEventListener("input", () => {
        window.clearTimeout(timer);
        timer = window.setTimeout(runSearch, 180);
      });
      input.addEventListener("focus", () => {
        if (options.length) renderResults(options);
      });
      input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          close();
          return;
        }
        if (event.key !== "Enter" || !search.classList.contains("is-open")) return;
        const active = results.querySelector(".ticket-search-option.is-active");
        if (!active) return;
        const ticket = options.find((item) => item.key === active.dataset.ticketKey);
        if (!ticket) return;
        event.preventDefault();
        selectTicket(ticket);
      });
      if (form) {
        form.addEventListener("submit", (event) => {
          const raw = input.value.trim();
          const exact = raw.match(/^[A-Z][A-Z0-9]{1,9}-\d+/i);
          if (!valueField.value && exact) valueField.value = exact[0].toUpperCase();
          if (!valueField.value && options.length) {
            valueField.value = options[0].key;
          }
          if (!valueField.value) {
            event.preventDefault();
            input.focus();
          }
        });
      }
    });
    document.addEventListener("click", (event) => {
      document.querySelectorAll("[data-ticket-search].is-open").forEach((search) => {
        if (search.contains(event.target)) return;
        search.classList.remove("is-open");
        const results = search.querySelector("[data-ticket-search-results]");
        if (results) results.innerHTML = "";
      });
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
        year: "numeric",
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
    if (field === "ticket_type") return translate(`type.${value}`, currentLang()) || value;
    if (field === "ticket_link") return value;
    if (field === "sprint_id") return `#${value}`;
    if (field === "sort_order") return "";
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
      } else if (field === "description" || field === "assignee_id" || field === "sprint_id") {
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
    setupTypePickers();
    setupTicketSearchInputs();
    setupSoundPreferences();
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
