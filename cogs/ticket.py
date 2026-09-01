from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("bot.ticket")

SETUP_CHANNEL_ID = 1544278267106951238
CATEGORY_ID = 1544278553649225778
OWNER_ROLE_ID = 1447409601107722372
SMOD_ROLE_ID = 1475101566473080885

OPEN_BUTTON_CUSTOM_ID = "ticket:open_button"
CLOSE_BUTTON_CUSTOM_ID = "ticket:close_button"

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_FILE = DATA_DIR / "ticket_channels.json"


class TicketOpenView(discord.ui.View):
    def __init__(self, cog: "Ticket"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Open private support",
        style=discord.ButtonStyle.primary,
        custom_id=OPEN_BUTTON_CUSTOM_ID,
    )
    async def open_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.cog.create_ticket_channel(interaction)


class TicketCloseView(discord.ui.View):
    def __init__(self, cog: "Ticket"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Close ticket",
        style=discord.ButtonStyle.danger,
        custom_id=CLOSE_BUTTON_CUSTOM_ID,
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return

        creator_id = self.cog.ticket_creators.get(channel.id)
        is_staff = interaction.user.guild_permissions.administrator
        is_creator = creator_id == interaction.user.id
        if not (is_staff or is_creator):
            await interaction.response.send_message(
                "You do not have permission to close this ticket.", ephemeral=True
            )
            return

        await interaction.response.send_message("Closing this ticket.", ephemeral=True)
        self.cog.ticket_creators.pop(channel.id, None)
        self.cog._save_data()
        try:
            await channel.delete(reason=f"Ticket closed by {interaction.user}")
        except discord.Forbidden:
            logger.warning("Missing permission to delete ticket channel %s", channel.id)


class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ticket_creators: dict[int, int] = {}
        self.panel_message_id: int | None = None
        self._create_lock = asyncio.Lock()
        self._load_data()

    async def cog_load(self):
        self.bot.add_view(TicketOpenView(self))
        self.bot.add_view(TicketCloseView(self))

    def _load_data(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not DATA_FILE.exists():
            return
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            self.ticket_creators = {int(channel): int(user) for channel, user in raw.items()}
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            logger.exception("Failed to load ticket data")
            self.ticket_creators = {}

    def _save_data(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(
            json.dumps(
                {str(channel): user for channel, user in self.ticket_creators.items()},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _find_user_ticket(self, guild: discord.Guild, user_id: int):
        for channel_id, creator_id in list(self.ticket_creators.items()):
            if creator_id != user_id:
                continue
            channel = guild.get_channel(channel_id)
            if channel is not None:
                return channel
            self.ticket_creators.pop(channel_id, None)
        self._save_data()
        return None

    async def create_ticket_channel(self, interaction: discord.Interaction):
        async with self._create_lock:
            await self._create_ticket_channel(interaction)

    async def _create_ticket_channel(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "This button can only be used in a server.", ephemeral=True
            )
            return

        is_owner = any(role.id == OWNER_ROLE_ID for role in interaction.user.roles)
        if interaction.user.premium_since is None and not is_owner:
            await interaction.response.send_message(
                "Private support is available to server boosters and Owners only.",
                ephemeral=True,
            )
            return

        existing_channel = self._find_user_ticket(guild, interaction.user.id)
        if existing_channel is not None:
            await interaction.response.send_message(
                f"You already have an open ticket: {existing_channel.mention}",
                ephemeral=True,
            )
            return

        category = guild.get_channel(CATEGORY_ID)
        if category is None:
            try:
                category = await guild.fetch_channel(CATEGORY_ID)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                category = None
        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message(
                "The configured ticket category could not be found. "
                "Check CATEGORY_ID and make sure it is a category visible to the bot.",
                ephemeral=True,
            )
            return

        username = re.sub(r"[^a-z0-9-]+", "-", interaction.user.name.lower()).strip("-")
        if not username:
            username = str(interaction.user.id)
        channel_name = f"support-{username}"[:100].rstrip("-")
        existing_names = {channel.name for channel in category.channels}
        if channel_name in existing_names:
            await interaction.response.send_message(
                "A private support channel with this username already exists.",
                ephemeral=True,
            )
            return

        bot_member = guild.me
        if bot_member is None:
            await interaction.response.send_message(
                "The bot member could not be found.", ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
            bot_member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                )

        smod_role = guild.get_role(SMOD_ROLE_ID)
        if smod_role is not None:
            overwrites[smod_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            )

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Private support ticket created by {interaction.user}",
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to create the ticket channel.", ephemeral=True
            )
            return

        self.ticket_creators[channel.id] = interaction.user.id
        self._save_data()
        await channel.send(
            f"{interaction.user.mention} Private support ticket. Describe your issue here.",
            view=TicketCloseView(self),
        )
        await interaction.response.send_message(
            f"Your private support channel was created: {channel.mention}",
            ephemeral=True,
        )

    @commands.hybrid_command(
        name="supportsetup", description="Set up the private support panel"
    )
    @app_commands.guilds(discord.Object(id=os.getenv("GUILD_ID")))
    @app_commands.checks.has_role(OWNER_ROLE_ID)
    @commands.has_role(OWNER_ROLE_ID)
    @commands.guild_only()
    async def supportsetup(self, ctx: commands.Context):
        channel = ctx.guild.get_channel(SETUP_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("The support setup channel is not configured correctly.")
            return

        embed = discord.Embed(
            title="Private Support",
            description=(
                "Server boosters can receive dedicated support here.\n\n"
                "Only Server boosters can open one private support ticket.\n\n"
                "Owners and SMODs are here to provide friendly and thorough support."
            ),
            color=discord.Color.blurple(),
        )
        await channel.send(embed=embed, view=TicketOpenView(self))
        await ctx.send(f"Private support panel posted in {channel.mention}")

    @supportsetup.error
    async def supportsetup_error(self, ctx: commands.Context, error):
        if isinstance(error, (commands.MissingRole, commands.MissingPermissions)):
            await ctx.send("You do not have permission to use this command.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command can only be used in a server.")
        else:
            raise error

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if channel.id in self.ticket_creators:
            self.ticket_creators.pop(channel.id, None)
            self._save_data()


async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))
