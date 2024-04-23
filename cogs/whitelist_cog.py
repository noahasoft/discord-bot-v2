import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite


@app_commands.guild_only()
class WhitelistCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot

    async def cog_load(self) -> None:
        await self.create_whitelist_table()
        await super().cog_load()

    @app_commands.command()
    async def whitelist(self, interaction: discord.Interaction, user: discord.User):
        """Adds a user to the whitelist."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You don't have permission to manage the whitelist."
            )
            return

        await self.add_user_to_whitelist(user.id)
        await interaction.response.send_message(
            f"{user.mention} has been added to the whitelist."
        )

    @app_commands.command()
    async def unwhitelist(self, interaction: discord.Interaction, user: discord.User):
        """Removes a user from the whitelist."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You don't have permission to manage the whitelist."
            )
            return

        await self.remove_user_from_whitelist(user.id)
        await interaction.response.send_message(
            f"{user.mention} has been removed from the whitelist."
        )

    @app_commands.command()
    async def print_whitelist(self, interaction: discord.Interaction):
        """Prints the whitelist."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You don't have permission to manage the whitelist."
            )
            return

        whitelist_ids = await self.get_whitelist()
        whitelist = [
            f"`{user.name}`"
            if (user := self.bot.get_user(user_id[0])) is not None
            else "Unknown User"
            for user_id in whitelist_ids
        ]
        repsonse = "Whitelist:\n----------------\n" + "\n".join(whitelist)
        await interaction.response.send_message(repsonse)

    # Database methods
    async def create_whitelist_table(self):
        async with aiosqlite.connect("whitelist.db") as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS whitelist (user_id INTEGER PRIMARY KEY)"
            )
            await db.commit()

    async def is_user_whitelisted(self, user_id: int) -> bool:
        async with aiosqlite.connect("whitelist.db") as db:
            cursor = await db.execute(
                "SELECT user_id FROM whitelist WHERE user_id = ?", (user_id,)
            )
            result = await cursor.fetchone()
            return result is not None

    async def add_user_to_whitelist(self, user_id: int):
        async with aiosqlite.connect("whitelist.db") as db:
            await db.execute(
                "INSERT OR IGNORE INTO whitelist (user_id) VALUES (?)", (user_id,)
            )
            await db.commit()

    async def remove_user_from_whitelist(self, user_id: int):
        async with aiosqlite.connect("whitelist.db") as db:
            await db.execute("DELETE FROM whitelist WHERE user_id = ?", (user_id,))
            await db.commit()

    async def get_whitelist(self) -> list:
        async with aiosqlite.connect("whitelist.db") as db:
            cursor = await db.execute("SELECT user_id FROM whitelist")
            result = await cursor.fetchall()
            return list(result)
