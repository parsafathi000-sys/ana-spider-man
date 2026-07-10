"""SQLite database layer for the bot.

Stores shop state that Spider does NOT own: Telegram user balances, orders,
and the bot-side config history (which config belongs to which Telegram user
on which Spider server). Spider remains the source of truth for the actual
Xray links/traffic; the bot persists the mapping + commerce side.

Uses aiosqlite (async) to match Spider's async style. Schema is created
lazily on first ``init()``.
"""
import aiosqlite
from pathlib import Path

from config import CONFIG


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id   INTEGER PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    balance       INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      TEXT PRIMARY KEY,
    telegram_id   INTEGER NOT NULL,
    plan_id       TEXT NOT NULL,
    gb            INTEGER NOT NULL,
    days          INTEGER NOT NULL,
    amount        INTEGER NOT NULL,
    operator      TEXT,
    server        TEXT,
    status        TEXT NOT NULL DEFAULT 'pending',
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(telegram_id);

CREATE TABLE IF NOT EXISTS configs (
    uuid          TEXT PRIMARY KEY,
    telegram_id   INTEGER NOT NULL,
    order_id      TEXT,
    server        TEXT NOT NULL,
    inbound_id    TEXT NOT NULL,
    operator      TEXT,
    vless_link    TEXT NOT NULL,
    traffic_limit_bytes INTEGER NOT NULL,
    expire_at     TEXT,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_configs_user ON configs(telegram_id);
"""


class Database:
    def __init__(self, path: Path):
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def init(self):
        self._conn = await aiosqlite.connect(str(self._path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not initialised — call init() first")
        return self._conn

    # ── Users ───────────────────────────────────────────────────
    async def get_user(self, telegram_id: int) -> dict | None:
        cur = await self.conn.execute(
            "SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def upsert_user(self, telegram_id: int, username: str | None,
                          first_name: str | None, now: str):
        await self.conn.execute(
            """INSERT INTO users (telegram_id, username, first_name, balance, created_at, updated_at)
               VALUES (?, ?, ?, 0, ?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET
                 username=excluded.username, first_name=excluded.first_name,
                 updated_at=excluded.updated_at""",
            (telegram_id, username, first_name, now, now))
        await self.conn.commit()

    async def add_balance(self, telegram_id: int, amount: int):
        await self.conn.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id=?",
            (amount, telegram_id))
        await self.conn.commit()

    async def get_balance(self, telegram_id: int) -> int:
        cur = await self.conn.execute(
            "SELECT balance FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cur.fetchone()
        return int(row["balance"]) if row else 0

    # ── Orders ──────────────────────────────────────────────────
    async def create_order(self, order_id: str, telegram_id: int, plan_id: str,
                           gb: int, days: int, amount: int, operator: str | None,
                           server: str | None, created_at: str):
        await self.conn.execute(
            """INSERT INTO orders (order_id, telegram_id, plan_id, gb, days, amount, operator, server, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (order_id, telegram_id, plan_id, gb, days, amount, operator, server, created_at))
        await self.conn.commit()

    async def set_order_status(self, order_id: str, status: str):
        await self.conn.execute(
            "UPDATE orders SET status=? WHERE order_id=?", (status, order_id))
        await self.conn.commit()

    # ── Configs ─────────────────────────────────────────────────
    async def save_config(self, uuid: str, telegram_id: int, order_id: str | None,
                          server: str, inbound_id: str, operator: str | None,
                          vless_link: str, traffic_limit_bytes: int,
                          expire_at: str | None, created_at: str):
        await self.conn.execute(
            """INSERT INTO configs (uuid, telegram_id, order_id, server, inbound_id, operator, vless_link, traffic_limit_bytes, expire_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uuid, telegram_id, order_id, server, inbound_id, operator, vless_link,
             traffic_limit_bytes, expire_at, created_at))
        await self.conn.commit()

    async def list_user_configs(self, telegram_id: int) -> list:
        cur = await self.conn.execute(
            "SELECT * FROM configs WHERE telegram_id=? ORDER BY created_at DESC",
            (telegram_id,))
        return [dict(r) for r in await cur.fetchall()]


_db: Database | None = None


def get_db() -> Database:
    """Process-wide singleton, initialised by bot.py before the event loop runs."""
    global _db
    if _db is None:
        _db = Database(CONFIG.DB_PATH)
    return _db
