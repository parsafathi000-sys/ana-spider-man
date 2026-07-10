"""Shared data models for the bot.

Kept intentionally small and dependency-free so handlers, services and the API
client can pass typed objects around instead of raw dicts. These mirror the
shapes Spider stores in core/state.py (USERS, LINKS, INBOUNDS, SUBS).
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Server:
    """One Spider Panel instance the bot can route to."""
    name: str
    base_url: str
    token: str = ""
    operators: list = field(default_factory=list)


@dataclass
class Inbound:
    """A Spider inbound — operator matching keys off ``name``."""
    inbound_id: str
    name: str
    protocol: str
    network: str
    security: str
    domain: str
    external_port: int = 443


@dataclass
class VpnConfig:
    """A single issued VPN config (one LINK in Spider terms)."""
    uuid: str
    user_id: int
    server: str
    inbound_id: str
    operator: str
    vless_link: str
    traffic_limit_bytes: int
    expire_at: Optional[str]
    created_at: str
    qr_path: Optional[str] = None


@dataclass
class Order:
    order_id: str
    user_id: int
    plan_id: str
    amount: int
    status: str
    created_at: str
