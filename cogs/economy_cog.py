import datetime
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite


@app_commands.guild_only()
class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.daily_value = 100
        self.passive_value = 10

    async def cog_load(self) -> None:
        await self.create_economy_table()
        await self.sync_members()
        self.daily.start()
        self.passive_income.start()
        self.scheduled_sync.start()
        await super().cog_load()

    async def sync_members(self):
        for user in self.bot.get_all_members():
            await self.create_if_not_exists(user.id)

    async def cog_unload(self) -> None:
        self.daily.stop()
        self.passive_income.stop()
        self.scheduled_sync.stop()
        await super().cog_unload()

    @app_commands.command()
    async def balance(self, interaction: discord.Interaction):
        """Prints the user's balance."""
        balance = await self.get_balance(interaction.user.id)
        await interaction.response.send_message(f"Balance: {balance}")

    @app_commands.command()
    async def leaderboard(self, interaction: discord.Interaction):
        """Prints the server's leaderboard."""
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute(
                "SELECT user_id, balance FROM economy ORDER BY balance DESC LIMIT 10"
            ) as cursor:
                response = "Leaderboard:\n----------------\n"
                for row in await cursor.fetchall():
                    user = self.bot.get_user(row[0])
                    response += f"`{user.name}`: ${row[1]:.2f}\n"
                await interaction.response.send_message(response)

    @tasks.loop(time=datetime.time(hour=8, tzinfo=datetime.timezone.utc))
    async def daily(self):
        for user_id in await self.get_registered_users():
            try:
                await self.deposit_money(user_id, self.passive_value)
            except Exception as e:
                print(f"Failed to deposit daily money for {user_id}: {str(e)}")

    @tasks.loop(minutes=15)
    async def scheduled_sync(self):
        await self.sync_members()

    @tasks.loop(minutes=10)
    async def passive_income(self):
        # iterate over all visible members, check if they're in voice, and give them money
        for member in self.bot.get_all_members():
            print(
                f"Checking member: {member.name} (ID: {member.id}) for passive income."
            )
            if member.voice and member.voice.channel is not None:
                try:
                    await self.deposit_money(member.id, self.passive_value)
                except Exception as e:
                    print(f"Failed to deposit passive money for {member.id}: {str(e)}")

    async def get_registered_users(self):
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute("SELECT user_id FROM economy") as cursor:
                return [row[0] async for row in cursor]

    async def create_economy_table(self):
        async with aiosqlite.connect("economy.db") as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS economy (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)"
            )
            await db.commit()

    async def create_if_not_exists(self, user_id: int):
        async with aiosqlite.connect("economy.db") as db:
            await db.execute(
                "INSERT OR IGNORE INTO economy (user_id, balance) VALUES (?, ?)",
                (user_id, 0),
            )
            await db.commit()

    async def get_balance(self, user_id: int) -> int:
        await self.create_if_not_exists(user_id)
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute(
                "SELECT balance FROM economy WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row is not None else 0

    async def withdraw_money(self, user_id: int, amount: int):
        await self.create_if_not_exists(user_id)
        async with aiosqlite.connect("economy.db") as db:
            await db.execute(
                "UPDATE economy SET balance = balance - ? WHERE user_id = ?",
                (amount, user_id),
            )
            await db.commit()

    async def deposit_money(self, user_id: int, amount: int):
        await self.create_if_not_exists(user_id)
        async with aiosqlite.connect("economy.db") as db:
            await db.execute(
                "UPDATE economy SET balance = balance + ? WHERE user_id = ?",
                (amount, user_id),
            )
            await db.commit()
