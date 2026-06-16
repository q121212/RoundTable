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
      "field.story_points": "Story points",
      "field.ticket_type": "Type",
      "field.link_type": "Link type",
      "field.target_ticket": "Target ticket",
      "field.title": "Title",
      "footer.tagline": "A round table for your tickets.",
      "column.story_points": "Story points in this status",
      "column.ticket_count": "Tickets in this status",
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
      "help.sprint": "Sprint or iteration this ticket is planned in.",
      "help.status": "Where the ticket currently is on the board.",
      "help.story_points": "Small effort estimate. Use 0 when not estimated.",
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
      "mentions.empty": "No matching people",
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
      "projects.settings": "Project settings",
      "projects.settings_access": "Access",
      "projects.settings_board": "Board",
      "projects.settings_danger": "Danger",
      "projects.settings_project": "Project",
      "projects.statuses": "Board statuses",
      "projects.statuses_help": "Only selected statuses appear on the board and in ticket status menus. Move tickets out before disabling a status.",
      "projects.statuses_selected": "Statuses used by this project",
      "projects.ticket_types_help": "Selected types are available when creating and editing tickets. Move existing tickets before disabling a type.",
      "projects.ticket_types_selected": "Ticket types used by this project",
      "projects.title": "Projects",
      "projects.tools": "Project tools",
      "sound.copy": "Short local sounds for board events. Different event types use different cues.",
      "sound.events_copy": "New tickets, comments, assignments, status changes, sprint changes, Done/Closed, and ticket links.",
      "sound.events_title": "Events with sound",
      "sound.focused": "Focused",
      "sound.off": "Off",
      "sound.soft": "Soft",
      "sound.test": "Test sound",
      "sound.theme_bright": "Bright",
      "sound.theme_round": "Round",
      "sound.title": "Sounds on this device",
      "stats.assignees": "Assignees",
      "stats.board_return": "Back to board",
      "stats.closed": "Closed",
      "stats.closed_help": "Tickets currently in Closed.",
      "stats.done": "Done",
      "stats.done_help": "Tickets currently in Done.",
      "stats.empty": "No tickets here yet.",
      "stats.flow": "Flow",
      "stats.more_tickets": "more",
      "stats.open": "Open",
      "stats.open_help": "Tickets that are not Done or Closed.",
      "stats.open_points": "Open SP",
      "stats.open_points_help": "Story points from open tickets.",
      "stats.people": "People",
      "stats.points": "Story points",
      "stats.priorities": "Priorities",
      "stats.assignees_help": "Work currently assigned to each person.",
      "stats.priorities_help": "Ticket count and story points grouped by priority.",
      "stats.shape": "Shape",
      "stats.sprints": "Sprints",
      "stats.sprints_help": "Tickets and story points planned by sprint.",
      "stats.statuses": "Statuses",
      "stats.statuses_help": "How tickets and story points are distributed across board statuses.",
      "stats.status_bar_help": "Top row compares ticket count with the busiest status; bottom row compares story points with total project points.",
      "stats.ticket_count": "Tickets",
      "stats.timeline": "Timeline",
      "stats.title": "Statistics",
      "stats.total": "Total tickets",
      "stats.total_help": "All tickets in this project.",
      "stats.types": "Types",
      "stats.types_help": "How work is split between tasks, epics, bugs, and stories.",
      "stats.visibility": "Statistics visibility",
      "stats.visibility_admin": "Project admins only",
      "stats.visibility_all": "Everyone in project",
      "stats.visibility_help": "By default, every project member can open project statistics.",
      "stats.visibility_member": "Members and admins",
      "stats.visibility_viewer": "Viewers, members, and admins",
      "stats.workload": "Workload",
      "sprint.activate": "Activate",
      "sprint.active": "Active sprints",
      "sprint.active_short": "Active",
      "sprint.all": "All sprints",
      "sprint.backlog": "No sprint",
      "sprint.close": "Close",
      "sprint.closed": "Closed",
      "sprint.create": "Create sprint",
      "sprint.empty": "No sprints yet.",
      "sprint.ends_on": "Ends",
      "sprint.filter_modes": "Views",
      "sprint.find_placeholder": "Find sprint",
      "sprint.find_or_create_placeholder": "Find or name sprint",
      "sprint.goal": "Goal",
      "sprint.goal_placeholder": "What should this sprint achieve?",
      "sprint.manage": "Sprint planning",
      "sprint.manage_copy": "Plan, activate, close, and reopen project sprints.",
      "sprint.manage_link": "Manage sprints",
      "sprint.new": "New sprint",
      "sprint.no_matches": "No matching sprints",
      "sprint.none": "No sprint",
      "sprint.open_sprints": "Sprints",
      "sprint.planned": "Planned",
      "sprint.quick_create": "Create sprint",
      "sprint.quick_create_placeholder": "New sprint name",
      "sprint.quick_create_help": "Create a sprint without leaving the board. Dates are optional.",
      "sprint.recent_closed": "Recent closed",
      "sprint.reopen": "Reopen",
      "sprint.save": "Save sprint",
      "sprint.selected_archive": "Selected archive",
      "sprint.existing": "Existing sprints",
      "sprint.sprints": "Sprints",
      "sprint.starts_on": "Starts",
      "sprint.status": "Status",
      "sprint.ticket_count": "tickets",
      "sprint.ticket_count_short": "t",
      "sprint.days_left": "days left",
      "sprint.ended": "ended",
      "sprint.ends_today": "ends today",
      "sprint.total_days": "sprint days",
      "status.all": "All",
      "story_points.none": "No SP",
      "story_points.short": "SP",
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
      "ticket.action.ticket_deleted": "deleted ticket",
      "ticket.action.ticket_updated": "updated",
      "ticket.action.type_changed": "changed type",
      "ticket.action.unlinked": "removed ticket link",
      "ticket.action.unwatching": "stopped watching",
      "ticket.action.watching": "started watching",
      "ticket.autosave_error": "Could not save",
      "ticket.autosave_saved": "Saved",
      "ticket.autosave_saving": "Saving...",
      "ticket.comments": "Comments",
      "ticket.delete": "Delete ticket",
      "ticket.delete_confirm": "Type the ticket key to confirm:",
      "ticket.delete_help": "Deleting a ticket permanently removes its comments, links, watchers, and history. This cannot be undone.",
      "ticket.delete_own_only": "Non-admins can delete only their own tickets",
      "ticket.delete_own_only_help": "Project admins are not limited by this checkbox.",
      "ticket.delete_policy": "Ticket deletion",
      "ticket.delete_policy_admin": "Project admins only",
      "ticket.delete_policy_help": "Delete action appears only on the ticket page for users allowed by this project.",
      "ticket.delete_policy_member": "Admins and members",
      "ticket.delete_policy_role_help": "Choose the lowest project role that can delete tickets.",
      "ticket.delete_policy_viewer": "Everyone with project access",
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
      "field.story_points": "Сторипоинты",
      "field.ticket_type": "Тип",
      "field.link_type": "Тип связи",
      "field.target_ticket": "Связанный тикет",
      "field.title": "Заголовок",
      "footer.tagline": "Круглый стол для ваших тикетов.",
      "column.story_points": "Сторипоинты в этом статусе",
      "column.ticket_count": "Тикетов в этом статусе",
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
      "help.sprint": "Спринт или итерация, в которую запланирован тикет.",
      "help.status": "Где тикет сейчас находится на доске.",
      "help.story_points": "Короткая оценка объема работы. 0 означает, что оценки пока нет.",
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
      "mentions.empty": "Никого не нашли",
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
      "projects.settings": "Настройки проекта",
      "projects.settings_access": "Доступ",
      "projects.settings_board": "Доска",
      "projects.settings_danger": "Опасная зона",
      "projects.settings_project": "Проект",
      "projects.statuses": "Статусы доски",
      "projects.statuses_help": "На доске и в меню тикетов будут только выбранные статусы. Перед отключением статуса перенесите из него тикеты.",
      "projects.statuses_selected": "Статусы этого проекта",
      "projects.ticket_types_help": "Выбранные типы доступны при создании и редактировании тикетов. Перед отключением типа переведите существующие тикеты.",
      "projects.ticket_types_selected": "Типы тикетов этого проекта",
      "projects.title": "Проекты",
      "projects.tools": "Инструменты проекта",
      "sound.copy": "Короткие локальные звуки для событий доски. Для разных типов событий используются разные сигналы.",
      "sound.events_copy": "Новые тикеты, комментарии, назначения, смена статуса, смена спринта, Done/Closed и связи тикетов.",
      "sound.events_title": "Какие события звучат",
      "sound.focused": "Важное",
      "sound.off": "Выкл",
      "sound.soft": "Мягко",
      "sound.test": "Проверить звук",
      "sound.theme_bright": "Яркая",
      "sound.theme_round": "Мягкая",
      "sound.title": "Звуки на этом устройстве",
      "stats.assignees": "Исполнители",
      "stats.board_return": "К доске",
      "stats.closed": "Закрыто",
      "stats.closed_help": "Тикеты, которые сейчас в статусе «Закрыто».",
      "stats.done": "Готово",
      "stats.done_help": "Тикеты, которые сейчас в статусе «Готово».",
      "stats.empty": "Тут пока нет тикетов.",
      "stats.flow": "Поток",
      "stats.more_tickets": "еще",
      "stats.open": "Открыто",
      "stats.open_help": "Тикеты, которые еще не в «Готово» или «Закрыто».",
      "stats.open_points": "Открытые SP",
      "stats.open_points_help": "Сторипоинты в открытых тикетах.",
      "stats.people": "Люди",
      "stats.points": "Сторипоинты",
      "stats.priorities": "Приоритеты",
      "stats.assignees_help": "Работа, которая сейчас назначена каждому человеку.",
      "stats.priorities_help": "Количество тикетов и сторипоинтов по приоритетам.",
      "stats.shape": "Структура",
      "stats.sprints": "Спринты",
      "stats.sprints_help": "Тикеты и сторипоинты, запланированные по спринтам.",
      "stats.statuses": "Статусы",
      "stats.statuses_help": "Распределение тикетов и сторипоинтов по статусам доски.",
      "stats.status_bar_help": "Верхняя строка сравнивает число тикетов с самым загруженным статусом; нижняя — сторипоинты с общим объёмом проекта.",
      "stats.ticket_count": "Тикеты",
      "stats.timeline": "План",
      "stats.title": "Статистика",
      "stats.total": "Всего тикетов",
      "stats.total_help": "Все тикеты в этом проекте.",
      "stats.types": "Типы",
      "stats.types_help": "Как работа распределена между задачами, эпиками, багами и историями.",
      "stats.visibility": "Видимость статистики",
      "stats.visibility_admin": "Только админы проекта",
      "stats.visibility_all": "Все участники проекта",
      "stats.visibility_help": "По умолчанию статистику проекта видят все участники.",
      "stats.visibility_member": "Участники и админы",
      "stats.visibility_viewer": "Наблюдатели, участники и админы",
      "stats.workload": "Нагрузка",
      "sprint.activate": "Активировать",
      "sprint.active": "Активные спринты",
      "sprint.active_short": "Активный",
      "sprint.all": "Все спринты",
      "sprint.backlog": "Без спринта",
      "sprint.close": "Закрыть",
      "sprint.closed": "Закрыт",
      "sprint.create": "Создать спринт",
      "sprint.empty": "Спринтов пока нет.",
      "sprint.ends_on": "Конец",
      "sprint.filter_modes": "Режимы",
      "sprint.find_placeholder": "Найти спринт",
      "sprint.find_or_create_placeholder": "Найти или назвать спринт",
      "sprint.goal": "Цель",
      "sprint.goal_placeholder": "Что должен дать этот спринт?",
      "sprint.manage": "Планирование спринтов",
      "sprint.manage_copy": "Планируйте, запускайте, закрывайте и переоткрывайте спринты проекта.",
      "sprint.manage_link": "Управлять спринтами",
      "sprint.new": "Новый спринт",
      "sprint.no_matches": "Спринты не найдены",
      "sprint.none": "Без спринта",
      "sprint.open_sprints": "Спринты",
      "sprint.planned": "План",
      "sprint.quick_create": "Создать спринт",
      "sprint.quick_create_placeholder": "Название нового спринта",
      "sprint.quick_create_help": "Создайте спринт, не уходя с доски. Даты можно не указывать.",
      "sprint.recent_closed": "Недавно закрытые",
      "sprint.reopen": "Переоткрыть",
      "sprint.save": "Сохранить спринт",
      "sprint.selected_archive": "Выбранный архив",
      "sprint.existing": "Текущие спринты",
      "sprint.sprints": "Спринты",
      "sprint.starts_on": "Начало",
      "sprint.status": "Статус",
      "sprint.ticket_count": "тикетов",
      "sprint.ticket_count_short": "т",
      "sprint.days_left": "дн. осталось",
      "sprint.ended": "завершился",
      "sprint.ends_today": "закончится сегодня",
      "sprint.total_days": "дней спринта",
      "status.all": "Все",
      "story_points.none": "Без SP",
      "story_points.short": "SP",
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
      "ticket.action.ticket_deleted": "удалил тикет",
      "ticket.action.ticket_updated": "обновил тикет",
      "ticket.action.type_changed": "изменил тип",
      "ticket.action.unlinked": "удалил связь",
      "ticket.action.unwatching": "перестал наблюдать",
      "ticket.action.watching": "начал наблюдать",
      "ticket.autosave_error": "Не удалось сохранить",
      "ticket.autosave_saved": "Сохранено",
      "ticket.autosave_saving": "Сохраняю...",
      "ticket.comments": "Комментарии",
      "ticket.delete": "Удалить тикет",
      "ticket.delete_confirm": "Введите ключ тикета для подтверждения:",
      "ticket.delete_help": "Удаление тикета безвозвратно удалит его комментарии, связи, наблюдателей и историю. Отменить нельзя.",
      "ticket.delete_own_only": "Не-админы удаляют только свои тикеты",
      "ticket.delete_own_only_help": "На админов проекта это ограничение не распространяется.",
      "ticket.delete_policy": "Удаление тикетов",
      "ticket.delete_policy_admin": "Только админы проекта",
      "ticket.delete_policy_help": "Удаление видно только на странице тикета тем, кому это разрешено настройкой проекта.",
      "ticket.delete_policy_member": "Админы и участники",
      "ticket.delete_policy_role_help": "Выберите минимальную роль проекта, которой можно удалять тикеты.",
      "ticket.delete_policy_viewer": "Все с доступом к проекту",
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
    setupSprintOptionLabels();
    setupActionLabels();
    setupActionDetails();
    setupSprintProgress();
    updateSprintFilterLabels();
    refreshColumnCounts();
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

  function statusDotClass(status) {
    return `status-${String(status || "Backlog").toLowerCase().replace(/\s+/g, "-")}-dot`;
  }

  function priorityIcon(priority) {
    return {
      Low: "arrow-down",
      Medium: "minus",
      High: "arrow-up",
      Urgent: "flame",
    }[priority] || "minus";
  }

  function priorityClass(priority) {
    return `priority-${String(priority || "Medium").toLowerCase()}-icon`;
  }

  let audioContext = null;
  const mentionState = new WeakMap();

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
    if (action === "sprint_changed") return "sprint";
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
    } else if (bright && kind === "sprint") {
      playTone(ctx, now, 587.33, 0.045, volume * 0.65, "triangle");
      playTone(ctx, now + 0.06, 440, 0.055, volume * 0.5, "sine");
      playTone(ctx, now + 0.115, 587.33, 0.065, volume * 0.45, "triangle");
    } else if (kind === "sprint") {
      playTone(ctx, now, 349.23, 0.07, volume * 0.55, "sine");
      playTone(ctx, now + 0.075, 523.25, 0.1, volume * 0.5, "triangle");
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

  function setBoardData(key, value) {
    const board = document.querySelector(".board");
    if (!board) return;
    board.dataset[key] = JSON.stringify(value);
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
    } else if (field === "story_points") {
      buildStoryPointsPopover(pop, card, chip);
    } else {
      buildOptionsPopover(pop, field, card, chip);
    }
    document.body.appendChild(pop);
    renderIcons();
    window.requestAnimationFrame(renderIcons);
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
    if (activePopover) {
      if (typeof activePopover._beforeClose === "function") activePopover._beforeClose();
      activePopover.remove();
    }
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
    if (event.target.closest(".mention-menu")) return;
    if (activePopover && !activePopover.contains(event.target) && event.target !== activeChip && !activeChip.contains(event.target)) {
      closePopover();
    }
  }

  function onPopoverKey(event) {
    if (event.key === "Escape") closePopover();
  }

  function positionPopover(pop, chip) {
    const rect = chip.getBoundingClientRect();
    const margin = 8;
    pop.style.position = "fixed";
    pop.style.maxWidth = `${Math.max(240, window.innerWidth - margin * 2)}px`;
    pop.style.maxHeight = `${Math.max(220, window.innerHeight - margin * 2)}px`;
    pop.style.overflow = "auto";
    pop.style.top = `${rect.bottom + 6}px`;
    let left = rect.left;
    const width = pop.offsetWidth;
    if (left + width > window.innerWidth - margin) left = window.innerWidth - margin - width;
    if (left < margin) left = margin;
    pop.style.left = `${left}px`;
    const height = pop.offsetHeight;
    const belowTop = rect.bottom + 6;
    const aboveTop = rect.top - 6 - height;
    if (belowTop + height > window.innerHeight - margin && aboveTop >= margin) {
      pop.style.top = `${aboveTop}px`;
    } else {
      pop.style.top = `${Math.min(belowTop, window.innerHeight - margin - Math.min(height, window.innerHeight - margin * 2))}px`;
    }
  }

  function buildOptionsPopover(pop, field, card, chip) {
    const current = chip.dataset.value || "";
    let options = [];
    if (field === "status") {
      options = boardData("statuses", []).map((s) => ({
        value: s,
        label: translate(`status.${s}`, currentLang()) || s,
        statusDot: true,
      }));
    } else if (field === "ticket_type") {
      options = boardData("ticketTypes", []).map((t) => ({
        value: t,
        label: translate(`type.${t}`, currentLang()) || t,
        icon: ticketTypeIcon(t),
      }));
    } else if (field === "priority") {
      options = boardData("priorities", []).map((p) => ({
        value: p,
        label: translate(`priority.${p}`, currentLang()) || p,
        icon: priorityIcon(p),
        priorityIcon: true,
      }));
    } else if (field === "sprint_id") {
      pop.classList.add("popover-sprint-options");
      options = [{ value: "", label: translate("sprint.none", currentLang()) || "No sprint" }];
      boardData("sprints", [])
        .filter((s) => s.status !== "closed")
        .forEach((s) => options.push({
          value: String(s.id),
          label: s.name,
          meta: sprintMenuMeta(s),
          title: sprintDisplayLabel(s),
          ticket_count: Number(s.ticket_count || 0),
          status: s.status,
        }));
    } else if (field === "assignee_id") {
      options = [{ value: "", label: translate("ticket.unassigned", currentLang()) || "Unassigned" }];
      boardData("members", []).forEach((m) => options.push({
        value: String(m.id),
        label: m.name || m.login,
        login: m.login || "",
        avatar_url: m.avatar_url || "",
      }));
    }
    options.forEach((opt) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "popover-option";
      if (opt.title) button.title = opt.title;
      if (field === "sprint_id") {
        button.classList.add("popover-sprint-option");
        if (Number(opt.ticket_count || 0) > 0) button.classList.add("is-filled");
      }
      if (String(opt.value) === String(current)) button.classList.add("is-current");
      if (opt.statusDot) {
        const dot = document.createElement("span");
        dot.className = `status-dot ${statusDotClass(opt.value)}`;
        dot.setAttribute("aria-hidden", "true");
        button.appendChild(dot);
      } else if (opt.icon) {
        const icon = document.createElement("span");
        icon.className = opt.priorityIcon
          ? `priority-icon ${priorityClass(opt.value)}`
          : `type-icon ${ticketTypeClass(opt.value)}`;
        icon.dataset.icon = opt.icon;
        icon.setAttribute("aria-hidden", "true");
        button.appendChild(icon);
      } else if (field === "assignee_id") {
        const avatar = document.createElement("span");
        avatar.className = "avatar-dot";
        avatar.setAttribute("aria-hidden", "true");
        renderAvatar(avatar, opt.avatar_url || "", opt.login || "");
        button.appendChild(avatar);
      }
      const label = document.createElement("span");
      label.className = "popover-option-label";
      label.textContent = opt.label;
      button.appendChild(label);
      if (opt.meta || opt.status === "active") {
        const meta = document.createElement("span");
        meta.className = "popover-option-meta";
        meta.textContent = opt.meta || "";
        if (opt.status === "active") {
          const badge = document.createElement("span");
          badge.className = "popover-option-badge";
          badge.textContent = translate("sprint.active_short", currentLang()) || "Active";
          meta.appendChild(badge);
        }
        button.appendChild(meta);
      }
      button.addEventListener("click", () => applyFieldChange(card, field, opt.value));
      pop.appendChild(button);
    });
  }

  async function applyFieldChange(card, field, value) {
    const payload = {};
    if (field === "assignee_id" || field === "sprint_id") {
      payload[field] = value ? Number(value) : null;
    } else if (field === "story_points") {
      payload[field] = Number(value || 0);
    } else {
      payload[field] = value;
    }
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
    const projectKey = document.querySelector(".board")?.dataset.projectKey || "";
    textarea.dataset.mentionInput = "true";
    textarea.dataset.mentionProject = projectKey;
    pop.appendChild(textarea);
    let submitted = false;
    const submit = async () => {
      if (submitted) return;
      const body = textarea.value.trim();
      if (!body) return;
      submitted = true;
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
        flashSaved(card);
      } catch (error) {
        window.alert(error.message || "Could not add comment");
        textarea.disabled = false;
        submitted = false;
      } finally {
        card.classList.remove("is-saving");
      }
    };
    pop._beforeClose = submit;
    textarea.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        submit();
        closePopover();
      }
    });
    setupMentionInput(textarea);
  }

  function buildStoryPointsPopover(pop, card, chip) {
    pop.classList.add("popover-points");
    const label = document.createElement("label");
    label.className = "popover-field-label";
    label.textContent = translate("field.story_points", currentLang()) || "Story points";
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.max = "999";
    input.step = "1";
    input.inputMode = "numeric";
    input.value = chip.dataset.value || "0";
    label.appendChild(input);
    pop.appendChild(label);
    let submitted = false;
    const submit = () => {
      if (submitted) return;
      submitted = true;
      const next = Math.max(0, Math.min(999, Number.parseInt(input.value || "0", 10) || 0));
      applyFieldChange(card, "story_points", next);
    };
    input.addEventListener("change", submit);
    input.addEventListener("blur", submit, { once: true });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        input.blur();
      }
    });
  }

  function buildDescriptionPopover(pop, card) {
    pop.classList.add("popover-desc");
    const textarea = document.createElement("textarea");
    textarea.rows = 6;
    textarea.value = card.dataset.description || "";
    textarea.placeholder = translate("help.ticket_description", currentLang()) || "Description";
    const projectKey = document.querySelector(".board")?.dataset.projectKey || "";
    textarea.dataset.mentionInput = "true";
    textarea.dataset.mentionProject = projectKey;
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
    setupMentionInput(textarea);
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
    setChipValue(card, "story_points", ticket.story_points || 0, storyPointsLabel(ticket.story_points));
    setChipValue(card, "sprint_id", ticket.sprint_id ? String(ticket.sprint_id) : "", ticket.sprint_name || translate("sprint.none", currentLang()) || "No sprint");
    updateAssigneeChip(card, ticket);
    updateLinkedTickets(card, ticket);
    updateSprintProgress(card, ticket);
    refreshColumnCounts();
    renderIcons();
  }

  function setChipValue(card, field, value, label) {
    const chip = card.querySelector(`.chip-edit[data-edit="${field}"]`);
    if (!chip) return;
    chip.dataset.value = value || "";
    chip.title = label || "";
    const labelEl = chip.querySelector(".chip-label");
    if (labelEl) {
      if (field === "status") labelEl.dataset.i18n = `status.${value}`;
      if (field === "priority") labelEl.dataset.i18n = `priority.${value}`;
      if (field === "ticket_type") labelEl.dataset.i18n = `type.${value}`;
      if (field === "sprint_id" && !value) labelEl.dataset.i18n = "sprint.none";
      if (field === "sprint_id" && value) labelEl.removeAttribute("data-i18n");
      if (field === "story_points" && Number(value || 0) <= 0) labelEl.dataset.i18n = "story_points.none";
      if (field === "story_points" && Number(value || 0) > 0) labelEl.removeAttribute("data-i18n");
      labelEl.textContent = label;
    }
    if (field === "priority") {
      chip.className = chip.className
        .split(/\s+/)
        .filter((name) => name && !name.startsWith("priority-chip-"))
        .join(" ");
      chip.classList.add(`priority-chip-${String(value).toLowerCase()}`);
      const icon = chip.querySelector("[data-priority-icon]");
      if (icon) {
        icon.className = `priority-icon ${priorityClass(value)}`;
        icon.dataset.icon = priorityIcon(value);
      }
    }
    if (field === "ticket_type") {
      const icon = chip.querySelector(".type-icon");
      if (icon) {
        icon.className = `type-icon ${ticketTypeClass(value)}`;
        icon.dataset.icon = ticketTypeIcon(value);
      }
    }
    if (field === "status") {
      const dot = chip.querySelector("[data-status-dot]");
      if (dot) {
        dot.className = `status-dot ${statusDotClass(value)}`;
      }
    }
  }

  function storyPointsLabel(value) {
    const points = Number(value || 0);
    return points > 0 ? `${points} SP` : translate("story_points.none", currentLang()) || "No SP";
  }

  function parseDateOnly(value) {
    if (!value) return null;
    const parts = String(value).split("-").map((part) => Number.parseInt(part, 10));
    if (parts.length !== 3 || parts.some(Number.isNaN)) return null;
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }

  function formatDateOnly(value) {
    const date = parseDateOnly(value);
    if (!date) return "";
    const enMonths = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const ruMonths = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
    const months = currentLang() === "ru" ? ruMonths : enMonths;
    return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
  }

  function dateDiffDays(from, to) {
    const oneDay = 24 * 60 * 60 * 1000;
    const start = new Date(from.getFullYear(), from.getMonth(), from.getDate());
    const end = new Date(to.getFullYear(), to.getMonth(), to.getDate());
    return Math.round((end - start) / oneDay);
  }

  function updateSprintProgress(card, ticket = {}) {
    const progress = card.querySelector(".ticket-card-sprint-progress");
    if (!progress) return;
    if (Object.prototype.hasOwnProperty.call(ticket, "sprint_starts_on")) progress.dataset.sprintStart = ticket.sprint_starts_on || "";
    if (Object.prototype.hasOwnProperty.call(ticket, "sprint_ends_on")) progress.dataset.sprintEnd = ticket.sprint_ends_on || "";
    if (Object.prototype.hasOwnProperty.call(ticket, "sprint_status")) progress.dataset.sprintStatus = ticket.sprint_status || "";
    const start = parseDateOnly(progress.dataset.sprintStart);
    const end = parseDateOnly(progress.dataset.sprintEnd);
    if (!start || !end) {
      progress.hidden = true;
      progress.textContent = "";
      return;
    }
    const today = new Date();
    const total = Math.max(1, dateDiffDays(start, end) + 1);
    const elapsed = Math.min(total, Math.max(0, dateDiffDays(start, today) + 1));
    const dotCount = total <= 14 ? total : 14;
    const filled = Math.max(1, Math.min(dotCount, Math.ceil((elapsed / total) * dotCount)));
    const left = dateDiffDays(today, end);
    let label = `${left} ${translate("sprint.days_left", currentLang()) || "days left"}`;
    if (left === 0) label = translate("sprint.ends_today", currentLang()) || "ends today";
    if (left < 0) label = translate("sprint.ended", currentLang()) || "ended";
    progress.hidden = false;
    progress.title = `${formatDateOnly(progress.dataset.sprintStart)} - ${formatDateOnly(progress.dataset.sprintEnd)} · ${total} ${translate("sprint.total_days", currentLang()) || "sprint days"} · ${label}`;
    progress.innerHTML = "";
    const dots = document.createElement("span");
    dots.className = "sprint-progress-dots";
    for (let index = 0; index < dotCount; index += 1) {
      const dot = document.createElement("span");
      dot.className = "sprint-progress-dot";
      if (index < filled) dot.classList.add("is-filled");
      if (left < 0) dot.classList.add("is-ended");
      dots.appendChild(dot);
    }
    const text = document.createElement("span");
    text.className = "sprint-progress-label";
    text.textContent = `${translate("field.sprint", currentLang()) || "Sprint"} · ${label}`;
    progress.append(dots, text);
  }

  function setupSprintProgress() {
    document.querySelectorAll(".ticket-card").forEach((card) => updateSprintProgress(card));
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
    chip.title = ticket.assignee_name || ticket.assignee_login || translate("ticket.unassigned", currentLang()) || "Unassigned";
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
    links.title = linked
      .slice(0, 5)
      .map((item) => `${item.other_key}${item.other_title ? ` · ${item.other_title}` : ""}`)
      .join("; ");
    if (linked.length > 5) {
      const more = currentLang() === "ru" ? `ещё ${linked.length - 5}` : `+${linked.length - 5} more`;
      links.title = `${links.title}; ${more}`;
    }
    if (!linked.length) return;
    const icon = document.createElement("span");
    icon.className = "ticket-links-icon";
    icon.dataset.icon = "link";
    icon.setAttribute("aria-hidden", "true");
    links.appendChild(icon);
    linked.slice(0, 2).forEach((item) => {
      const pill = document.createElement("a");
      pill.className = "linked-ticket-pill";
      pill.href = `/t/${item.other_key}`;
      pill.textContent = item.other_key;
      if (item.other_title) pill.title = item.other_title;
      links.appendChild(pill);
    });
    if (linked.length > 2) {
      const more = document.createElement("span");
      more.className = "linked-ticket-more";
      more.textContent = `+${linked.length - 2}`;
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
      const counter = column.querySelector(".column-count");
      if (counter) counter.textContent = column.querySelectorAll(".ticket-card").length;
      const points = Array.from(column.querySelectorAll('.ticket-card .chip-edit[data-edit="story_points"]'))
        .reduce((sum, chip) => sum + (Number.parseInt(chip.dataset.value || "0", 10) || 0), 0);
      const pointsEl = column.querySelector("[data-column-points]");
      if (pointsEl) pointsEl.textContent = String(points);
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
        <button type="button" class="chip chip-edit chip-type tooltip-anchor" data-edit="ticket_type" aria-haspopup="true" data-i18n-tooltip="help.ticket_type" data-tooltip="Type of work. Epics are bigger containers; tasks, bugs, and stories are regular tickets.">
          <span class="type-icon" aria-hidden="true"></span>
          <span class="chip-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-status tooltip-anchor" data-edit="status" aria-haspopup="true" data-i18n-tooltip="help.status" data-tooltip="Where the ticket currently is on the board.">
          <span class="status-dot" data-status-dot aria-hidden="true"></span>
          <span class="chip-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-priority tooltip-anchor" data-edit="priority" aria-haspopup="true" data-i18n-tooltip="help.priority" data-tooltip="Defaults to Medium. Use Urgent only for work that blocks people now.">
          <span class="priority-icon" data-priority-icon aria-hidden="true"></span>
          <span class="chip-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-story-points tooltip-anchor" data-edit="story_points" aria-haspopup="true" data-i18n-tooltip="help.story_points" data-tooltip="Small effort estimate. Use 0 when not estimated.">
          <span class="story-points-icon" data-icon="gauge" aria-hidden="true"></span>
          <span class="chip-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-sprint tooltip-anchor" data-edit="sprint_id" aria-haspopup="true" data-i18n-tooltip="help.sprint" data-tooltip="Sprint or iteration this ticket is planned in.">
          <span class="chip-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-assignee tooltip-anchor" data-edit="assignee_id" aria-haspopup="true" data-i18n-tooltip="help.assignee" data-tooltip="Person responsible for the next action. They will receive notifications if enabled.">
          <span class="avatar-dot" aria-hidden="true"></span>
          <span class="chip-label assignee-label"></span>
        </button>
        <button type="button" class="chip chip-edit chip-desc tooltip-anchor" data-edit="description" data-icon="square-pen" aria-haspopup="true" aria-label="Edit description" data-i18n-aria="field.description" data-i18n-tooltip="field.description" data-tooltip="Description"></button>
        <button type="button" class="chip chip-edit chip-comment tooltip-anchor" data-edit="comment" data-icon="message-square-plus" aria-haspopup="true" aria-label="Comment" data-i18n-aria="action.comment" data-i18n-tooltip="action.comment" data-tooltip="Comment"></button>
      </div>
      <div class="ticket-card-sprint-progress" hidden></div>
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
        if (payload.event === "ticket_deleted") {
          const key = payload.ticket_key || payload.ticket?.key;
          const card = key ? document.querySelector(`.ticket-card[data-ticket-key="${cssEscape(key)}"]`) : null;
          if (card) {
            card.remove();
            refreshColumnCounts();
          }
          const ticketPage = document.querySelector("[data-ticket-page]");
          if (ticketPage && ticketPage.dataset.ticketKey === key) {
            const projectKey = ticketPage.dataset.projectKey || "";
            window.location.href = `/p/${encodeURIComponent(projectKey)}/board`;
          }
          return;
        }
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
    source.addEventListener("ticket_deleted", handleTicketEvent);
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
    const fields = ["title", "description", "ticket_type", "status", "priority", "story_points", "assignee_id", "sprint_id"];
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
      if (field === "story_points") return Math.max(0, Math.min(999, Number.parseInt(control.value || "0", 10) || 0));
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

  function setupProjectSettingsAutosave() {
    document.querySelectorAll("[data-project-settings-root]").forEach((root) => {
      const projectKey = root.dataset.projectKey;
      const forms = root.querySelectorAll("[data-project-details-form], [data-board-settings-form]");
      if (!projectKey || !forms.length) return;
      let timer = null;

      const setStatus = (key) => {
        root.querySelectorAll("[data-autosave-status]").forEach((status) => {
          status.dataset.i18n = key;
          status.textContent = translate(key, currentLang()) || status.textContent;
          status.dataset.state = key.endsWith("error") ? "error" : key.endsWith("saving") ? "saving" : "saved";
        });
      };

      const settingsFormData = () => {
        const details = root.querySelector("[data-project-details-form]");
        const board = root.querySelector("[data-board-settings-form]");
        if (!details || !board) return null;
        const name = details.elements.name?.value || "";
        if (!name.trim()) return null;
        const csrf = details.elements.csrf_token?.value || board.elements.csrf_token?.value || "";
        const data = new FormData();
        data.append("csrf_token", csrf);
        data.append("name", name);
        data.append("description", details.elements.description?.value || "");
        data.append("repo", details.elements.repo?.value || "");
        board.querySelectorAll('input[name="statuses"]:checked').forEach((input) => {
          data.append("statuses", input.value);
        });
        board.querySelectorAll('input[name="ticket_types"]:checked').forEach((input) => {
          data.append("ticket_types", input.value);
        });
        const statsVisibility = board.querySelector('input[name="stats_visibility"]:checked');
        data.append("stats_visibility", statsVisibility?.value || "viewer");
        const ticketDeletePolicy = board.querySelector('input[name="ticket_delete_policy"]:checked');
        data.append("ticket_delete_policy", ticketDeletePolicy?.value || "admin");
        const ticketDeleteOwnOnly = board.querySelector('input[name="ticket_delete_own_only"]:checked');
        data.append("ticket_delete_own_only", ticketDeleteOwnOnly ? "1" : "0");
        return data;
      };

      const saveNow = async () => {
        const data = settingsFormData();
        if (!data) {
          setStatus("ticket.autosave_error");
          return;
        }
        setStatus("ticket.autosave_saving");
        try {
          const response = await fetch(`/api/projects/${encodeURIComponent(projectKey)}/settings`, {
            method: "POST",
            body: data,
            headers: { "x-csrf-token": data.get("csrf_token") || "" },
          });
          if (!response.ok) throw new Error("settings save failed");
          setStatus("ticket.autosave_saved");
        } catch (error) {
          setStatus("ticket.autosave_error");
        }
      };

      const saveSoon = (delay) => {
        window.clearTimeout(timer);
        timer = window.setTimeout(saveNow, delay);
      };

      forms.forEach((form) => {
        form.addEventListener("submit", (event) => {
          event.preventDefault();
          saveSoon(0);
        });
        form.querySelectorAll("input, textarea, select").forEach((control) => {
          if (control.type === "hidden") return;
          if (control.type === "checkbox" || control.type === "radio" || control.tagName === "SELECT") {
            control.addEventListener("change", () => saveSoon(0));
          } else {
            control.addEventListener("input", () => saveSoon(650));
            control.addEventListener("blur", () => saveSoon(0));
          }
        });
      });
    });
  }

  function setupTypePickers() {
    document.querySelectorAll("[data-type-picker], [data-priority-picker]").forEach((picker) => {
      const isPriority = picker.hasAttribute("data-priority-picker");
      const fieldName = isPriority ? "priority" : "ticket_type";
      const field = picker.parentElement ? picker.parentElement.querySelector(`input[name="${fieldName}"]`) : null;
      const toggle = picker.querySelector(isPriority ? "[data-priority-toggle]" : "[data-type-toggle]");
      const menu = picker.querySelector(".type-picker-menu");
      const selectedIcon = picker.querySelector(isPriority ? "[data-selected-priority-icon]" : "[data-selected-type-icon]");
      const selectedLabel = picker.querySelector(isPriority ? "[data-selected-priority-label]" : "[data-selected-type-label]");
      const valueAttr = isPriority ? "priorityValue" : "typeValue";
      const valueSelector = isPriority ? "[data-priority-value]" : "[data-type-value]";
      const choiceSelector = isPriority ? ".priority-choice" : ".type-choice";
      if (!field) return;
      const update = (value, notify = false) => {
        field.value = value;
        picker.querySelectorAll(valueSelector).forEach((button) => {
          const selected = button.dataset[valueAttr] === value;
          button.classList.toggle("is-selected", selected);
          button.setAttribute("aria-selected", selected ? "true" : "false");
        });
        if (selectedIcon) {
          selectedIcon.className = isPriority
            ? `priority-icon ${priorityClass(value)}`
            : `type-icon ${ticketTypeClass(value)}`;
          selectedIcon.dataset.icon = isPriority ? priorityIcon(value) : ticketTypeIcon(value);
        }
        if (selectedLabel) {
          const key = isPriority ? `priority.${value}` : `type.${value}`;
          selectedLabel.dataset.i18n = key;
          selectedLabel.textContent = translate(key, currentLang()) || value;
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
          const current = menu && menu.querySelector(`${choiceSelector}.is-selected`);
          if (current) current.focus();
        });
      }
      picker.querySelectorAll(valueSelector).forEach((button) => {
        button.addEventListener("click", () => {
          update(button.dataset[valueAttr] || (isPriority ? "Medium" : "Task"), true);
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
      update(field.value || (isPriority ? "Medium" : "Task"));
    });
    document.addEventListener("click", (event) => {
      document.querySelectorAll("[data-type-picker].is-open, [data-priority-picker].is-open").forEach((picker) => {
        if (picker.contains(event.target)) return;
        picker.classList.remove("is-open");
        const toggle = picker.querySelector("[data-type-toggle], [data-priority-toggle]");
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

  function activeMentionQuery(input) {
    const cursor = input.selectionStart || 0;
    const before = input.value.slice(0, cursor);
    const match = before.match(/(?:^|[\s(])@([A-Za-z0-9-]{0,39})$/);
    if (!match) return null;
    const query = match[1] || "";
    return {
      query,
      start: cursor - query.length - 1,
      end: cursor,
    };
  }

  function closeMentionMenu(input) {
    const state = mentionState.get(input);
    if (!state) return;
    state.menu.remove();
    mentionState.delete(input);
  }

  function positionMentionMenu(input, menu) {
    const rect = input.getBoundingClientRect();
    menu.style.position = "fixed";
    menu.style.left = `${Math.max(8, Math.min(rect.left, window.innerWidth - menu.offsetWidth - 8))}px`;
    const bottomTop = rect.bottom + 6;
    const top = bottomTop + menu.offsetHeight > window.innerHeight - 8
      ? Math.max(8, rect.top - menu.offsetHeight - 6)
      : bottomTop;
    menu.style.top = `${top}px`;
    menu.style.width = `${Math.min(rect.width, window.innerWidth - 16)}px`;
  }

  function selectMention(input, user) {
    const state = mentionState.get(input);
    if (!state || !state.range) return;
    const before = input.value.slice(0, state.range.start);
    const after = input.value.slice(state.range.end);
    const mention = `@${user.login} `;
    input.value = `${before}${mention}${after}`;
    const cursor = before.length + mention.length;
    input.setSelectionRange(cursor, cursor);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    closeMentionMenu(input);
    input.focus();
  }

  function renderMentionMenu(input, users, range) {
    closeMentionMenu(input);
    if (!users.length) return;
    const menu = document.createElement("div");
    menu.className = "mention-menu";
    menu.setAttribute("role", "listbox");
    users.forEach((user, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "mention-option";
      if (index === 0) button.classList.add("is-active");
      button.dataset.userId = user.id;
      const avatar = document.createElement("span");
      avatar.className = "avatar-dot";
      avatar.setAttribute("aria-hidden", "true");
      renderAvatar(avatar, user.avatar_url || "", user.login || "");
      const text = document.createElement("span");
      text.className = "mention-option-text";
      const name = document.createElement("strong");
      name.textContent = user.name || user.login;
      const login = document.createElement("small");
      login.textContent = `@${user.login}`;
      text.append(name, login);
      button.append(avatar, text);
      button.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        selectMention(input, user);
      });
      menu.appendChild(button);
    });
    document.body.appendChild(menu);
    mentionState.set(input, { menu, users, range });
    positionMentionMenu(input, menu);
  }

  function setupMentionInput(input) {
    if (!input || input.dataset.mentionReady === "true") return;
    input.dataset.mentionReady = "true";
    let timer = null;
    let controller = null;

    const search = async () => {
      const range = activeMentionQuery(input);
      if (!range || !input.dataset.mentionProject) {
        closeMentionMenu(input);
        return;
      }
      if (controller) controller.abort();
      controller = new AbortController();
      const url = new URL(`/api/projects/${encodeURIComponent(input.dataset.mentionProject)}/users/search`, window.location.origin);
      url.searchParams.set("q", range.query);
      try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error("mention search failed");
        const data = await response.json();
        renderMentionMenu(input, Array.isArray(data.users) ? data.users : [], range);
      } catch (error) {
        if (error.name !== "AbortError") closeMentionMenu(input);
      }
    };

    input.addEventListener("input", () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(search, 120);
    });
    input.addEventListener("click", search);
    input.addEventListener("blur", () => window.setTimeout(() => closeMentionMenu(input), 120));
    input.addEventListener("keydown", (event) => {
      const state = mentionState.get(input);
      if (!state) return;
      const options = Array.from(state.menu.querySelectorAll(".mention-option"));
      const currentIndex = Math.max(0, options.findIndex((option) => option.classList.contains("is-active")));
      if (event.key === "Escape") {
        closeMentionMenu(input);
        return;
      }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        const nextIndex = event.key === "ArrowDown"
          ? Math.min(options.length - 1, currentIndex + 1)
          : Math.max(0, currentIndex - 1);
        options.forEach((option, index) => option.classList.toggle("is-active", index === nextIndex));
      }
      if (event.key === "Enter" && options.length) {
        event.preventDefault();
        const active = options.find((option) => option.classList.contains("is-active")) || options[0];
        const user = state.users.find((item) => String(item.id) === active.dataset.userId);
        if (user) selectMention(input, user);
      }
    });
  }

  function setupMentionInputs(root = document) {
    root.querySelectorAll("[data-mention-input]").forEach((input) => setupMentionInput(input));
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

  function sprintDateRangeLabel(startValue, endValue) {
    const start = formatDateOnly(startValue);
    const end = formatDateOnly(endValue);
    if (start && end) return `${start} - ${end}`;
    if (start) return start;
    return end;
  }

  function compactDateOnly(value, includeYear = false) {
    const date = parseDateOnly(value);
    if (!date) return "";
    const enMonths = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const ruMonths = ["янв.", "фев.", "мар.", "апр.", "май", "июн.", "июл.", "авг.", "сен.", "окт.", "ноя.", "дек."];
    const months = currentLang() === "ru" ? ruMonths : enMonths;
    return `${date.getDate()} ${months[date.getMonth()]}${includeYear ? ` ${date.getFullYear()}` : ""}`;
  }

  function compactSprintDateRangeLabel(startValue, endValue) {
    const start = parseDateOnly(startValue);
    const end = parseDateOnly(endValue);
    if (!start && !end) return "";
    if (start && end) {
      const sameYear = start.getFullYear() === end.getFullYear();
      const sameMonth = sameYear && start.getMonth() === end.getMonth();
      if (sameMonth) {
        const endLabel = compactDateOnly(endValue, true);
        return `${start.getDate()}-${endLabel}`;
      }
      return `${compactDateOnly(startValue, !sameYear)}-${compactDateOnly(endValue, true)}`;
    }
    return compactDateOnly(startValue || endValue, true);
  }

  function sprintShortLabel(sprint) {
    return sprint?.name || "";
  }

  function sprintDisplayLabel(sprint) {
    const name = sprint?.name || "";
    const range = sprintDateRangeLabel(sprint?.starts_on, sprint?.ends_on);
    return range ? `${name} · ${range}` : name;
  }

  function sprintMenuMeta(sprint) {
    const parts = [];
    const range = compactSprintDateRangeLabel(sprint?.starts_on, sprint?.ends_on);
    if (range) parts.push(range);
    const count = Number(sprint?.ticket_count || 0);
    if (count > 0) parts.push(`${count} ${translate("sprint.ticket_count_short", currentLang()) || "t"}`);
    return parts.join(" · ");
  }

  function setupSprintOptionLabels() {
    document.querySelectorAll("[data-sprint-option]").forEach((option) => {
      const name = option.dataset.sprintName || option.textContent.trim();
      const range = sprintDateRangeLabel(option.dataset.sprintStart, option.dataset.sprintEnd);
      option.textContent = range ? `${name} · ${range}` : name;
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

  function setupSprintFilter() {
    document.querySelectorAll("[data-sprint-filter-combo]").forEach((combo) => {
      const toggle = combo.querySelector("[data-sprint-filter-toggle]");
      const menu = combo.querySelector("[data-sprint-filter-menu]");
      const search = combo.querySelector("[data-sprint-filter-search]");
      const createButton = combo.querySelector("[data-sprint-filter-create-toggle]");
      const createForm = combo.querySelector("[data-sprint-quick-create-form]");
      if (!toggle || !menu || !search) return;

      const close = () => {
        combo.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      };
      const open = () => {
        document.querySelectorAll("[data-sprint-filter-combo].is-open").forEach((other) => {
          if (other !== combo) other.classList.remove("is-open");
        });
        combo.classList.add("is-open");
        toggle.setAttribute("aria-expanded", "true");
        renderSprintFilterOptions(combo);
        window.setTimeout(() => search.focus(), 0);
      };

      updateSprintFilterCurrent(combo);
      renderSprintFilterOptions(combo);

      toggle.addEventListener("click", (event) => {
        event.preventDefault();
        if (combo.classList.contains("is-open")) {
          close();
        } else {
          open();
        }
      });
      const updateCreateButton = () => {
        if (createButton) createButton.disabled = !search.value.trim();
      };
      search.addEventListener("input", () => {
        renderSprintFilterOptions(combo);
        updateCreateButton();
      });
      search.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" || !createButton || createButton.disabled) return;
        event.preventDefault();
        createButton.click();
      });
      if (createButton) {
        updateCreateButton();
        createButton.addEventListener("click", (event) => {
          event.preventDefault();
          if (!createForm) return;
          const nameInput = createForm.querySelector('[name="name"]');
          if (nameInput && !nameInput.value.trim()) nameInput.value = search.value.trim();
          createForm.hidden = !createForm.hidden;
          if (!createForm.hidden) window.setTimeout(() => (nameInput || createForm.querySelector("input"))?.focus(), 0);
        });
      }
      if (createForm) {
        createForm.addEventListener("submit", async (event) => {
          event.preventDefault();
          const controls = Array.from(createForm.querySelectorAll("input, select, button")).concat([search, createButton].filter(Boolean));
          await createQuickSprint(combo.dataset.projectKey || "", new FormData(createForm), controls);
        });
      }
      combo.addEventListener("keydown", (event) => {
        if (event.key === "Escape") close();
      });
    });

    document.addEventListener("pointerdown", (event) => {
      if (event.target.closest("[data-sprint-filter-combo]")) return;
      document.querySelectorAll("[data-sprint-filter-combo].is-open").forEach((combo) => {
        combo.classList.remove("is-open");
        combo.querySelector("[data-sprint-filter-toggle]")?.setAttribute("aria-expanded", "false");
      });
    });
  }

  async function createQuickSprint(projectKey, formDataOrName, controls = []) {
    if (!projectKey) return;
    const formData = formDataOrName instanceof FormData ? formDataOrName : new FormData();
    if (!(formDataOrName instanceof FormData)) formData.append("name", String(formDataOrName || ""));
    const name = String(formData.get("name") || "").trim();
    if (!name) return;
    formData.set("name", name);
    if (!formData.get("status")) formData.set("status", "planned");
    controls.forEach((control) => {
      if (control) control.disabled = true;
    });
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectKey)}/sprints/quick`, {
        method: "POST",
        headers: { "x-csrf-token": csrfToken(), accept: "application/json" },
        body: formData,
      });
      if (!response.ok) throw new Error(await response.text());
      const sprint = await response.json();
      const sprints = boardData("sprints", []).filter((item) => String(item.id) !== String(sprint.id));
      setBoardData("sprints", [sprint, ...sprints]);
      window.location.href = sprintFilterUrl(projectKey, sprint.id);
    } catch (error) {
      window.alert(error.message || "Could not create sprint");
      controls.forEach((control) => {
        if (control) control.disabled = false;
      });
    }
  }

  function sprintFilterUrl(projectKey, value) {
    const url = new URL(`/p/${encodeURIComponent(projectKey)}/board`, window.location.origin);
    if (value) url.searchParams.set("sprint", value);
    return `${url.pathname}${url.search}`;
  }

  function sprintFilterServiceOptions() {
    return [
      { value: "", label: translate("sprint.all", currentLang()) || "All sprints" },
      { value: "none", label: translate("sprint.none", currentLang()) || "No sprint" },
      { value: "active", label: translate("sprint.active", currentLang()) || "Active sprints" },
    ];
  }

  function updateSprintFilterCurrent(combo) {
    const current = combo.dataset.currentSprintFilter || "";
    const target = combo.querySelector("[data-sprint-filter-current]");
    if (!target) return;
    const service = sprintFilterServiceOptions().find((option) => option.value === current);
    if (service) {
      target.textContent = service.label;
      target.removeAttribute("title");
      return;
    }
    const sprint = boardData("sprints", []).find((item) => String(item.id) === String(current));
    target.textContent = sprint ? sprintShortLabel(sprint) : current;
    if (sprint) target.title = sprintDisplayLabel(sprint);
  }

  function updateSprintFilterLabels() {
    setupSprintOptionLabels();
    document.querySelectorAll("[data-sprint-filter-combo]").forEach((combo) => {
      updateSprintFilterCurrent(combo);
      if (combo.classList.contains("is-open")) renderSprintFilterOptions(combo);
    });
  }

  function renderSprintFilterOptions(combo) {
    const list = combo.querySelector("[data-sprint-filter-options]");
    const search = combo.querySelector("[data-sprint-filter-search]");
    if (!list) return;
    const projectKey = combo.dataset.projectKey || "";
    const current = combo.dataset.currentSprintFilter || "";
    const query = (search?.value || "").trim().toLowerCase();
    const allSprints = boardData("sprints", []);
    list.innerHTML = "";

    const addGroup = (title, options) => {
      if (!options.length) return;
      const group = document.createElement("div");
      group.className = "sprint-filter-group";
      const heading = document.createElement("div");
      heading.className = "sprint-filter-group-title";
      heading.textContent = title;
      group.appendChild(heading);
      options.forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "sprint-filter-option";
        if (option.title) button.title = option.title;
        if (Number(option.ticket_count || 0) > 0) button.classList.add("is-filled");
        button.setAttribute("role", "option");
        if (String(option.value) === String(current)) {
          button.classList.add("is-current");
          button.setAttribute("aria-selected", "true");
        } else {
          button.setAttribute("aria-selected", "false");
        }
        const main = document.createElement("span");
        main.className = "sprint-filter-option-main";
        main.textContent = option.label;
        button.appendChild(main);
        if (option.status === "active") {
          button.classList.add("is-active-sprint");
          const badge = document.createElement("span");
          badge.className = "sprint-filter-status";
          badge.textContent = translate("sprint.active_short", currentLang()) || "Active";
          button.appendChild(badge);
        }
        if (option.meta) {
          const meta = document.createElement("span");
          meta.className = "sprint-filter-option-meta";
          meta.textContent = option.meta;
          button.appendChild(meta);
        }
        button.addEventListener("click", () => {
          window.location.href = sprintFilterUrl(projectKey, option.value);
        });
        group.appendChild(button);
      });
      list.appendChild(group);
    };

    if (!query) {
      addGroup(translate("sprint.filter_modes", currentLang()) || "Filter", sprintFilterServiceOptions());
      addGroup(
        translate("sprint.open_sprints", currentLang()) || "Open sprints",
        allSprints
          .filter((sprint) => sprint.status !== "closed")
          .map((sprint) => ({
            value: String(sprint.id),
            label: sprint.name,
            meta: sprintMenuMeta(sprint),
            title: sprintDisplayLabel(sprint),
            ticket_count: Number(sprint.ticket_count || 0),
            status: sprint.status,
          }))
      );
      const recentClosed = allSprints.filter((sprint) => sprint.status === "closed").slice(0, 6);
      addGroup(
        translate("sprint.recent_closed", currentLang()) || "Recent closed",
        recentClosed.map((sprint) => ({
          value: String(sprint.id),
          label: sprint.name,
          meta: sprintMenuMeta(sprint),
          title: sprintDisplayLabel(sprint),
          ticket_count: Number(sprint.ticket_count || 0),
          status: sprint.status,
        }))
      );
      const visibleIds = new Set(recentClosed.concat(allSprints.filter((sprint) => sprint.status !== "closed")).map((sprint) => String(sprint.id)));
      const selectedArchived = allSprints.filter((sprint) => String(sprint.id) === String(current) && !visibleIds.has(String(sprint.id)));
      addGroup(
        translate("sprint.selected_archive", currentLang()) || "Selected archive",
        selectedArchived.map((sprint) => ({
          value: String(sprint.id),
          label: sprint.name,
          meta: sprintMenuMeta(sprint),
          title: sprintDisplayLabel(sprint),
          ticket_count: Number(sprint.ticket_count || 0),
          status: sprint.status,
        }))
      );
      return;
    }

    const matches = allSprints
      .filter((sprint) => sprintDisplayLabel(sprint).toLowerCase().includes(query))
      .slice(0, 30)
      .map((sprint) => ({
        value: String(sprint.id),
        label: sprint.name,
        meta: sprintMenuMeta(sprint),
        title: sprintDisplayLabel(sprint),
        ticket_count: Number(sprint.ticket_count || 0),
        status: sprint.status,
      }));
    addGroup(translate("sprint.sprints", currentLang()) || "Sprints", matches);
    if (!matches.length) {
      const empty = document.createElement("div");
      empty.className = "sprint-filter-empty";
      empty.textContent = translate("sprint.no_matches", currentLang()) || "No matching sprints";
      list.appendChild(empty);
    }
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
    setupProjectSettingsAutosave();
    setupMenus();
    setupConfirms();
    setupCopyButtons();
    setupLocalTimes();
    setupActionLabels();
    setupActionDetails();
    setupMemberRoleForms();
    setupAssigneePickers();
    setupMentionInputs();
    setupOpenCreate();
    setupMobileStatusTabs();
    setupSprintFilter();
    setupSprintProgress();
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
