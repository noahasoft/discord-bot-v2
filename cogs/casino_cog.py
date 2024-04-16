import random
import discord
from discord import app_commands
from discord.ext import commands, tasks

JACKPOT_DEFAULT = 1000


@app_commands.guild_only()
class CasinoCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.lottery_jackpot = JACKPOT_DEFAULT
        self.economy_cog = self.bot.get_cog("EconomyCog")

    async def cog_load(self) -> None:
        self.lottery.start()
        await super().cog_load()

    async def cog_unload(self) -> None:
        self.lottery.stop()
        await super().cog_unload()

    @app_commands.command()
    async def slots(self, interaction: discord.Interaction, bet: int):
        """Play the slots with the specified bet."""
        if bet < 1:
            await interaction.response.send_message("Bet must be at least 1.")
            return

        balance = await self.economy_cog.get_balance(interaction.user.id)
        if balance < bet:
            await interaction.response.send_message("Insufficient balance.")
            return

        slots = [
            ":apple:",
            ":banana:",
            ":cherries:",
            ":grapes:",
            ":lemon:",
            ":watermelon:",
        ]
        slot1, slot2, slot3 = [
            slots[i] for i in [random.randint(0, len(slots) - 1) for _ in range(3)]
        ]
        response = f"{slot1} {slot2} {slot3}"

        if slot1 == slot2 == slot3:
            await self.economy_cog.deposit_money(interaction.user.id, bet)
            await interaction.response.send_message(
                f"{response}\Congratulations! You won {bet}!"
            )
            self.jackpot_users.append(interaction.user.id)
        else:
            await self.economy_cog.withdraw_money(interaction.user.id, bet)
            self.lottery_jackpot += bet
            await interaction.response.send_message(
                f"{response}\nBetter luck next time! You lost {bet}."
            )

    @app_commands.command()
    async def lottery_jackpot(self, interaction: discord.Interaction):
        """Prints the current jackpot."""
        await interaction.response.send_message(f"Jackpot: {self.lottery_jackpot}")

    @tasks.loop(hours=168)
    async def lottery(self):
        users = await self.economy_cog.get_registered_users()
        winner = random.choice(users)
        await self.economy_cog.deposit_money(winner, self.lottery_jackpot)
        self.lottery_jackpot = JACKPOT_DEFAULT