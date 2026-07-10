"""Telegram handlers — user shop flow.

Uses python-telegram-bot v21 (async, ApplicationBuilder). Conversation is kept
simple: /start -> choose operator -> choose plan -> pay -> receive config.
Admin commands live in admin.py.
"""
import io
import secrets

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
)

from config import CONFIG
from db.database import get_db
from services.shop import (
    charge_and_create_order, build_config, lookup_plan, select_server,
)
from utils.i18n import t, LANG
from utils.helpers import now_ir
from utils.qr import make_qr

OPERATORS = ["MTN", "MCI", "Irancell", "Hamrah", "Rightel"]


def _operator_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(op, callback_data=f"op:{op}") for op in OPERATORS
    ]])


def _plan_keyboard():
    buttons = []
    for pid, p in CONFIG.PLANS.items():
        label = f"{p['gb']}GB / {p['days']}روز — {p['price']} {CONFIG.CURRENCY}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"plan:{pid}")])
    return InlineKeyboardMarkup(buttons)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    u = update.effective_user
    await db.upsert_user(u.id, u.username, u.first_name, now_ir().isoformat())
    bal = await db.get_balance(u.id)
    await update.message.reply_text(
        t("welcome") + "\n\n" + t("balance", amount=bal, currency=CONFIG.CURRENCY),
        reply_markup=_operator_keyboard())


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = await get_db().get_balance(update.effective_user.id)
    await update.message.reply_text(
        t("balance", amount=bal, currency=CONFIG.CURRENCY))


async def cmd_myconfigs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await get_db().list_user_configs(update.effective_user.id)
    if not rows:
        await update.message.reply_text(t("no_configs"))
        return
    text = t("my_configs") + "\n\n"
    for r in rows[:10]:
        text += f"• {r['operator'] or '—'} @ {r['server']}\n{r['vless_link']}\n\n"
    await update.message.reply_text(text)


async def cb_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    op = q.data.split(":", 1)[1]
    context.user_data["operator"] = op
    await q.edit_message_text(t("choose_plan"), reply_markup=_plan_keyboard())


async def cb_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pid = q.data.split(":", 1)[1]
    if not lookup_plan(pid):
        await q.edit_message_text(t("invalid_input"))
        return

    uid = q.from_user.id
    operator = context.user_data.get("operator")
    try:
        order = await charge_and_create_order(uid, pid, operator)
    except ValueError:
        await q.edit_message_text(t("insufficient_balance"))
        return

    result = await build_config(uid, order)
    link = result["vless_link"]

    # QR via in-memory PNG
    qr_path = make_qr(link, CONFIG.DB_PATH.parent / "qr")
    with open(qr_path, "rb") as f:
        await q.message.reply_photo(
            InputFile(f, filename="config.png"),
            caption=t("config_ready") + f"\n\n{link}")
    await q.edit_message_text(
        f"{t('order_created', order_id=order['order_id'])}\n⚡ {link}")


def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("myconfigs", cmd_myconfigs))
    app.add_handler(CallbackQueryHandler(cb_operator, pattern=r"^op:"))
    app.add_handler(CallbackQueryHandler(cb_plan, pattern=r"^plan:"))
