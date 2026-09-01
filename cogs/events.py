import os
import time
import discord
from discord.ext import commands

WELCOME_CHANNEL_ID = os.getenv("WELCOME_CHANNEL_ID")


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._welcome_sent_at: dict[int, float] = {}

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not WELCOME_CHANNEL_ID:
            return

        now = time.monotonic()
        last_sent = self._welcome_sent_at.get(member.id)
        if last_sent is not None and now - last_sent < 10:
            return
        self._welcome_sent_at[member.id] = now

        channel = self.bot.get_channel(int(WELCOME_CHANNEL_ID))
        if channel is None:
            return

        embed = discord.Embed(
            description=f"Welcome {member.mention}!",
            color=0xFF73FA
        )

        embed.set_author(
            name=member.display_name,
            icon_url=member.display_avatar.url
        )

        embed.set_footer(text=f"User ID: {member.id}")

        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
