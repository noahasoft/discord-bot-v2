import discord
from discord import app_commands
from discord.ext import commands

from cogs.games.slots import SlotMachine


@app_commands.guild_only()
class CasinoCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.economy_cog = self.bot.get_cog("EconomyCog")
        self.slot_machine = SlotMachine.default()

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

        slot1, slot2, slot3 = self.slot_machine.pull_lever()
        response = f"{slot1} {slot2} {slot3}"

        if slot1 == slot2 == slot3:
            winnings = self.slot_machine.get_winnings(slot1, slot2, slot3, bet)
            await self.economy_cog.deposit_money(interaction.user.id, winnings)
            await interaction.response.send_message(
                f"{response}\Congratulations! You won {winnings}!"
            )
            self.jackpot_users.append(interaction.user.id)
        else:
            await self.economy_cog.withdraw_money(interaction.user.id, bet)
            self.lottery_jackpot += bet
            await interaction.response.send_message(
                f"{response}\nBetter luck next time! You lost {bet}."
            )
