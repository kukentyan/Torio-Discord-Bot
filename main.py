import asyncio
import os
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv

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

global_cooldown = commands.CooldownMapping.from_cooldown(
    2, 1.0, commands.BucketType.default
)


@bot.check
async def global_checks(ctx: commands.Context):
    if ctx.command and ctx.command.name in [
        "vbchannel", "grolepannel", "translate", "supportsetup"
    ]:
        return True

    if ALLOWED_CHANNEL_ID and ctx.channel.id != int(ALLOWED_CHANNEL_ID):
        redirect_msg = f"Use commands in the bot channel only."
        if BOTCHANNELID:
            redirect_msg += f"\n{BOTCHANNELID}"
        await ctx.send(redirect_msg, delete_after=5.0)
        return False

    bucket = global_cooldown.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()

    if retry_after:
        await ctx.send(
            f"Please wait {retry_after:.1f}s before using another command.",
            delete_after=5.0
        )
        return False

    return True


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


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("TOKEN is not configured in .env file.")
    bot.run(TOKEN)