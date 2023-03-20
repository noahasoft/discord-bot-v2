# This example requires the 'message_content' intent.

import asyncio
from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
import logging
import os
from aiogtts import aiogTTS
from typing import Optional
from audiofix import FFmpegPCMAudio

MY_GUILD = discord.Object(
    id=int(os.environ["DISCORD_GUILD"])
)  # replace with your guild id

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
aiogtts = aiogTTS()


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"), intents=intents
        )

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    # New role management functions
    async def create_role(self, guild: discord.Guild, name, color=None, permissions=None):
        color = discord.Color(int(color)) if color else discord.Color.default()
        permissions = discord.Permissions(permissions) if permissions else discord.Permissions(discord.Permissions.DEFAULT_VALUE)
        await guild.create_role(name=name, color=color, permissions=permissions)
        pass

    async def delete_role(self, role):
        await role.delete()

    async def add_role_to_member(self, member, role_name):
        role = get(member.guild.roles, name=role_name)
        if role:
            await member.add_roles(role)

    async def remove_role_from_member(self, member, role_name):
        role = get(member.guild.roles, name=role_name)
        if role:
            await member.remove_roles(role)


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


# This context menu command only works on members
@client.tree.context_menu(name="Show Join Date")
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f"{member} joined at {discord.utils.format_dt(member.joined_at)}"
    )


@client.tree.command()
async def create_role(interaction: discord.Interaction, role_name: str, role_color: str = None, role_permissions: int = None):
    """Create a new role with the specified name, color, and permissions."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You don't have permission to create roles.")
        return

    await client.create_role(interaction.guild, role_name, role_color, role_permissions)
    await interaction.response.send_message(f"Role '{role_name}' created successfully.")

@client.tree.command()
async def delete_role(interaction: discord.Interaction, role_name: str):
    """Delete a role with the specified name."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You don't have permission to delete roles.")
        return

    role = get(interaction.guild.roles, name=role_name)
    if not role:
        await interaction.response.send_message(f"Role '{role_name}' not found.")
        return

    await client.delete_role(role)
    await interaction.response.send_message(f"Role '{role_name}' deleted successfully.")

@client.tree.command()
async def add_role(interaction: discord.Interaction, member: discord.Member, role_name: str):
    """Add a role to a specified member."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You don't have permission to manage roles.")
        return

    await client.add_role_to_member(member, role_name)
    await interaction.response.send_message(f"Role '{role_name}' added to {member.name}.")

@client.tree.command()
async def remove_role(interaction: discord.Interaction, member: discord.Member, role_name: str):
    """Remove a role from a specified member."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You don't have permission to manage roles.")
        return

    await client.remove_role_from_member(member, role_name)
    await interaction.response.send_message(f"Role '{role_name}' removed from {member.name}.")


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

# Add this command to the bot script
@client.tree.command()
async def restart(interaction: discord.Interaction):
    """Restarts the bot."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to restart the bot.")
        return

    await interaction.response.send_message("Restarting the bot...")
    await client.close()

async def say_line(line: str, channel: discord.VoiceChannel):
    io = BytesIO()

    # await aiogtts.save(line, "join.mp3")
    await aiogtts.write_to_fp(line, io)
    io.seek(0)

    voice_guild = channel.guild
    if voice_guild is not None:
        voice_channel = await channel.connect()

        voice_channel.play(FFmpegPCMAudio(io.read(), pipe=True))

        while voice_channel.is_playing():
            await asyncio.sleep(1)

        await voice_channel.disconnect()
    else:
        await channel.send("You need to join a voice channel first!")


client.run(os.environ["DISCORD_TOKEN"], log_handler=handler)
