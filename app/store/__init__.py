"""app.store package facade.

All data-access logic lives in focused submodules; this module only re-exports
their public names so ``from app.store import X`` keeps working unchanged. The
submodules form a strict dependency DAG with no import cycles:

    _validation            (leaf: validators / normalizers / project config)
    _read_models           (leaf: read-only ticket SELECTs + row mappers)
    _policies              -> _validation
    _notification_outbox   -> _read_models
    _action_log            -> _notification_outbox
    _users                 -> _notification_outbox
    _projects              -> _validation, _policies, _action_log, _notification_outbox
    _sprints               -> _projects, _policies, _action_log, _validation
    _integrations          -> _validation, _read_models, _action_log
    _accounts              -> _notification_outbox
    _tickets               -> _projects, _sprints, _read_models, _policies, _validation, _action_log
    _board / _statistics   -> _projects, _sprints, _read_models, _policies, _validation
"""

# log_action (action_log writes + notify fan-out) lives in _action_log.py.
from ._action_log import log_action as log_action

# Validators, normalizers, and per-project config helpers now live in
# _validation.py. Re-exported here so app.store stays the single public facade
# (the `as` aliases mark them as intentional re-exports for linters).
from ._validation import (  # noqa: E402
    STATS_VISIBILITIES as STATS_VISIBILITIES,
    TICKET_DELETE_POLICIES as TICKET_DELETE_POLICIES,
    normalize_github_installation_id as normalize_github_installation_id,
    normalize_github_link_url as normalize_github_link_url,
    normalize_github_repo as normalize_github_repo,
    normalize_project_statuses as normalize_project_statuses,
    normalize_project_ticket_types as normalize_project_ticket_types,
    normalize_stats_visibility as normalize_stats_visibility,
    normalize_ticket_delete_policy as normalize_ticket_delete_policy,
    project_stats_visibility as project_stats_visibility,
    project_statuses as project_statuses,
    project_ticket_delete_own_only as project_ticket_delete_own_only,
    project_ticket_delete_policy as project_ticket_delete_policy,
    project_ticket_types as project_ticket_types,
    validate_date_string as validate_date_string,
    validate_priority as validate_priority,
    validate_project_key as validate_project_key,
    validate_project_ticket_status as validate_project_ticket_status,
    validate_project_ticket_type as validate_project_ticket_type,
    validate_status as validate_status,
    validate_story_points as validate_story_points,
    validate_ticket_link_type as validate_ticket_link_type,
    validate_ticket_type as validate_ticket_type,
)


# User records and global-admin role syncing live in _users.py.
from ._users import (  # noqa: E402
    list_users as list_users,
    sync_configured_admin_roles as sync_configured_admin_roles,
    upsert_user as upsert_user,
)


# Notification fan-out and preference storage live in _notification_outbox.py
# (imports _read_models, never _tickets/_action_log). Re-exported from facade.
from ._notification_outbox import (  # noqa: E402
    describe_action as describe_action,
    enqueue_notifications as enqueue_notifications,
    ensure_notification_preferences as ensure_notification_preferences,
    notification_preferences as notification_preferences,
    notification_preferences_conn as notification_preferences_conn,
    notification_recipients as notification_recipients,
    update_notification_preferences as update_notification_preferences,
)


# Project records, membership, and settings live in _projects.py.
from ._projects import (  # noqa: E402
    add_project_member as add_project_member,
    create_project as create_project,
    delete_project as delete_project,
    get_project_by_key as get_project_by_key,
    get_project_for_ticket_key as get_project_for_ticket_key,
    list_projects as list_projects,
    project_members as project_members,
    remove_project_member as remove_project_member,
    require_project_member_conn as require_project_member_conn,
    search_project_users as search_project_users,
    update_project_member as update_project_member,
    update_project_settings as update_project_settings,
)


# Project authorization policies live in _policies.py (cycle-free: db + the
# validation helpers only). Re-exported so app.store stays the public facade.
from ._policies import (  # noqa: E402
    can_delete_ticket as can_delete_ticket,
    can_view_project_stats as can_view_project_stats,
    project_role_for_user as project_role_for_user,
    require_project_access as require_project_access,
    require_project_admin as require_project_admin,
    require_project_stats_access as require_project_stats_access,
    require_ticket_delete_access as require_ticket_delete_access,
)


# Sprint records and lifecycle live in _sprints.py.
from ._sprints import (  # noqa: E402
    create_sprint as create_sprint,
    list_project_sprints as list_project_sprints,
    update_sprint as update_sprint,
    update_sprint_status as update_sprint_status,
    validate_project_sprint_conn as validate_project_sprint_conn,
)


# Ticket records, updates, comments, links, and search live in _tickets.py.
from ._tickets import (  # noqa: E402
    add_comment as add_comment,
    close_ticket as close_ticket,
    create_ticket as create_ticket,
    delete_ticket as delete_ticket,
    link_ticket as link_ticket,
    reopen_ticket as reopen_ticket,
    search_linkable_tickets as search_linkable_tickets,
    search_tickets as search_tickets,
    set_watch as set_watch,
    unlink_ticket as unlink_ticket,
    update_ticket as update_ticket,
    update_ticket_link as update_ticket_link,
)


# Read-only ticket helpers and row mappers live in _read_models.py — the seam
# that breaks the notifications<->tickets cycle (reads import nothing from
# tickets/action_log/notifications). Re-exported from the facade.
from ._read_models import (  # noqa: E402
    attach_ticket_link_summaries_conn as attach_ticket_link_summaries_conn,
    get_ticket as get_ticket,
    get_ticket_by_id_conn as get_ticket_by_id_conn,
    get_ticket_by_key_conn as get_ticket_by_key_conn,
    get_ticket_bundle as get_ticket_bundle,
    list_linkable_tickets_conn as list_linkable_tickets_conn,
    list_ticket_links_conn as list_ticket_links_conn,
)


# Board view assembly lives in _board.py.
from ._board import board_for_project as board_for_project  # noqa: E402


# Project statistics live in _statistics.py.
from ._statistics import project_statistics as project_statistics  # noqa: E402


# GitHub linking helpers live in _integrations.py (imports _validation,
# _read_models, _action_log). Re-exported from the facade.
from ._integrations import (  # noqa: E402
    GITHUB_REF_TYPES as GITHUB_REF_TYPES,
    TICKET_KEY_RE as TICKET_KEY_RE,
    extract_ticket_keys as extract_ticket_keys,
    link_github_ref as link_github_ref,
    mark_github_delivery as mark_github_delivery,
)

# Per-user account peripherals (MCP tokens, Telegram links/tokens, api_audit,
# retention pruning, test notification) live in _accounts.py.
from ._accounts import (  # noqa: E402
    consume_telegram_link_token as consume_telegram_link_token,
    create_mcp_token as create_mcp_token,
    create_telegram_link_token as create_telegram_link_token,
    create_test_notification as create_test_notification,
    get_telegram_link as get_telegram_link,
    list_mcp_tokens as list_mcp_tokens,
    purge_expired_records as purge_expired_records,
    record_api_audit as record_api_audit,
    revoke_mcp_token as revoke_mcp_token,
    unlink_telegram as unlink_telegram,
)
