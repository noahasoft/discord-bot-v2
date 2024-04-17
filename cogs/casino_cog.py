import discord
from discord import app_commands
from discord.ext import commands

from cogs.games.slots import (
    PayRule,
    Payline,
    GameBase,
    Machine,
    Symbol,
    Reelstrip,
    Window,
)


@app_commands.guild_only()
class CasinoCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.economy_cog = self.bot.get_cog("EconomyCog")
        self.slot_machine = Machine(
            [
                GameBase(
                    "g01",
                    [Payline([1, 1, 1])],
                    [PayRule(3, 2.0)],
                    [
                        Reelstrip(
                            [
                                Symbol(":apple:"),
                                Symbol(":banana:"),
                            ],
                            [6, 4],
                        )
                        for _ in range(3)
                    ],
                )
            ],
            Window(3, 3),
        )

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

        result = self.slot_machine.pull_lever()
        winnings = self.slot_machine.evaluate(result) * bet
        response = ""
        for row in range(self.slot_machine.window.rows):
            for (widx, wheel) in enumerate(result):
                if self.slot_machine.is_on_scoreline(row, widx):
                    response += "**" + wheel[row].name + "** "
                else:
                    response += wheel[row].name + " "
            # Only supports linear paylines for now
            if self.slot_machine.is_on_scoreline(row, 0):
                response += " <<<"
            response += "\n"

        if winnings > 0:
            await self.economy_cog.deposit_money(interaction.user.id, winnings)
            await interaction.response.send_message(
                f"{response}\nCongratulations! You won ${winnings:.2f}!"
            )
        else:
            await self.economy_cog.withdraw_money(interaction.user.id, bet)
            await interaction.response.send_message(
                f"{response}\nBetter luck next time! You lost ${bet:.2f}."
            )
