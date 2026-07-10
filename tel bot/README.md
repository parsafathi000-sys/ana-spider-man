# Spider Telegram VPN Shop Bot

A Telegram shop that sells VLESS VPN configs issued through one or more
**Spider Panel** (FastAPI + Xray) instances via REST. The bot handles the
commerce + UX layer; Spider remains the source of truth for Xray links,
traffic, and inbounds.

## Architecture

```
tel bot/
├── bot.py              Entrypoint: loads .env, inits DB, runs PTB loop
├── config.py           Env-driven config (IRAN_TZ, Spider servers, plans)
├── models/             Typed dataclasses (Server, Inbound, VpnConfig, Order)
├── db/                 aiosqlite store: users, balances, orders, configs
├── api/                SpiderClient — REST contract + MOCK_MODE fallback
├── services/           shop.py: server selection, billing, config builder
├── handlers/           user_handlers.py (shop flow) + admin_handlers.py
├── utils/              i18n (Farsi), byte formatting, QR generation
└── requirements.txt    Pinned deps (upper bounds per Hermes policy)
```

## Setup

```bash
cd "tel bot"
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill BOT_TOKEN + Spider server(s)
python bot.py
```

## How it maps to Spider

| Bot concept            | Spider backend (added next phase)        |
|------------------------|------------------------------------------|
| Server selection       | `GET /api/stats/traffic` per instance    |
| Operator routing       | inbound `name` contains MTN/MCI/Irancell |
| Create user            | `POST /api/users`                        |
| Issue config           | `POST /api/links` → `generate_vless_link`|
| Subscription           | `GET /api/subs/{id}`                     |
| Auth                   | `X-Spider-Token` = `SETTINGS.security_token` |

Currently Spider only exposes `/`, `/health`, `/api/telegram/status`. The bot
defines the contract above; with `MOCK_MODE=true` it runs fully without a live
panel so the UX can be developed and demoed now.

## Bot commands

- `/start` — pick operator → pick plan → pay (balance) → get VLESS + QR
- `/balance` — show wallet balance
- `/myconfigs` — list your issued configs
- `/admin`, `/adminstats` — admin-only server capacity dashboard
