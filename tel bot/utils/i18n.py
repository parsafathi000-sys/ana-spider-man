"""Persian (Farsi) strings + tiny i18n helper.

UI mirrors Spider's Farsi-first style. Add keys here; handlers call ``t(key)``.
"""
LANG = "fa"

_STRINGS = {
    "welcome": "به فروشگاه VPN خوش آمدید 🕷️\n\nیک پلن انتخاب کنید:",
    "choose_operator": "اپراتور مورد نظر خود را انتخاب کنید:",
    "choose_plan": "پلن مورد نظر را انتخاب کنید:",
    "balance": "💰 موجودی: {amount} {currency}",
    "insufficient_balance": "موجودی کافی نیست. لطفاً شارژ کنید.",
    "order_created": "✅ سفارش ثبت شد.\nشناسه: {order_id}",
    "config_ready": "⚡ کانفیگ شما آماده است:",
    "my_configs": "📋 کانفیگ‌های شما:",
    "no_configs": "هنوز کانفیگی ندارید.",
    "admin_panel": "🔐 پنل مدیریت",
    "admin_stats": "📊 آمار سرورها:",
    "invalid_input": "ورودی نامعتبر است.",
    "cancel": "لغو",
    "back": "بازگشت",
}


def t(key: str, **kwargs) -> str:
    s = _STRINGS.get(key, key)
    try:
        return s.format(**kwargs)
    except Exception:
        return s
