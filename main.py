import discord
from discord import app_commands
from discord.ext import commands
import os
import time

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1447408228798304359
ALLOWED_CHANNEL_ID = 1478624166126026813

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


global_cooldown = commands.CooldownMapping.from_cooldown(
    2, 1.0, commands.BucketType.default
)

@bot.check
async def global_checks(ctx):
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        await ctx.send(
            "Use commands in the bot channel only.\n<#1478624166126026813>",
            ephemeral=True
        )
        return False

    bucket = global_cooldown.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()

    if retry_after:
        await ctx.send(
            f"Please wait {retry_after:.1f}s before using another command.",
            ephemeral=True
        )
        return False

    return True

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        return
    raise error

@bot.event
async def on_ready() -> None:
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user}")


@bot.hybrid_command(name="ping", description="ping!")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


@bot.hybrid_command(name="boosters", description="Display the list of server boosters")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def boosters(ctx):
    guild = ctx.guild
    booster_list = guild.premium_subscribers

    embed = discord.Embed(
        title="<a:ServerBoost:1483456396371427369> Server Boosters <a:ServerBoost:1483456396371427369>",
        color=0x9B59B6
    )

    if not booster_list:
        embed.description = "There are currently no boosters."
    else:
        boosters_text = "\n".join(
            [f"{member.mention} (`{member.name}`)" for member in booster_list]
        )
        embed.description = boosters_text
        booster_count = len(booster_list)
        booster_word = "booster" if booster_count == 1 else "boosters"
        embed.set_footer(text=f"Total {booster_count} {booster_word} • Nitro Boost Tier {guild.premium_tier}")

    await ctx.send(embed=embed)


class FeatureSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="FullBright", description="Visual Module", value="fullbright"),
            discord.SelectOption(label="Zoom", description="Visual Module", value="zoom"),
            discord.SelectOption(label="Coordinates", description="Visual Module", value="coordinates"),
            discord.SelectOption(label="No Hurt Cam", description="Visual Module", value="nohurtcam"),
            discord.SelectOption(label="TrueSight", description="Visual Module", value="truesight"),
            discord.SelectOption(label="TimeChanger", description="Visual Module", value="timechanger"),
            discord.SelectOption(label="Reach", description="Combat Module", value="reach"),
            discord.SelectOption(label="AutoClicker", description="Combat Module", value="autoclicker"),
            discord.SelectOption(label="Hitbox", description="Combat Module", value="hitbox"),
            discord.SelectOption(label="Micro Aim", description="Combat Module", value="microaim"),
            discord.SelectOption(label="Trigger Bot", description="Combat Module", value="triggerbot"),
            discord.SelectOption(label="Aim Assist", description="Combat Module", value="aimassist"),
            discord.SelectOption(label="ToggleSprint", description="Movement Module", value="togglesprint"),
            discord.SelectOption(label="Speed", description="Movement Module", value="speed"),
            discord.SelectOption(label="JumpReset", description="Movement Module", value="jumpreset"),
            discord.SelectOption(label="AntiKnockback", description="Movement Module", value="antiknockback"),
            discord.SelectOption(label="Stream Protect", description="Misc Module", value="streamprotect"),
            discord.SelectOption(label="SystemTray", description="Misc Module", value="systemtray"),
        ]
        super().__init__(placeholder="Select a module to learn more...", options=options)

    async def callback(self, interaction: discord.Interaction):
        details = {
            "fullbright": {
                "title": "FullBright",
                "desc": "Keeps the world fully illuminated at all times.\nNo more dark caves or night-time visibility issues.",
                "category": "Visual Module"
            },
            "zoom": {
                "title": "Zoom",
                "desc": "Adjustable zoom for clearer long-distance vision.\nPerfect for scouting or checking distant locations.",
                "category": "Visual Module"
            },
            "coordinates": {
                "title": "Coordinates",
                "desc": "Displays your current XYZ coordinates on screen.\nAlways know exactly where you are.",
                "category": "Visual Module"
            },
            "nohurtcam": {
                "title": "No Hurt Cam",
                "desc": "Disables the hurt camera shake effect when taking damage.\n⚠️ 1.21.130~1.21.132 Only. On v26, use the in-game settings instead.",
                "category": "Visual Module"
            },
            "truesight": {
                "title": "TrueSight",
                "desc": "Makes all invisible entities fully visible, including players, mobs, and effects.",
                "category": "Visual Module"
            },
            "timechanger": {
                "title": "TimeChanger",
                "desc": "Freely change the in-game time client-side.\nUseful for better visibility or aesthetics.",
                "category": "Visual Module"
            },
            "reach": {
                "title": "Reach",
                "desc": "Extends melee attack distance.\nHit enemies before they can hit you.",
                "category": "Combat Module"
            },
            "autoclicker": {
                "title": "AutoClicker",
                "desc": "Automates left and right clicks for combat and building.\nSupports both left-click and right-click automation.",
                "category": "Combat Module"
            },
            "hitbox": {
                "title": "Hitbox",
                "desc": "Expands entity hitboxes for easier targeting.\nLand hits more consistently on fast-moving targets.",
                "category": "Combat Module"
            },
            "microaim": {
                "title": "Micro Aim",
                "desc": "Automatically fine-tunes your sensitivity when manually aiming at an enemy.\nHelps your aim lock on smoothly without snapping.",
                "category": "Combat Module"
            },
            "triggerbot": {
                "title": "Trigger Bot",
                "desc": "Automatically attacks when your crosshair is over a target.\nSupports two switchable modes: **First Hit** and **Auto Click**.",
                "category": "Combat Module"
            },
            "togglesprint": {
                "title": "ToggleSprint",
                "desc": "Sprint without holding the sprint key.\nKeep sprinting hands-free at all times.",
                "category": "Movement Module"
            },
            "speed": {
                "title": "Speed",
                "desc": "Increases player movement speed.\nMove faster than normal across any terrain.",
                "category": "Movement Module"
            },
            "jumpreset": {
                "title": "JumpReset",
                "desc": "Automates jump reset timing during combat.\nStay on top of your combos without manual timing.",
                "category": "Movement Module"
            },
            "antiknockback": {
                "title": "AntiKnockback",
                "desc": "Reduces or prevents knockback from attacks.\nStay in position even when taking hits.",
                "category": "Movement Module"
            },
            "streamprotect": {
                "title": "Stream Protect",
                "desc": "Keeps the Torio Client window hidden during screen sharing or live streaming.\nYour viewers will never see the client — only you can.",
                "category": "Misc Module"
            },
            "systemtray": {
                "title": "SystemTray",
                "desc": "Access or close the Torio Client window directly from the system tray.\nNo need to alt-tab — you can also fully exit the client from here.",
                "category": "Misc Module"
            },
            "aimassist": {
                "title": "Aim Assist",
                "desc": "Helps you aim at targets by providing slight assistance.\nGreat for players who struggle with precise aiming.",
                "category": "Combat Module"
            },
        }

        selected = self.values[0]
        info = details[selected]

        embed = discord.Embed(
            title=info["title"],
            description=info["desc"],
            color=0x5865F2
        )
        embed.set_footer(text=info["category"])

        await interaction.response.edit_message(embed=embed, view=self.view)

class FeatureView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.cooldowns = {}

        self.add_item(FeatureSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This menu can only be used by the person who ran the command.",
                ephemeral=True
            )
            return False

        user_id = interaction.user.id
        now = time.time()

        last = self.cooldowns.get(user_id, 0)

        if now - last < 2:
            wait = round(2 - (now - last), 1)

            await interaction.response.send_message(
                f"Please wait {wait}s before using the menu again.",
                ephemeral=True
            )
            return False

        self.cooldowns[user_id] = now
        return True

@bot.hybrid_command(name="features", description="Display all features of Torio Client")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def features(ctx):
    embed = discord.Embed(
        title="Torio Client — Features",
        description="Select a module from the list below to see its details.",
        color=0x5865F2
    )
    embed.add_field(name="Visual", value="FullBright, Zoom, Coordinates, No Hurt Cam, TrueSight, TimeChanger", inline=False)
    embed.add_field(name="Combat", value="Reach, AutoClicker, Hitbox, Micro Aim, Trigger Bot, Aim Assist", inline=False)
    embed.add_field(name="Movement", value="ToggleSprint, Speed, JumpReset, AntiKnockback", inline=False)
    embed.add_field(name="Misc", value="Stream Protect, SystemTray", inline=False)

    await ctx.send(embed=embed, view=FeatureView(ctx.author.id))

@bot.hybrid_command(name="invite", description="Get the invite link for the Torio Client support server")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def invite(ctx):
    embed = discord.Embed(
        title="Join the TorioGhost Client Server!",
        description="Get support, report bugs, \nand connect with other users in our official Discord server.",
        color=0x5865F2
    )
    embed.add_field(name="Invite Link https://discord.gg/xq8sWQhuXG", value="**[Join Here](https://discord.gg/xq8sWQhuXG)**", inline=False)

    await ctx.send(embed=embed)

@bot.hybrid_command(name="download", description="Get the download link for the Torio Client")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def download(ctx):
    embed = discord.Embed(
        title="Download Torio Client<:TorioLogo:1483456665222123530>",
        description="Click the link below to download the latest release of the Torio Client.",
        color=0x5865F2
    )
    embed.add_field(name="GitHub Releases", value="**[Download Here](https://github.com/Uncle-Awrt/Torio-Client/releases)**", inline=False)

    await ctx.send(embed=embed)

bot.run(TOKEN)