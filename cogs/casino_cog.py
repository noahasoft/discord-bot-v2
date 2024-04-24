import aiosqlite
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
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot
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

    @app_commands.command()
    async def show_slot_stats(
        self, interaction: discord.Interaction, public: bool = False
    ):
        """Show the statistics for the user's slot machine play."""
        user_id = interaction.user.id
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute(
                "SELECT SUM(CASE WHEN value > 0 THEN value ELSE 0 END) AS winnings,"
                " COUNT(CASE WHEN value > 0 THEN 1 END) AS winnings_count,"
                " SUM(CASE WHEN value < 0 THEN value ELSE 0 END) AS losses,"
                " COUNT(CASE WHEN value < 0 THEN 1 END) AS losses_count,"
                " AVG(value) AS average_winnings"
                " FROM transactions"
                " WHERE user_id = ?"
                " AND (description = 'slot winnings' OR description = 'slot cost')",
                (user_id,),
            ) as cursor:
                stats_row = await cursor.fetchone()
                if stats_row is None:
                    winnings = 0
                    winnings_count = 0
                    losses = 0
                    losses_count = 0
                    avg_winnings = 0
                else:
                    (
                        winnings,
                        winnings_count,
                        losses,
                        losses_count,
                        avg_winnings,
                    ) = stats_row
        await interaction.response.send_message(
            f"**{interaction.user.name} Slot Stats**\n"
            f"Winnings: ${winnings:.2f}\nLosses: ${losses:.2f}\nNet: ${winnings + losses:.2f}"
            f"\nGames Played: {winnings_count + losses_count}"
            f"\nAverage Winnings: ${avg_winnings:.2f}"
            f"\nWin Rate: {(winnings_count / (winnings_count + losses_count)) * 100:.2f}%",
            ephemeral=(not public),
        )
