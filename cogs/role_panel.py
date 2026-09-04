from __future__ import annotations

import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("bot.role_panel")

ROLE_OPTIONS = [
    {
        "role_id": 1447827414024716431,
        "label": "Updates Role",
        "description": "Select to acquire Updates Role",
    },
    {
        "role_id": 1528715114461659196,
        "label": "VC Ping Role",
        "description": "Select to acquire VC Ping Role",
    },
]

SELECT_CUSTOM_ID = "role_panel:select"
OWNER_ROLE_ID = 1447409601107722372

class RolePanelSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=opt["label"],
                value=str(opt["role_id"]),
                description=opt.get("description") or None,
            )
            for opt in ROLE_OPTIONS
        ]
        super().__init__(
            placeholder="Select desired roles...",
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id=SELECT_CUSTOM_ID,
        )

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        guild = interaction.guild

        if not isinstance(member, discord.Member) or not guild:
            return

        selected_ids = {int(v) for v in self.values}
        panel_role_ids = {opt["role_id"] for opt in ROLE_OPTIONS}
        current_ids = {r.id for r in member.roles}

        to_add_ids = selected_ids - current_ids
        to_remove_ids = (panel_role_ids - selected_ids) & current_ids

        to_add = [guild.get_role(rid) for rid in to_add_ids if guild.get_role(rid)]
        to_remove = [guild.get_role(rid) for rid in to_remove_ids if guild.get_role(rid)]

        try:
            if to_add:
                await member.add_roles(*to_add, reason="Role Panel Select")
            if to_remove:
                await member.remove_roles(*to_remove, reason="Role Panel Deselect")
        except discord.Forbidden:
            await interaction.response.send_message(
                "Lacking permissions to manage roles. Check Bot hierarchy.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            logger.exception("Failed to modify roles via panel.")
            await interaction.response.send_message(
                "An error occurred. Please try again.", ephemeral=True
            )
            return

        await interaction.response.defer()


class RolePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RolePanelSelect())


class RolePanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(RolePanelView())

    @commands.hybrid_command(name="grolepannel", description="Deploy the role selection panel")
    @app_commands.guilds(discord.Object(id=os.getenv("GUILD_ID")))
    @app_commands.checks.has_role(OWNER_ROLE_ID)
    @commands.has_role(OWNER_ROLE_ID)
    @commands.guild_only()
    async def grolepannel(self, ctx: commands.Context):
        """Deploys the role selection panel in the current channel"""
        embed = discord.Embed(
            title="Get Roles",
            description=(
                "Please select the roles you wish to acquire from the menu below.\n"
                "Selecting a role will add it, and deselecting will remove it."
            ),
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=RolePanelView())

    @grolepannel.error
    async def grolepannel_error(self, ctx: commands.Context, error):
        is_ephemeral = bool(ctx.interaction)
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Administrator privileges are required.", ephemeral=is_ephemeral)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(RolePanel(bot))