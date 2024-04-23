import discord
from discord import app_commands
from discord.ext import commands

from cogs.games.slots import (
    PayRule,
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
        num_reels = 3
        symbols = [Symbol(":apple:"), Symbol(":banana:"), Symbol(":cherries:")]
        counts = [6, 4, 2]
        payouts = [200, 500, 1000]
        window = Window([3] * num_reels)
        paylines = [window.centerline()]
        pay_rules = [
            PayRule([sym] * num_reels, pay) for sym, pay in zip(symbols, payouts)
        ]
        self.slot_machine = Machine(
            [
                GameBase(
                    "Default",
                    paylines,
                    pay_rules,
                    [Reelstrip(symbols, counts) for _ in range(num_reels)],
                )
            ],
            window,
        )
        self.slot_cost = 20

    @app_commands.command()
    async def slots(self, interaction: discord.Interaction):
        """Play the slots."""
        balance = await self.economy_cog.get_balance(interaction.user.id)
        if balance < self.slot_cost:
            await interaction.response.send_message("Insufficient balance.")
            return

        result = self.slot_machine.pull_lever()
        winnings = self.slot_machine.evaluate(result)
        response = ""
        for row in range(self.slot_machine.window.max_rows):
            for (widx, wheel) in enumerate(result):
                if self.slot_machine.is_on_scoreline(widx, row):
                    response += "**" + wheel[row].name + "** "
                else:
                    response += wheel[row].name + " "
            # Can only signify linear paylines for now
            if self.slot_machine.is_on_scoreline(0, row):
                response += " <<<"
            response += "\n"

        if winnings > 0:
            await self.economy_cog.deposit_money(
                interaction.user.id, winnings, "slot winnings"
            )
            await interaction.response.send_message(
                f"{response}\nCongratulations! You won ${winnings:.2f}!"
            )
        else:
            await self.economy_cog.withdraw_money(
                interaction.user.id, self.slot_cost, "slot cost"
            )
            await interaction.response.send_message(
                f"{response}\nBetter luck next time! You lost ${self.slot_cost:.2f}."
            )

    @app_commands.command()
    async def show_rules(self, interaction: discord.Interaction):
        """Show the rules and payouts for the slot machine."""
        response = f"**Cost per play**: ${self.slot_cost:.2f}\n\n"
        response += "**Pay Rules**:\n"
        for game in self.slot_machine.games:
            response += f"*Game {game.name}*\n"
            for rule in game.pay_rules:
                response += f"{''.join(list(map(str, rule.symbol_pattern)))} --- ${rule.payout:.2f}\n"
            response += "\n**Paylines (Zero indexed)**:\n"
            for line in game.paylines:
                response += f"{'-'.join(list(map(str, line.indices)))}\n"
        await interaction.response.send_message(response, ephemeral=True)
