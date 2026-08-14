import os
import discord
from discord import app_commands
from discord.ext import commands
from utils.i18n import get_user_locale, get_text

GUILD_ID = os.getenv("GUILD_ID")
SERVERBOOST = os.getenv("SERVERBOOST", "🚀")


class WebsiteView(discord.ui.View):
    def __init__(self, button_label: str):
        super().__init__()
        self.add_item(discord.ui.Button(
            label=button_label,
            url="https://uncle-awrt.github.io/Torio-Client-Website/",
            style=discord.ButtonStyle.link
        ))


class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check bot latency")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.hybrid_command(name="boosters", description="Display the list of server boosters")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def boosters(self, ctx: commands.Context):
        guild = ctx.guild
        booster_list = guild.premium_subscribers if guild else []
        locale = get_user_locale(ctx)
        t = get_text("boosters", locale)

        embed = discord.Embed(
            title=f"{SERVERBOOST} {t.get('title', 'Server Boosters')} {SERVERBOOST}",
            color=0x9B59B6
        )

        if not booster_list:
            embed.description = t.get("no_boosters", "There are currently no boosters.")
        else:
            boosters_text = "\n".join(
                [f"{member.mention} (`{member.name}`)" for member in booster_list]
            )
            embed.description = boosters_text
            booster_count = len(booster_list)
            booster_word = "booster" if booster_count == 1 else "boosters"
            footer_text = t.get("footer", "Total {count} {word} • Nitro Boost Tier {tier}").format(
                count=booster_count,
                word=booster_word,
                tier=guild.premium_tier if guild else 0
            )
            embed.set_footer(text=footer_text)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="members", aliases=["membercount"], description="Display current server member statistics")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def members(self, ctx: commands.Context):
        guild = ctx.guild
        if not guild:
            await ctx.send("This command can only be used in a server.", ephemeral=True)
            return

        locale = get_user_locale(ctx)
        t = get_text("members", locale)

        total_members = guild.member_count or len(guild.members)
        bots = sum(1 for m in guild.members if m.bot)
        humans = total_members - bots
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)

        embed = discord.Embed(
            title=t.get("title", "Server Member Statistics"),
            description=t.get("description", "Current member statistics for **{server_name}**.").format(
                server_name=guild.name
            ),
            color=0x5865F2
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name=t.get("total", "Total Members"), value=f"**{total_members:,}**", inline=True)
        embed.add_field(name=t.get("humans", "Humans"), value=f"**{humans:,}**", inline=True)
        embed.add_field(name=t.get("bots", "Bots"), value=f"**{bots:,}**", inline=True)
        embed.add_field(name=t.get("online", "Online"), value=f"**{online_members:,}**", inline=True)

        embed.set_footer(text=t.get("footer", "Torio Client Official Community"))
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="invite", description="Get the invite link for the Torio Client support server")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def invite(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Join the TorioGhost Client Server!",
            description="Get support, report bugs, \nand connect with other users in our official Discord server.",
            color=0x5865F2
        )
        embed.add_field(
            name="Invite Link https://discord.gg/xq8sWQhuXG",
            value="**[Join Here](https://discord.gg/xq8sWQhuXG)**",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="website", description="Get the official website link for Torio Client")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def website(self, ctx: commands.Context):
        locale = get_user_locale(ctx)
        t = get_text("website", locale)

        embed = discord.Embed(
            title=t.get("title", "Torio Client — Official Website"),
            description=t.get("description", "Click the link below to visit the official Torio Client website."),
            color=0x5865F2
        )
        embed.add_field(
            name="Official Website",
            value="**[uncle-awrt.github.io/Torio-Client-Website](https://uncle-awrt.github.io/Torio-Client-Website/)**",
            inline=False
        )
        button_label = t.get("button", "Visit Website")
        await ctx.send(embed=embed, view=WebsiteView(button_label))

    @commands.hybrid_command(name="rules", description="Display the official server rules")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def rules(self, ctx: commands.Context):
        locale = get_user_locale(ctx)
        t = get_text("rules", locale)

        embed = discord.Embed(
            title=t.get("title", "Torio Client Server — Official Rules"),
            description=t.get("description", "Please read and follow our community rules."),
            color=0x5865F2
        )
        embed.add_field(name=t.get("field_name", "Server Rules"), value=t.get("rules", ""), inline=False)
        embed.set_footer(text=t.get("footer", ""))

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
