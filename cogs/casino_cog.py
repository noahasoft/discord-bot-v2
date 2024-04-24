import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from copy import deepcopy

from cogs.games.slots import (
    PayRule,
    GameBase,
    Machine,
    Symbol,
    Reelstrip,
    Window,
)

EXTRA_REEL_ITEM_ID = 0


@app_commands.guild_only()
class CasinoCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot
        self.economy_cog = self.bot.get_cog("EconomyCog")
        self.inventory_cog = self.bot.get_cog("InventoryCog")
        num_reels = 3
        symbols = [Symbol(":apple:"), Symbol(":banana:"), Symbol(":cherries:")]
        counts = [6, 4, 2]
        payouts = [200, 500, 1000]
        self.base_reelstrip = Reelstrip(symbols, counts)
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
                    [self.base_reelstrip.copy() for _ in range(num_reels)],
                )
            ],
            window,
        )
        self.slot_cost = 20

    async def cog_load(self) -> None:
        await self.add_slot_items()
        await super().cog_load()

    @app_commands.command()
    async def slots(self, interaction: discord.Interaction):
        """Play the slots."""
        balance = await self.economy_cog.get_balance(interaction.user.id)
        if balance < self.slot_cost:
            await interaction.response.send_message("Insufficient balance.")
            return
        machine = deepcopy(self.slot_machine)
        extra_reels = await self.inventory_cog.get_item_quantity(
            interaction.user.id, EXTRA_REEL_ITEM_ID
        )
        for _ in range(extra_reels):
            machine.add_reel(self.base_reelstrip.copy())
        result = machine.pull_lever()
        winnings = machine.evaluate(result)
        response = ""
        for row in range(machine.window.max_rows):
            for (widx, wheel) in enumerate(result):
                if machine.is_on_scoreline(widx, row):
                    response += "**" + wheel[row].name + "** "
                else:
                    response += wheel[row].name + " "
            # Can only signify linear paylines for now
            if machine.is_on_scoreline(0, row):
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
        self,
        interaction: discord.Interaction,
        ephemeral: bool = True,
        all_server: bool = False,
    ):
        """Show the winnings statistics for the slot machine."""
        user_id = interaction.user.id
        query = (
            "SELECT SUM(CASE WHEN value > 0 THEN value ELSE 0 END) AS winnings,"
            " COUNT(CASE WHEN value > 0 THEN 1 END) AS winnings_count,"
            " SUM(CASE WHEN value < 0 THEN value ELSE 0 END) AS losses,"
            " COUNT(CASE WHEN value < 0 THEN 1 END) AS losses_count,"
            " AVG(value) AS average_winnings"
            " FROM transactions WHERE "
            + ("user_id = ? AND " if not all_server else "")
            + " (description = 'slot winnings' OR description = 'slot cost')"
        )
        params = (user_id,) if not all_server else ()

        async with aiosqlite.connect("economy.db") as db:
            cursor = await db.execute(query, params)
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
            f"**{interaction.user.name if not all_server else 'Total'} Slot Stats**"
            f"\n----------------"
            f"\n**Winnings**: ${winnings:.2f}"
            f"\n**Losses**: ${losses:.2f}"
            f"\n**Net**: ${winnings + losses:.2f}"
            f"\n**Games Played**: {winnings_count + losses_count}"
            f"\n**Average Winnings**: ${avg_winnings:.2f}"
            f"\n**Win Rate**: {(winnings_count / (winnings_count + losses_count)) * 100:.2f}%",
            ephemeral=ephemeral,
        )

    async def add_slot_items(self):
        """Build slot machine inventory items in the database."""
        async with aiosqlite.connect("economy.db") as db:
            await db.execute(
                "INSERT OR IGNORE INTO items (item_id, name, cost, properties, description) VALUES (?, ?, ?, ?, ?)",
                (
                    EXTRA_REEL_ITEM_ID,
                    "Additional Reel",
                    10_000,
                    str({}),
                    "Adds an additional reel to the slot machine.",
                ),
            )
            await db.commit()
