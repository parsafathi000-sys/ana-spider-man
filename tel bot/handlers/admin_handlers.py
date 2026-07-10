"""Admin panel handlers — restricted to CONFIG.ADMIN_IDS.

Shows per-server capacity/stats and recent orders. Reads from Spider via the
same SpiderClient the user flow uses, so admin sees real capacity before the
next phase wires up Spider's REST API.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

from config import CONFIG
from api.spider_client import SpiderClient


def _is_admin(user_id: int) -> bool:
    return user_id in CONFIG.ADMIN_IDS


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    await update.message.reply_text(t_admin("admin_panel"), reply_markup=_admin_keyboard())


async def cmd_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    lines = [t_admin("admin_stats")]
    for s in CONFIG.SPIDER_SERVERS:
        try:
            client = SpiderClient(s)
            stats = await client.server_stats()
            total = stats.get("total_bytes", 0)
            used = stats.get("used_bytes", 0)
            free = total - used
            lines.append(f"\n• {s.name} ({', '.join(s.operators) or '—'})\n"
                         f"  free: {_fmt(free)} / total: {_fmt(total)}")
        except Exception as e:
            lines.append(f"\n• {s.name}: ERROR {e}")
    await update.message.reply_text("\n".join(lines))


def _admin_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📊 آمار سرورها", callback_data="adm:stats"),
    ]])


def _fmt(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


# tiny local i18n for admin only (keeps user i18n file clean)
def t_admin(key: str) -> str:
    return {
        "admin_panel": "🔐 پنل مدیریت",
        "admin_stats": "📊 آمار سرورها:",
    }.get(key, key)


def register_admin_handlers(app):
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("adminstats", cmd_admin_stats))
