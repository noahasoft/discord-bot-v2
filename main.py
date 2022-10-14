# This example requires the 'message_content' intent.

import asyncio
from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands
import logging
import os
from aiogtts import aiogTTS
from typing import Optional


MY_GUILD = discord.Object(
    id=int(os.environ["DISCORD_GUILD"])
)  # replace with your guild id

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
aiogtts = aiogTTS()
io = BytesIO()


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"), intents=intents
        )
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        # self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
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


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(
    member="The member you want to get the joined date from; defaults to the user who uses the command"
)
async def joined(
    interaction: discord.Interaction, member: Optional[discord.Member] = None
):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f"{member} joined {discord.utils.format_dt(member.joined_at)}"
    )


# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.

# This context menu command only works on members
@client.tree.context_menu(name="Show Join Date")
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f"{member} joined at {discord.utils.format_dt(member.joined_at)}"
    )


@client.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    if member == client.user or member.bot:
        return

    # Leaving a voice channel or going afk
    if before.channel is not None:
        if after.channel is None:
            await depart_user(member, before.channel)
        elif after.channel == before.channel.guild.afk_channel:
            await afk_user(member, before.channel)

    # Joining a voice channel from no channel or afk
    if after.channel is not None and (before.channel is None or before.channel == before.channel.guild.afk_channel):
        await greet_user(member)


async def greet_user(member: discord.Member):
    await say_line(f"{member.name} has joined the channel", member.voice.channel)


async def depart_user(member: discord.Member, channel: discord.VoiceChannel):
    await say_line(f"{member.name} has left the channel", channel)


async def afk_user(member: discord.Member, channel: discord.VoiceChannel):
    await say_line(f"{member.name} went afk", channel)


async def say_line(line: str, channel: discord.VoiceChannel):
    await aiogtts.save(line, "join.mp3")

    voice_guild = channel.guild
    if voice_guild is not None:
        voice_channel = await channel.connect()

        voice_channel.play(discord.FFmpegPCMAudio("join.mp3"))

        while voice_channel.is_playing():
            await asyncio.sleep(1)

        await voice_channel.disconnect()
    else:
        await channel.send("You need to join a voice channel first!")


client.run(os.environ["DISCORD_TOKEN"], log_handler=handler)
