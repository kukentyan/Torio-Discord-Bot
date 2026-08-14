import json
from pathlib import Path
import discord

LOCALES_DIR = Path(__file__).parent.parent / "locales"

_locales_cache = {}
_modules_cache = None


def load_locale(locale: str) -> dict:
    if locale not in _locales_cache:
        file_path = LOCALES_DIR / f"{locale}.json"
        if not file_path.exists():
            file_path = LOCALES_DIR / "en.json"
        with open(file_path, "r", encoding="utf-8") as f:
            _locales_cache[locale] = json.load(f)
    return _locales_cache[locale]


def get_modules() -> dict:
    global _modules_cache
    if _modules_cache is None:
        file_path = LOCALES_DIR / "modules.json"
        with open(file_path, "r", encoding="utf-8") as f:
            _modules_cache = json.load(f)
    return _modules_cache


def get_user_locale(target) -> str:
    """
    Returns 'ja', 'ru', 'uk', 'es', or 'en' based on target's locale (Interaction or Context).
    """
    locale = None
    if isinstance(target, discord.Interaction):
        locale = target.locale
    elif hasattr(target, "interaction") and target.interaction:
        locale = target.interaction.locale

    if locale:
        loc_str = str(locale).lower()
        if loc_str.startswith("ja"):
            return "ja"
        elif loc_str.startswith("ru"):
            return "ru"
        elif loc_str.startswith("uk"):
            return "uk"
        elif loc_str.startswith("es"):
            return "es"
    return "en"


def get_text(section: str, locale: str = "en") -> dict:
    loc_data = load_locale(locale)
    return loc_data.get(section, {})
