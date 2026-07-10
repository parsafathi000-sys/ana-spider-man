"""Bot entrypoint — wires config, DB, handlers and runs the PTB event loop.

Run:  python bot.py            (long-polling)
Or set WEBHOOK_URL in .env for webhook mode.

Loads .env via python-dotenv, initialises the SQLite store, registers handlers,
and starts polling. Mirrors Spider's async-first design.
"""
import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

from config import CONFIG
from db.database import get_db
from handlers import register_handlers, register_admin_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("spider_bot")


async def main():
    load_dotenv()
    if not CONFIG.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set — copy .env.example to .env")

    db = get_db()
    await db.init()
    logger.info("DB initialised at %s", CONFIG.DB_PATH)

    app = ApplicationBuilder().token(CONFIG.BOT_TOKEN).build()
    register_handlers(app)
    register_admin_handlers(app)
    logger.info("Handlers registered; servers=%d mock=%s",
                len(CONFIG.SPIDER_SERVERS), CONFIG.MOCK_MODE)

    if CONFIG.WEBHOOK_URL:
        await app.bot.set_webhook(CONFIG.WEBHOOK_URL)
        logger.info("Webhook set: %s", CONFIG.WEBHOOK_URL)
        await app.run_webhook(listen="0.0.0.0", port=CONFIG.PORT)
    else:
        logger.info("Starting long-polling")
        await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
