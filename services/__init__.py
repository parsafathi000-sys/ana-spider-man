"""Services package"""
from .xray_service import (
    generate_vless_link,
    generate_xray_server_config,
    generate_reality_keys,
    start_xray,
    stop_xray,
    get_xray_status,
    install_xray_core,
    is_xray_installed,
    get_xray_version,
    validate_xray_config,
    write_xray_config,
)

from .xray_core import (
    generate_xray_config,
    install_xray_core,
    start_xray,
    stop_xray,
    restart_xray,
    get_xray_status,
    is_xray_installed,
    get_xray_version,
)

from .relay_vless import (
    parse_vless_header,
    check_and_use,
    websocket_tunnel,
    _ws_client_ip,
)

from .xhttp_siz10 import (
    router as xhttp_siz10_router,
)