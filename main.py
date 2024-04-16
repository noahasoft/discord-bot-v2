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
import aiosqlite
import aiohttp

from cogs.joined_cog import JoinedCog
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
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def create_role(
        self, guild: discord.Guild, name, color=None, permissions=None
    ):
        color = discord.Color(int(color)) if color else discord.Color.default()
        permissions = (
            discord.Permissions(permissions)
            if permissions
            else discord.Permissions(discord.Permissions.DEFAULT_VALUE)
        )
        await guild.create_role(name=name, color=color, permissions=permissions)

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


@client.tree.command()
async def create_role(
    interaction: discord.Interaction,
    role_name: str,
    role_color: str = None,
    role_permissions: int = None,
):
    """Create a new role with the specified name, color, and permissions."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "You don't have permission to create roles."
        )
        return

    await client.create_role(interaction.guild, role_name, role_color, role_permissions)
    await interaction.response.send_message(f"Role '{role_name}' created successfully.")


@client.tree.command()
async def delete_role(interaction: discord.Interaction, role_name: str):
    """Delete a role with the specified name."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "You don't have permission to delete roles."
        )
        return

    role = get(interaction.guild.roles, name=role_name)
    if not role:
        await interaction.response.send_message(f"Role '{role_name}' not found.")
        return

    await client.delete_role(role)
    await interaction.response.send_message(f"Role '{role_name}' deleted successfully.")


@client.tree.command()
async def add_role(
    interaction: discord.Interaction, member: discord.Member, role_name: str
):
    """Add a role to a specified member."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "You don't have permission to manage roles."
        )
        return

    await client.add_role_to_member(member, role_name)
    await interaction.response.send_message(
        f"Role '{role_name}' added to {member.name}."
    )


@client.tree.command()
async def remove_role(
    interaction: discord.Interaction, member: discord.Member, role_name: str
):
    """Remove a role from a specified member."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "You don't have permission to manage roles."
        )
        return

    await client.remove_role_from_member(member, role_name)
    await interaction.response.send_message(
        f"Role '{role_name}' removed from {member.name}."
    )


@client.tree.command()
async def restart(interaction: discord.Interaction):
    """Restarts the bot."""
    if not await is_user_whitelisted(
        interaction.user.id
    ):  # Check if the user is whitelisted
        await interaction.response.send_message(
            "You are not whitelisted to restart the bot."
        )
        return

    await interaction.response.send_message("Bot restarting, please wait.")
    await client.close()


client.run(os.environ["DISCORD_TOKEN"], log_handler=handler)
