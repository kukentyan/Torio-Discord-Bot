from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("bot.vc_recruit")

DATA_DIR = Path(__file__).parent.parent / "data"
CHANNELS_FILE = DATA_DIR / "vc_channels.json"

BUTTON_CUSTOM_ID = "vc:recruit_button"

VC_ROLE_ID = 1528715114461659196
OWNER_ROLE_ID = 1447409601107722372

COOLDOWN_SECONDS = 60
PANEL_REPOST_COOLDOWN = 15

_last_recruit_time: dict[int, float] = {}

class RecruitModal(discord.ui.Modal, title="VC Recruitment"):
    content = discord.ui.TextInput(
        label="Enter recruitment details",
        style=discord.TextStyle.paragraph,
        placeholder="e.g., LFG from 19:00!",
        max_length=500,
        required=True,
    )

    def __init__(self, target_vc: discord.VoiceChannel):
        super().__init__()
        self.target_vc = target_vc

    async def on_submit(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(VC_ROLE_ID)

        if role is None:
            await interaction.response.send_message(
                "The VC recruitment role is not configured correctly. Check VC_ROLE_ID.",
                ephemeral=True,
            )
            return

        now = time.monotonic()
        last_time = _last_recruit_time.get(interaction.user.id)
        if last_time is not None and (now - last_time) < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_time))
            await interaction.response.send_message(
                f"Rate limited. Please wait {remaining} seconds before recruiting again.",
                ephemeral=True,
            )
            return

        if len(self.target_vc.members) > 0:
            await interaction.response.send_message(
                "Cannot recruit: The selected VC channel is currently occupied.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            description=f"**Target VC:** {self.target_vc.mention}\n\n{self.content.value}",
            color=discord.Color.green(),
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.channel.send(
            content=role.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        
        _last_recruit_time[interaction.user.id] = now
        
        await interaction.response.edit_message(
            content="Recruitment posted successfully.", view=None
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception("An error occurred within the VC recruitment modal", exc_info=error)
        if interaction.response.is_done():
            await interaction.followup.send(
                "An error occurred during submission. Please try again.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "An error occurred during submission. Please try again.", ephemeral=True
            )


class VCRecruitSelect(discord.ui.Select):
    def __init__(self, voice_channels: list[discord.VoiceChannel]):
        options = [
            discord.SelectOption(label=vc.name, value=str(vc.id))
            for vc in voice_channels[:25]
        ]
        super().__init__(
            placeholder="Select a VC to recruit for...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_id = int(self.values[0])
        actual_vc = interaction.guild.get_channel(selected_id)

        if not isinstance(actual_vc, discord.VoiceChannel):
            await interaction.response.send_message(
                "Invalid selection or channel no longer exists.", ephemeral=True
            )
            return

        await interaction.response.send_modal(RecruitModal(target_vc=actual_vc))


class EphemeralVCView(discord.ui.View):
    def __init__(self, voice_channels: list[discord.VoiceChannel]):
        super().__init__(timeout=300)
        self.add_item(VCRecruitSelect(voice_channels))


class VCRecruitView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Recruit for VC",
        style=discord.ButtonStyle.success,
        custom_id=BUTTON_CUSTOM_ID,
    )
    async def recruit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        vcs = [vc for vc in interaction.guild.voice_channels]
        if not vcs:
            await interaction.response.send_message(
                "No Voice Channels are available in this server.", ephemeral=True
            )
            return
            
        view = EphemeralVCView(vcs)
        await interaction.response.send_message(
            "Please select the target VC from the dropdown below:",
            view=view,
            ephemeral=True
        )


class VCRecruit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.vc_channels: dict[int, int] = {}
        self._locks: dict[int, asyncio.Lock] = {}
        self._last_repost: dict[int, float] = {}
        self._load_data()

    def _get_lock(self, channel_id: int) -> asyncio.Lock:
        if channel_id not in self._locks:
            self._locks[channel_id] = asyncio.Lock()
        return self._locks[channel_id]

    async def cog_load(self):
        self.bot.add_view(VCRecruitView())

    def _load_data(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if CHANNELS_FILE.exists():
            try:
                raw = json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
                self.vc_channels = {int(k): int(v) for k, v in raw.items()}
            except Exception:
                logger.exception("Failed to load vc_channels.json")
                self.vc_channels = {}

    def _save_channels(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        CHANNELS_FILE.write_text(
            json.dumps(
                {str(k): v for k, v in self.vc_channels.items()},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    async def _repost_panel(self, channel: discord.TextChannel):
        now = time.monotonic()
        last_repost = self._last_repost.get(channel.id)
        if last_repost is not None and now - last_repost < PANEL_REPOST_COOLDOWN:
            return

        lock = self._get_lock(channel.id)
        if lock.locked():
            return

        async with lock:
            now = time.monotonic()
            last_repost = self._last_repost.get(channel.id)
            if last_repost is not None and now - last_repost < PANEL_REPOST_COOLDOWN:
                return

            old_message_id = self.vc_channels.get(channel.id)
            if old_message_id:
                try:
                    old_message = await channel.fetch_message(old_message_id)
                    await old_message.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass
                except discord.HTTPException:
                    logger.exception("Failed to delete the old panel message")

            try:
                embed = discord.Embed(
                    title="VC Recruitment",
                    description="Click the button below to recruit for VC.",
                    color=discord.Color.green()
                )
                new_message = await channel.send(
                    embed=embed,
                    view=VCRecruitView(),
                )
            except discord.Forbidden:
                logger.warning(f"Lacking permissions to send messages in channel {channel.id}")
                return

            self.vc_channels[channel.id] = new_message.id
            self._last_repost[channel.id] = time.monotonic()
            self._save_channels()

    @commands.hybrid_command(name="vbchannel", description="Deploy the VC recruitment panel")
    @app_commands.guilds(discord.Object(id=os.getenv("GUILD_ID")))
    @app_commands.checks.has_role(OWNER_ROLE_ID)
    @commands.has_role(OWNER_ROLE_ID)
    @commands.guild_only()
    async def vbchannel(self, ctx: commands.Context):
        await self._repost_panel(ctx.channel)

    @vbchannel.error
    async def vbchannel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Administrator privileges are required to execute this command.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command can only be used within a server.")
        else:
            raise error

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.channel.id not in self.vc_channels:
            return
        if message.id == self.vc_channels.get(message.channel.id):
            return
        await self._repost_panel(message.channel)


async def setup(bot: commands.Bot):
    await bot.add_cog(VCRecruit(bot))