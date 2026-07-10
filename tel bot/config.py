"""Bot configuration.

Mirrors Spider's ``config/settings.py`` philosophy: everything comes from the
environment (no hardcoded secrets), with an ``IRAN_TZ`` and a single ``CONFIG``
object the rest of the bot imports. Secrets (BOT_TOKEN, Spider tokens) live in
.env only — never in code.
"""
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

IRAN_TZ = ZoneInfo("Asia/Tehran")

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))


def _env_list(name: str):
    raw = os.environ.get(name)
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _parse_servers() -> list:
    """Build the list of Spider instances from env.

    SPIDER_SERVERS (JSON array) wins. Falls back to the single
    SPIDER_API_BASE / SPIDER_API_TOKEN pair. Empty if neither is set.
    """
    raw = os.environ.get("SPIDER_SERVERS")
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                from models.schemas import Server
                out = []
                for item in data:
                    if isinstance(item, dict) and item.get("base_url"):
                        out.append(Server(
                            name=item.get("name", "server"),
                            base_url=item["base_url"].rstrip("/"),
                            token=item.get("token", ""),
                            operators=item.get("operators", []),
                        ))
                return out
        except Exception:
            pass
    from models.schemas import Server
    base = os.environ.get("SPIDER_API_BASE")
    if base:
        return [Server(
            name="default", base_url=base.rstrip("/"),
            token=os.environ.get("SPIDER_API_TOKEN", ""), operators=[])]
    return []


class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    ADMIN_IDS = [int(x) for x in _env_list("ADMIN_TELEGRAM_IDS") if x.isdigit()]
    DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "bot.db")))
    SPIDER_SERVERS = _parse_servers()
    SPIDER_TIMEOUT = float(os.environ.get("SPIDER_TIMEOUT", "15"))
    MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() in ("1", "true", "yes")
    CURRENCY = os.environ.get("CURRENCY", "تومان")
    PLANS = json.loads(os.environ.get(
        "PLANS",
        '{"1":{"gb":5,"days":30,"price":50000},'
        '"2":{"gb":15,"days":30,"price":120000},'
        '"3":{"gb":50,"days":30,"price":300000}}',
    ))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
    PORT = int(os.environ.get("PORT", "8443"))

    @property
    def has_servers(self) -> bool:
        return bool(self.SPIDER_SERVERS)


CONFIG = Config()
