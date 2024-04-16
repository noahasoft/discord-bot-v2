import discord
from discord.ext import commands
import logging
import os

from cogs.casino_cog import CasinoCog
from cogs.economy_cog import EconomyCog
from cogs.joined_cog import JoinedCog
from cogs.role_cog import RoleCog
from cogs.utilities_cog import UtilitiesCog
from cogs.voice_cog import VoiceCog
from cogs.whitelist_cog import WhitelistCog

MY_GUILD = discord.Object(id=int(os.environ["DISCORD_GUILD"]))

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"), intents=intents
        )

    async def setup_hook(self):
        await self.add_cog(JoinedCog(self))
        await self.add_cog(VoiceCog(self))
        await self.add_cog(WhitelistCog(self))
        await self.add_cog(RoleCog(self))
        await self.add_cog(EconomyCog(self))
        await self.add_cog(UtilitiesCog(self))
        await self.add_cog(CasinoCog(self))
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


client = MyBot()


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    print("------")


@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f"Hi, {interaction.user.mention}")


client.run(os.environ["DISCORD_TOKEN"], log_handler=handler)
