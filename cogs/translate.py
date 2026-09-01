from __future__ import annotations

import asyncio
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import discord
from discord import app_commands
from discord.ext import commands
from deep_translator import GoogleTranslator
from langdetect import detect

GUILD_ID = os.getenv("GUILD_ID")
LANGUAGES_FILE = Path(__file__).parent.parent / "data" / "translate_languages.json"
LANGUAGE_OPTIONS = [
    ("English", "en"),
    ("Japanese", "ja"),
    ("Spanish", "es"),
    ("Russian", "ru"),
    ("Ukrainian", "uk"),
]
TRANSLATION_COOLDOWN = 10
MAX_TRANSLATION_LENGTH = 4000
SENSITIVE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|pwd|secret|token|api[_ -]?key)\s*[:=]", re.IGNORECASE),
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[a-zA-Z0-9_-]{16,}\b"),
    re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
    re.compile(r"https?://[^\s]+\?[^\s]+", re.IGNORECASE),
)
CARD_NUMBER_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


def contains_sensitive_content(text: str) -> bool:
    if any(pattern.search(text) for pattern in SENSITIVE_PATTERNS):
        return True

    for match in CARD_NUMBER_PATTERN.finditer(text):
        digits = re.sub(r"[ -]", "", match.group())
        if len(digits) < 13 or len(digits) > 19:
            continue
        checksum = sum(
            (digit if index % 2 == 0 else (digit * 2 - 9 if digit > 4 else digit * 2))
            for index, digit in enumerate(map(int, reversed(digits)))
        )
        if checksum % 10 == 0:
            return True
    return False


def has_translatable_text(text: str) -> bool:
    text_without_urls = URL_PATTERN.sub(" ", text)
    return bool(text_without_urls.strip()) and any(
        char.isalnum() for char in text_without_urls
    )


def split_translation(text: str, chunk_size: int = 1900) -> list[str]:
    return [text[index:index + chunk_size] for index in range(0, len(text), chunk_size)]


def translate_text(text: str, target: str) -> str:
    try:
        translated = GoogleTranslator(source="auto", target=target).translate(text)
        if translated:
            return translated
    except Exception:
        pass

    url = (
        "https://api.mymemory.translated.net/get?"
        f"q={quote(text)}&langpair={quote(detect(text))}|{quote(target)}"
    )
    request = Request(url, headers={"User-Agent": "TorioClientBOT/1.0"})
    with urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    translated = data.get("responseData", {}).get("translatedText")
    if not translated:
        raise RuntimeError("Translation provider returned no result")
    return translated


class LanguageSelect(discord.ui.Select):
    def __init__(self, message: discord.Message, author_id: int, default_language: str):
        self.message = message
        self.author_id = author_id
        super().__init__(
            placeholder="Select a target language...",
            options=[
                discord.SelectOption(
                    label=label, value=value, default=value == default_language
                )
                for label, value in LANGUAGE_OPTIONS
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This menu can only be used by the person who ran Translate.",
                ephemeral=True,
            )
            return

        target = self.values[0]
        await interaction.response.defer(ephemeral=True)
        try:
            translated = await asyncio.to_thread(
                translate_text, self.message.content, target
            )
        except Exception:
            await interaction.followup.send(
                "Translation failed. Please try again later.", ephemeral=True
            )
            return

        if len(translated) > 1900:
            translated = translated[:1897] + "..."

        language_name = dict((value, label) for label, value in LANGUAGE_OPTIONS)[target]
        await interaction.followup.send(
            f"**Translation ({language_name})**\n{translated}",
            ephemeral=True,
        )


class LanguageSelectView(discord.ui.View):
    def __init__(self, message: discord.Message, author_id: int, default_language: str):
        super().__init__(timeout=60)
        self.add_item(LanguageSelect(message, author_id, default_language))


class TranslateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.languages: dict[str, str] = {}
        self._last_translation: dict[int, float] = {}
        self._load_languages()
        self.translate_message = app_commands.ContextMenu(
            name="Translate",
            callback=self.translate_message_callback,
            guild_ids=[int(GUILD_ID)],
        )

    async def cog_load(self):
        self.bot.tree.add_command(self.translate_message)

    async def cog_unload(self):
        self.bot.tree.remove_command(
            self.translate_message.name,
            type=self.translate_message.type,
            guild=discord.Object(id=int(GUILD_ID)),
        )

    def _load_languages(self):
        if not LANGUAGES_FILE.exists():
            return
        try:
            self.languages = json.loads(LANGUAGES_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.languages = {}

    def _save_languages(self):
        LANGUAGES_FILE.parent.mkdir(parents=True, exist_ok=True)
        LANGUAGES_FILE.write_text(
            json.dumps(self.languages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _get_language(self, interaction: discord.Interaction) -> str:
        saved_language = self.languages.get(str(interaction.user.id))
        if saved_language in {value for _, value in LANGUAGE_OPTIONS}:
            return saved_language

        locale = str(interaction.locale).lower()
        for language in (value for _, value in LANGUAGE_OPTIONS):
            if locale.startswith(language):
                return language
        return "en"

    async def translate_message_callback(self, interaction: discord.Interaction, message: discord.Message):
        if not has_translatable_text(message.content):
            if message.attachments or message.embeds:
                message_type = "image or GIF" if message.attachments else "embed"
                response = (
                    f"This {message_type} has no caption or text to translate. "
                    "Text inside images and GIFs is not supported yet."
                )
            else:
                response = "This message does not contain translatable text."
            await interaction.response.send_message(
                response, ephemeral=True
            )
            return

        if len(message.content) > MAX_TRANSLATION_LENGTH:
            await interaction.response.send_message(
                f"Messages longer than {MAX_TRANSLATION_LENGTH} characters cannot be translated.",
                ephemeral=True,
            )
            return

        if contains_sensitive_content(message.content):
            await interaction.response.send_message(
                "This message may contain sensitive information, so it was not sent "
                "to the translation service.",
                ephemeral=True,
            )
            return

        now = time.monotonic()
        last_translation = self._last_translation.get(interaction.user.id)
        if last_translation is not None and now - last_translation < TRANSLATION_COOLDOWN:
            remaining = int(TRANSLATION_COOLDOWN - (now - last_translation)) + 1
            await interaction.response.send_message(
                f"Please wait {remaining} seconds before translating again.",
                ephemeral=True,
            )
            return
        self._last_translation[interaction.user.id] = now

        target = self._get_language(interaction)
        await interaction.response.defer(ephemeral=True)
        try:
            translated = await asyncio.to_thread(
                translate_text, message.content, target
            )
        except Exception:
            await interaction.followup.send(
                "Translation failed. Please try again later.", ephemeral=True
            )
            return

        if not translated:
            await interaction.followup.send(
                "This message could not be translated.", ephemeral=True
            )
            return

        language_name = dict((value, label) for label, value in LANGUAGE_OPTIONS)[target]
        chunks = split_translation(translated)
        for index, chunk in enumerate(chunks):
            heading = f"**Translation ({language_name})**\n" if index == 0 else ""
            notice = (
                "\n\n-# (Translated using an external translation service.)"
                if index == len(chunks) - 1
                else ""
            )
            await interaction.followup.send(
                f"{heading}{chunk}{notice}", ephemeral=True
            )

    @commands.hybrid_command(
        name="setlanguage", description="Set your default translation language"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(language="Your default translation language")
    @app_commands.choices(language=[
        app_commands.Choice(name=label, value=value)
        for label, value in LANGUAGE_OPTIONS
    ])
    async def setlanguage(self, ctx: commands.Context, language: str):
        self.languages[str(ctx.author.id)] = language
        self._save_languages()
        language_name = dict((value, label) for label, value in LANGUAGE_OPTIONS)[language]
        await ctx.send(
            f"Default translation language set to **{language_name}**.",
            ephemeral=bool(ctx.interaction),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(TranslateCog(bot))