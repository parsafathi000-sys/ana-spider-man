# shared.py — Relay-facing alias for the canonical state in core.state.
#
# During the flat-rewrite the project kept `from shared import (...)` inside
# relay_vless.py. To avoid forking state into two separate dicts (which would
# cause silent data loss between the relay and the rest of the app), this
# module re-exports the real shared state from core.state. Relay-local
# constants (RELAY_BUF) live here.
from core.state import (  # noqa: F401
    stats,
    hourly_traffic,
    connections,
    error_logs,
    LINKS,
    LINKS_LOCK,
    PATH_INDEX,
    PATH_INDEX_LOCK,
    SUBS,
    SUBS_LOCK,
    USERS,
    USERS_LOCK,
    INBOUNDS,
    INBOUNDS_LOCK,
    SESSIONS,
    SESSIONS_LOCK,
    is_link_allowed,
    save_state,
)

# ── VLESS Relay local constants ──
RELAY_BUF = 256 * 1024   # 256 KB buffer
sub_clients: dict = {}
TIMEOUT = 30

IP_LOCK = __import__("threading").Lock()
