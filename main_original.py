def generate_vless_link(uuid: str, remark: str = "Spider", inbound_id: str | None = None, user: dict | None = None) -> str:
    """Generate a VLESS share-link strictly based on the real Xray inbound config.

    The link reflects:
    - external domain & external port (public facing values)
    - network (ws, xhttp, grpc, etc.)
    - security (tls, reality) and all required reality params (pbk, sid, spx)
    - transport-specific fields (path, mode, serviceName, extra)
    - fingerprint, sni, alpn where appropriate

    If `user` is provided, user-specific overrides for transport/sni are respected
    but the inbound remains the primary source of truth.
    """
    import json
    from urllib.parse import quote
    # Resolve inbound: use provided id, otherwise fall back to a deterministic default (first inbound)
    inbound = None
    if inbound_id:
        inbound = INBOUNDS.get(inbound_id)
    if not inbound:
        inbound = next(iter(INBOUNDS.values())) if INBOUNDS else {}

    # Resolve host and port (public values) - NEVER use internal port
    host = inbound.get("external_domain") or inbound.get("domain") or SETTINGS.get("domain") or get_host()
    port = inbound.get("external_port", 443)
    network = inbound.get("network", "ws")
    security = inbound.get("security", "tls")
    sni = inbound.get("sni") or host
    fp = inbound.get("fingerprint", "chrome")

    # Allow user-specific overrides for transport/sni if provided
    if user:
        if user.get("transport_type"):
            network = user["transport_type"]
        if user.get("sni"):
            sni = user["sni"]

    params: dict[str, str] = {
        "encryption": "none",
        "security": security,
        "type": network,
        "host": host,
        "sni": sni,
        "fp": fp,
    }

    # Transport specific handling
    if network == "ws":
        ws_path = inbound.get("ws_settings", {}).get("path", f"/ws/{uuid}")
        params["path"] = ws_path
        params["alpn"] = "http/1.1"
    elif network == "xhttp":
        xh = inbound.get("xhttp_settings", {})
        params["mode"] = xh.get("mode", "auto")
        params["path"] = xh.get("path", "/")
        params["alpn"] = "h2,http/1.1"
        # Extra settings (excluding the ones already used)
        extra_dict = {k: v for k, v in xh.items() if k not in ("mode", "path")}
        if extra_dict:
            params["extra"] = quote(json.dumps(extra_dict, separators=(",", ":")))
    elif network == "grpc":
        params["serviceName"] = inbound.get("grpc_settings", {}).get("serviceName", "")
    elif network == "tcp":
        params["alpn"] = "h2,http/1.1"

    # Reality protocol – ensure required fields exist
    if security == "reality":
        rs = inbound.get("reality_settings", {})
        # Required fields validation – if missing, raise clear error
        missing = []
        # Use private_key/public_key from inbound config (persisted)
        if not rs.get("private_key") and not rs.get("public_key"):
            missing.append("pbk")
        if not rs.get("short_id"):
            missing.append("sid")
        if not rs.get("sni") and not rs.get("serverNames"):
            missing.append("sni")
        if missing:
            raise ValueError(f"Reality configuration incomplete: missing {', '.join(missing)}")
        # Use the persisted keys for the link
        params["pbk"] = rs.get("public_key", "")  # PublicKey goes to pbk
        params["sid"] = rs.get("short_id", "")
        params["spx"] = quote(rs.get("spiderx", "/"))

    # Build query string, skipping empty values
    query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items() if v)
    return f"vless://{uuid}@{host}:{port}?{query}#{quote(remark)}"


def uptime() -> str: