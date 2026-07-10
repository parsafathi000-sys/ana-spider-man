"""REST API client for the Spider Panel backend.

CONTEXT: As scanned, Spider (main.py) currently exposes only
  GET /  GET /health  GET /api/telegram/status  POST /api/telegram/seen
There is NO user/inbound/link/sub REST API yet. This client defines the
contract the bot expects Spider to fulfil (the next build phase adds those
routers to Spider and guards them with SECURITY_TOKEN). Every method degrades
to mock data when CONFIG.MOCK_MODE is true so the bot runs end-to-end for
development/demo without a live panel.

Auth: header ``X-Spider-Token: <token>`` (Spider's existing SETTINGS["security_token"]
is the natural secret to reuse — see config/settings.py).

Convention: one ``SpiderClient`` per server instance (base_url + token).
"""
import json
from typing import Optional

import aiohttp

from config import CONFIG
from models.schemas import Inbound, Server


class SpiderError(RuntimeError):
    pass


class SpiderClient:
    def __init__(self, server: Server):
        self.server = server
        self.base = server.base_url.rstrip("/")

    def _headers(self) -> dict:
        return {"X-Spider-Token": self.server.token,
                "Content-Type": "application/json"}

    async def _request(self, method: str, path: str, json_body: Optional[dict] = None) -> dict:
        if CONFIG.MOCK_MODE:
            return _mock_response(method, path, json_body)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=CONFIG.SPIDER_TIMEOUT)) as s:
            async with s.request(method, f"{self.base}{path}",
                                 headers=self._headers(), json=json_body) as resp:
                if resp.status >= 400:
                    raise SpiderError(f"{self.server.name} {method} {path} -> {resp.status}")
                return await resp.json()

    # ── Read endpoints (bot dashboard / admin) ──────────────────
    async def list_inbounds(self) -> list[Inbound]:
        data = await self._request("GET", "/api/inbounds")
        out = []
        for iid, ib in data.get("inbounds", {}).items():
            out.append(Inbound(
                inbound_id=iid, name=ib.get("name", iid),
                protocol=ib.get("protocol", "vless"),
                network=ib.get("network", "ws"),
                security=ib.get("security", "tls"),
                domain=ib.get("domain", ""),
                external_port=ib.get("external_port", 443),
            ))
        return out

    async def server_stats(self) -> dict:
        """Capacity signal: total/used bytes across links on this instance."""
        return await self._request("GET", "/api/stats/traffic")

    # ── Write endpoints (issue a config for a user) ─────────────
    async def create_user(self, username: str, traffic_limit_bytes: int,
                          days: int, inbound_id: Optional[str] = None) -> dict:
        body = {"username": username, "traffic_limit_bytes": traffic_limit_bytes,
                "days": days, "inbound_id": inbound_id}
        return await self._request("POST", "/api/users", body)

    async def create_link(self, user_id: str, remark: str,
                          inbound_id: Optional[str] = None) -> dict:
        body = {"user_id": user_id, "remark": remark, "inbound_id": inbound_id}
        return await self._request("POST", "/api/links", body)

    async def get_subscription(self, sub_id: str) -> str:
        """Return the aggregated subscription body (all links as vless:// lines)."""
        data = await self._request("GET", f"/api/subs/{sub_id}")
        return data.get("subscription", "")


# ── Mock backend (MOCK_MODE) ────────────────────────────────────
def _mock_response(method: str, path: str, body: Optional[dict]) -> dict:
    if path == "/api/inbounds":
        return {"inbounds": {
            "default": {"name": "VLESS+WS پیش‌فرض", "protocol": "vless",
                        "network": "ws", "security": "tls",
                        "domain": "mock.spider.local", "external_port": 443},
        }}
    if path == "/api/stats/traffic":
        return {"total_bytes": 5 * 1024 ** 4, "used_bytes": 1 * 1024 ** 4,
                "links": 12}
    if path == "/api/users" and method == "POST":
        return {"user_id": "u_mock_" + str(abs(hash(json.dumps(body or {})))),
                "ok": True}
    if path == "/api/links" and method == "POST":
        uid = "a1b2c3d4e5f6" + str(abs(hash(json.dumps(body or {}))))[:16]
        return {"uuid": uid, "vless_link":
                f"vless://{uid}@mock.spider.local:443?encryption=none&security=tls&type=ws&host=mock.spider.local&path=%2Fws%2F{uid}#mock",
                "sub_id": "sub_mock"}
    if path.startswith("/api/subs/"):
        return {"subscription": "vless://mock@mock.spider.local:443#mock"}
    return {}
