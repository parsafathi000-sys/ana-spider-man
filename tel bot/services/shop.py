"""Services: bot-side business logic.

Three responsibilities, kept separate so handlers stay thin:
  * server_selection — pick the best Spider instance (operator match + capacity)
  * orders          — plan pricing + balance/billing against the DB
  * config_builder  — turn a paid order into a real VLESS config via SpiderClient
"""
from datetime import datetime, timedelta

from config import CONFIG, IRAN_TZ
from models.schemas import Server
from api.spider_client import SpiderClient
from db.database import get_db
from utils.helpers import now_ir, parse_size_to_bytes


# ── Server selection ──────────────────────────────────────────────
# Capacity scoring: prefer servers with the most free traffic. Operator
# preference is an exact filter first; if no server matches the requested
# operator, fall back to any server (so a shop never dead-ends).
async def select_server(operator: str | None):
    clients = [(s, SpiderClient(s)) for s in CONFIG.SPIDER_SERVERS]
    if not clients:
        return None, None

    # 1) operator-exact match
    if operator:
        for s, c in clients:
            if operator in s.operators:
                return s, c

    # 2) otherwise the least-loaded server by free capacity
    best, best_client, best_free = None, None, -1
    for s, c in clients:
        try:
            stats = await c.server_stats()
        except Exception:
            stats = {"total_bytes": 0, "used_bytes": 0}
        free = stats.get("total_bytes", 0) - stats.get("used_bytes", 0)
        if free > best_free:
            best, best_client, best_free = s, c, free
    return best, best_client


# ── Orders / billing ──────────────────────────────────────────────
def lookup_plan(plan_id: str) -> dict | None:
    return CONFIG.PLANS.get(str(plan_id))


async def charge_and_create_order(telegram_id: int, plan_id: str,
                                  operator: str | None) -> dict:
    """Validate balance, deduct, persist order as 'paid'.

    Returns the order dict (caller then calls build_config).
    """
    db = get_db()
    plan = lookup_plan(plan_id)
    if not plan:
        raise ValueError("unknown_plan")

    balance = await db.get_balance(telegram_id)
    if balance < plan["price"]:
        raise ValueError("insufficient_balance")

    await db.add_balance(telegram_id, -plan["price"])

    order_id = f"ord_{telegram_id}_{int(now_ir().timestamp())}"
    await db.create_order(
        order_id=order_id, telegram_id=telegram_id, plan_id=plan_id,
        gb=plan["gb"], days=plan["days"], amount=plan["price"],
        operator=operator, server=None,
        created_at=now_ir().isoformat())
    await db.set_order_status(order_id, "paid")
    return {"order_id": order_id, "plan": plan, "operator": operator}


# ── Config builder ────────────────────────────────────────────────
async def build_config(telegram_id: int, order: dict) -> dict:
    """Issue a real config on the selected Spider server and persist it."""
    db = get_db()
    server, client = await select_server(order["operator"])
    if server is None:
        raise RuntimeError("no_spider_server")

    plan = order["plan"]
    limit_bytes = parse_size_to_bytes(plan["gb"], "GB")
    days = plan["days"]
    username = f"tg_{telegram_id}"

    user = await client.create_user(username, limit_bytes, days)
    user_id = user["user_id"]

    link = await client.create_link(user_id, remark=f"tg{telegram_id}", inbound_id=None)
    uuid = link["uuid"]
    vless = link["vless_link"]

    expire_at = (now_ir() + timedelta(days=days)).isoformat()

    await db.save_config(
        uuid=uuid, telegram_id=telegram_id, order_id=order["order_id"],
        server=server.name, inbound_id="default", operator=order["operator"],
        vless_link=vless, traffic_limit_bytes=limit_bytes,
        expire_at=expire_at, created_at=now_ir().isoformat())

    # mark order with chosen server for ops visibility
    await db.conn.execute(
        "UPDATE orders SET server=? WHERE order_id=?",
        (server.name, order["order_id"]))
    await db.conn.commit()

    return {"uuid": uuid, "vless_link": vless, "server": server.name,
            "operator": order["operator"], "expire_at": expire_at}
