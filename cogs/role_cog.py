import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get


@app_commands.guild_only()
class RoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def create_role(
        self,
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

        await self.make_role(interaction.guild, role_name, role_color, role_permissions)
        await interaction.response.send_message(
            f"Role '{role_name}' created successfully."
        )

    @app_commands.command()
    async def delete_role(self, interaction: discord.Interaction, role_name: str):
        """Delete a role with the specified name."""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "You don't have permission to delete roles."
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(f"Role '{role_name}' not found.")
            return

        await role.delete()
        await interaction.response.send_message(
            f"Role '{role_name}' deleted successfully."
        )

    @app_commands.command()
    async def add_role(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role_name: str,
    ):
        """Add a role to a specified member."""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "You don't have permission to manage roles."
            )
            return

        await self.add_role_to_member(member, role_name)
        await interaction.response.send_message(
            f"Role '{role_name}' added to {member.name}."
        )

    @app_commands.command()
    async def remove_role(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role_name: str,
    ):
        """Remove a role from a specified member."""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "You don't have permission to manage roles."
            )
            return

        await self.remove_role_from_member(member, role_name)
        await interaction.response.send_message(
            f"Role '{role_name}' removed from {member.name}."
        )

    async def make_role(self, guild: discord.Guild, name, color=None, permissions=None):
        color = discord.Color(int(color)) if color else discord.Color.default()
        permissions = (
            discord.Permissions(permissions)
            if permissions
            else discord.Permissions(discord.Permissions.DEFAULT_VALUE)
        )
        await guild.create_role(name=name, color=color, permissions=permissions)

    async def add_role_to_member(self, member, role_name):
        role = get(member.guild.roles, name=role_name)
        if role:
            await member.add_roles(role)

    async def remove_role_from_member(self, member, role_name):
        role = get(member.guild.roles, name=role_name)
        if role:
            await member.remove_roles(role)
