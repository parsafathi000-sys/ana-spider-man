"""Services package.

All Xray logic (install, keys, config generation, link generation, process
control) lives in `xray_service`. The old `xray_core` module was a conflicting
duplicate and has been removed. Do NOT reintroduce a second xray module.

NOTE: `relay_vless` and `xhttp_siz10` are root-level modules (not in this
package) in the flat layout, so they are NOT re-exported here.
"""
from .xray_service import (
    generate_vless_link,
    generate_xray_server_config,
    generate_reality_keys,
    ensure_reality_keys,
    start_xray,
    stop_xray,
    restart_xray,
    get_xray_status,
    install_xray_core,
    is_xray_installed,
    get_xray_version,
    validate_xray_config,
    write_xray_config,
    RealityIncompleteError,
)
