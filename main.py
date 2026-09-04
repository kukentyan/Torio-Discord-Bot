import asyncio
import logging
import os
import socket
from pathlib import Path
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from utils.i18n import get_user_locale, get_text

# ---------------------------------------------------------
# Monkey Patch: StickerFormatType & StickerItem Crash Prevention
# Prevents KeyError / ValueError when Discord sends new sticker formats (e.g., GIF)
# ---------------------------------------------------------
def _apply_sticker_patches():
    try:
        from discord.enums import StickerFormatType
        value_cls = getattr(StickerFormatType, "_enum_value_cls_", None)
        if value_cls is not None:
            @property
            def safe_file_extension(self) -> str:
                # 1: png, 2: apng, 3: lottie (json), 4: gif
                lookup = {1: "png", 2: "png", 3: "json", 4: "gif"}
                val = getattr(self, "value", None)
                if val in lookup:
                    return lookup[val]
                name = getattr(self, "name", "").lower()
                if "gif" in name:
                    return "gif"
                return "png"

            value_cls.file_extension = safe_file_extension
            print("Successfully applied StickerFormatType patch.")
    except Exception as e:
        print(f"[Warning] Failed to patch StickerFormatType: {e}")

    try:
        import discord.sticker
        orig_init = discord.sticker.StickerItem.__init__

        def safe_sticker_init(self, *, state, data):
            try:
                orig_init(self, state=state, data=data)
            except Exception:
                self._state = state
                self.name = data.get("name", "")
                self.id = int(data.get("id", 0))
                self.format = getattr(discord.enums.StickerFormatType, "png", None)
                self.url = f"https://cdn.discordapp.com/stickers/{self.id}.png"

        discord.sticker.StickerItem.__init__ = safe_sticker_init
    except Exception as e:
        print(f"[Warning] Failed to patch StickerItem: {e}")

_apply_sticker_patches()


# ---------------------------------------------------------
# Environment & Intents Setup
# ---------------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
ALLOWED_CHANNEL_ID = os.getenv("ALLOWED_CHANNEL_ID")
BOTCHANNELID = os.getenv("BOTCHANNELID")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True


class TorioBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        cogs = [
            "cogs.general",
            "cogs.client_info",
            "cogs.events",
            "cogs.role_panel",
            "cogs.vc_recruit",
            "cogs.translate",
            "cogs.ticket"
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"Loaded extension: {cog}")
            except Exception as e:
                print(f"Failed to load extension {cog}: {e}")


bot = TorioBot()

# Per-user cooldown: 1 command per 2.0 seconds
user_cooldown = commands.CooldownMapping.from_cooldown(
    1, 2.0, lambda obj: getattr(obj, "user", getattr(obj, "author", None)).id
)


# ---------------------------------------------------------
# Global Check & Notifications (Ephemeral for user privacy + i18n)
# ---------------------------------------------------------
@bot.check
async def global_checks(ctx: commands.Context):
    if ctx.command and ctx.command.name in [
        "vbchannel", "grolepannel", "translate", "supportsetup"
    ]:
        return True

    locale = get_user_locale(ctx)
    gen_t = get_text("general", locale)

    # Check allowed channel
    if ALLOWED_CHANNEL_ID and ctx.channel.id != int(ALLOWED_CHANNEL_ID):
        redirect_msg = gen_t.get(
            "bot_channel_only", "Use commands in the bot channel only."
        )
        if BOTCHANNELID:
            redirect_msg += f"\n{BOTCHANNELID}"

        if ctx.interaction:
            # Ephemeral notification: visible ONLY to the user who invoked the command
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(redirect_msg, ephemeral=True)
            else:
                await ctx.interaction.followup.send(redirect_msg, ephemeral=True)
        else:
            await ctx.send(f"{ctx.author.mention} {redirect_msg}", delete_after=3.0)
        return False

    # Check rate limit cooldown (per-user)
    bucket = user_cooldown.get_bucket(ctx)
    retry_after = bucket.update_rate_limit()

    if retry_after:
        cd_template = gen_t.get(
            "command_cooldown",
            "Please wait {wait}s before using another command."
        )
        cd_msg = cd_template.format(wait=f"{retry_after:.1f}")
        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(cd_msg, ephemeral=True)
            else:
                await ctx.interaction.followup.send(cd_msg, ephemeral=True)
        else:
            await ctx.send(f"{ctx.author.mention} {cd_msg}", delete_after=3.0)
        return False

    return True


# ---------------------------------------------------------
# Error Handlers (Slash & Prefix)
# ---------------------------------------------------------
@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CommandOnCooldown):
        msg = f"Please wait {error.retry_after:.1f}s before using this command."
    elif isinstance(error, app_commands.MissingPermissions):
        msg = "You do not have permission to execute this command."
    elif isinstance(error, app_commands.MissingRole):
        msg = "You do not have the required role to execute this command."
    elif isinstance(error, app_commands.CheckFailure):
        return
    else:
        msg = "An error occurred while executing this command."

    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)
    except Exception:
        pass


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CheckFailure):
        return
    current_error = error
    for _ in range(3):
        if isinstance(current_error, discord.NotFound) and getattr(current_error, "code", None) == 10062:
            return
        next_error = getattr(current_error, "original", None)
        if next_error is None or next_error is current_error:
            break
        current_error = next_error
    raise error


# ---------------------------------------------------------
# Ready Event
# ---------------------------------------------------------
@bot.event
async def on_ready() -> None:
    if GUILD_ID:
        try:
            await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"Synced slash commands to guild: {GUILD_ID}")
        except Exception as e:
            print(f"Failed to sync command tree: {e}")

    await bot.change_presence(
        status=discord.Status.do_not_disturb,
        activity=discord.Game(name="/download")
    )

    print(f"Logged in as {bot.user}")


# ---------------------------------------------------------
# Network Watchdog & Auto-Reconnect Loop
# Prevents application crash when internet connection drops
# ---------------------------------------------------------
def is_internet_available() -> bool:
    endpoints = [("8.8.8.8", 53), ("1.1.1.1", 53), ("gateway.discord.gg", 443)]
    for host, port in endpoints:
        try:
            sock = socket.create_connection((host, port), timeout=3.0)
            sock.close()
            return True
        except (OSError, socket.gaierror, TimeoutError):
            continue
    return False


async def wait_for_internet_connection(check_interval: int = 5):
    loop = asyncio.get_running_loop()
    logged = False
    while True:
        connected = await loop.run_in_executor(None, is_internet_available)
        if connected:
            if logged:
                print("Internet connection detected! Restoring connection to Discord...")
            break
        if not logged:
            print("Internet connection lost. Waiting for connection to restore before reconnecting...")
            logged = True
        await asyncio.sleep(check_interval)


async def main():
    if not TOKEN:
        raise ValueError("TOKEN is not configured in .env file.")

    reconnect_delay = 5
    while True:
        try:
            async with bot:
                await bot.start(TOKEN)
        except (
            discord.ConnectionClosed,
            discord.GatewayNotFound,
            discord.HTTPException,
            aiohttp.ClientError,
            aiohttp.ClientConnectorError,
            aiohttp.ClientOSError,
            socket.gaierror,
            asyncio.TimeoutError,
            OSError,
        ) as net_err:
            print(f"Connection lost ({type(net_err).__name__}: {net_err}).")
            await wait_for_internet_connection(check_interval=5)
            print(f"Reconnecting in {reconnect_delay} seconds...")
            await asyncio.sleep(reconnect_delay)
        except Exception as err:
            print(f"Unexpected error: {type(err).__name__}: {err}. Waiting for network...")
            await wait_for_internet_connection(check_interval=5)
            await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot shutdown requested.")