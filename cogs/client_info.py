import os
import time
import discord
from discord import app_commands
from discord.ext import commands
from utils.i18n import get_user_locale, get_text, get_modules

GUILD_ID = os.getenv("GUILD_ID")
TORIOLOGO = os.getenv("TORIOLOGO", "")


class CategoryModuleSelect(discord.ui.Select):
    def __init__(self, category="Visual Modules", locale="en"):
        self.category = category
        self.user_locale = locale
        modules = get_modules()
        options = []
        for key, info in modules.items():
            if info["category"] == category:
                label = info["title"].replace("*", "")
                options.append(
                    discord.SelectOption(
                        label=label[:100],
                        description=category[:100],
                        value=key
                    )
                )
        t = get_text("features", locale)
        ph = t.get("mod_select_ph", "Select a module...")
        super().__init__(placeholder=ph, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        modules = get_modules()
        info = modules[selected]
        locale = get_user_locale(interaction)

        desc = info.get(f"desc_{locale}", info["desc_en"])

        embed = discord.Embed(
            title=info["title"],
            description=desc,
            color=0x5865F2
        )
        embed.set_footer(text=info["category"])

        await interaction.response.edit_message(embed=embed, view=self.view)


class CategorySelect(discord.ui.Select):
    def __init__(self, locale="en"):
        self.user_locale = locale
        t = get_text("features", locale)
        options = [
            discord.SelectOption(
                label=t.get("cat_visual", "Visual Modules"),
                description="Fullbright, Zoom, ESP, TrueSight, etc.",
                value="Visual Modules"
            ),
            discord.SelectOption(
                label=t.get("cat_combat", "Combat Modules"),
                description="Reach, AutoClicker, Hitbox, Aim Assist, etc.",
                value="Combat Modules"
            ),
            discord.SelectOption(
                label=t.get("cat_movement", "Movement Modules"),
                description="Toggle Sprint, Velocity, Lag Switch, etc.",
                value="Movement Modules"
            ),
            discord.SelectOption(
                label=t.get("cat_utility", "Utility & Settings"),
                description="GUI Settings, Ingame Overlay, FakeLag, etc.",
                value="Utility & Settings"
            ),
        ]
        super().__init__(placeholder=t.get("cat_select_ph", "Select a category..."), options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        locale = get_user_locale(interaction)
        t = get_text("features", locale)
        modules = get_modules()

        category_modules = [
            info["title"].replace("*", "")
            for info in modules.values()
            if info["category"] == selected_category
        ]
        modules_text = ", ".join(category_modules)

        embed = discord.Embed(
            title=f"Torio Client — {selected_category}",
            description=f"{t.get('available_mods', '**Available Modules:**')}\n{modules_text}\n\n{t.get('select_below', '')}",
            color=0x5865F2
        )

        self.view.clear_items()
        self.view.add_item(CategorySelect(locale))
        self.view.add_item(CategoryModuleSelect(selected_category, locale))

        await interaction.response.edit_message(embed=embed, view=self.view)


class FeatureView(discord.ui.View):
    def __init__(self, author_id, current_category="Visual Modules", locale="en"):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.cooldowns = {}

        self.add_item(CategorySelect(locale))
        self.add_item(CategoryModuleSelect(current_category, locale))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        locale = get_user_locale(interaction)
        gen_t = get_text("general", locale)

        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                gen_t.get("menu_author_only", "This menu can only be used by the person who ran the command."),
                ephemeral=True
            )
            return False

        user_id = interaction.user.id
        now = time.time()
        last = self.cooldowns.get(user_id, 0)

        if now - last < 2:
            wait = round(2 - (now - last), 1)
            msg = gen_t.get("menu_cooldown", "Please wait {wait}s before using the menu again.").format(wait=wait)
            await interaction.response.send_message(msg, ephemeral=True)
            return False

        self.cooldowns[user_id] = now
        return True


async def feature_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices = []
    modules = get_modules()
    for key, info in modules.items():
        title = info["title"].replace("*", "")
        if current.lower() in key or current.lower() in title.lower():
            choices.append(app_commands.Choice(name=title, value=key))
    return choices[:25]


class ClientInfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="features", description="Display all features of Torio Client")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def features(self, ctx: commands.Context):
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer()

        locale = get_user_locale(ctx)
        t = get_text("features", locale)
        modules = get_modules()

        embed = discord.Embed(
            title=t.get("title", "Torio Client — Features"),
            description=t.get("description", ""),
            color=0x5865F2
        )

        visuals = ", ".join([m["title"].replace("*", "") for m in modules.values() if m["category"] == "Visual Modules"])
        combats = ", ".join([m["title"].replace("*", "") for m in modules.values() if m["category"] == "Combat Modules"])
        movements = ", ".join([m["title"].replace("*", "") for m in modules.values() if m["category"] == "Movement Modules"])
        utilities = ", ".join([m["title"].replace("*", "") for m in modules.values() if m["category"] == "Utility & Settings"])

        embed.add_field(name=t.get("cat_visual", "Visual Modules"), value=visuals, inline=False)
        embed.add_field(name=t.get("cat_combat", "Combat Modules"), value=combats, inline=False)
        embed.add_field(name=t.get("cat_movement", "Movement Modules"), value=movements, inline=False)
        embed.add_field(name=t.get("cat_utility", "Utility & Settings"), value=utilities, inline=False)

        await ctx.send(embed=embed, view=FeatureView(ctx.author.id, locale=locale))

    @commands.hybrid_command(name="feature", description="Search details for a specific module of Torio Client")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.autocomplete(module=feature_autocomplete)
    async def feature(self, ctx: commands.Context, module: str):
        locale = get_user_locale(ctx)
        modules = get_modules()
        module_key = module.lower().replace(" ", "")
        info = modules.get(module_key)

        if not info:
            for key, val in modules.items():
                if module_key in key or module_key in val["title"].lower():
                    info = val
                    break

        if not info:
            gen_t = get_text("general", locale)
            not_found_msg = gen_t.get(
                "not_found",
                "Module `{module}` not found. Use `/features` to see all modules."
            ).format(module=module)
            await ctx.send(not_found_msg, ephemeral=True)
            return

        desc = info.get(f"desc_{locale}", info["desc_en"])

        embed = discord.Embed(
            title=info["title"],
            description=desc,
            color=0x5865F2
        )
        embed.set_footer(text=info["category"])
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="download", description="Get the download link for the Torio Client")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def download(self, ctx: commands.Context):
        locale = get_user_locale(ctx)
        t = get_text("download", locale)

        title = f"{t.get('title', 'Download Torio Client')} {TORIOLOGO}".strip()
        embed = discord.Embed(
            title=title,
            description=t.get("description", ""),
            color=0x5865F2
        )
        embed.add_field(
            name="GitHub Releases",
            value="**[Download Here](https://github.com/Uncle-Awrt/Torio-Client/releases)**",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="version", description="Look at what version of Minecraft Torio Client Supports")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def version(self, ctx: commands.Context):
        locale = get_user_locale(ctx)
        t = get_text("version", locale)

        embed = discord.Embed(
            title=t.get("title", "Torio Client — Version Information"),
            description=t.get("description", ""),
            color=0x5865F2
        )
        embed.add_field(
            name=t.get("field", "Supported Bedrock Versions"),
            value="26.0, 26.1, 26.2, 26.3, 26.10, 26.11, 26.12, 26.13, 26.20, 26.21, 26.30, 26.31, 26.32, 26.33, 26.40, 26.42",
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ClientInfoCog(bot))
