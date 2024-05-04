from typing import List
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from copy import deepcopy

from cogs.games.slots import (
    PayRule,
    GameBase,
    Machine,
    Payline,
    Reward,
    RewardType,
    Symbol,
    Reelstrip,
    Window,
)

EXTRA_REEL_ITEM_ID = 0
WINDOW_EXPANSION_ITEM_ID = 1


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
        paylines = [
            window.centerline(),
        ]
        pay_rules = [
            PayRule([sym] * num_reels, Reward(RewardType.MONEY, pay))
            for sym, pay in zip(symbols, payouts)
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
    @app_commands.checks.cooldown(1, 5, key=lambda i: (i.guild_id, i.user.id))
    async def slots(self, interaction: discord.Interaction):
        """Play the slots."""
        balance = await self.economy_cog.get_balance(interaction.user.id)
        if balance < self.slot_cost:
            await interaction.response.send_message("Insufficient balance.")
            return

        machine = await self.prepare_slot_machine(interaction.user.id)
        spins = 1
        winnings = 0.0

        while spins > 0:
            result = machine.pull_lever()
            reward = machine.evaluate(result)
            response = self.generate_slot_response(machine, result)

            if reward.reward_type == RewardType.SPIN:
                spins += int(reward.value)
            if reward.reward_type == RewardType.MONEY:
                winnings += reward.value
            spins -= 1

        if winnings > 0:
            await self.economy_cog.deposit_money(
                interaction.user.id, winnings, "slot winnings"
            )
            await interaction.response.send_message(
                f"{response}\nCongratulations! You won ${winnings:,.2f}!",
                ephemeral=True,
            )
        else:
            await self.economy_cog.withdraw_money(
                interaction.user.id, self.slot_cost, "slot cost"
            )
            await interaction.response.send_message(
                f"{response}\nBetter luck next time! You lost ${self.slot_cost:,.2f}.",
                ephemeral=True,
            )

    async def prepare_slot_machine(self, user_id: int) -> Machine:
        machine = deepcopy(self.slot_machine)
        extra_reels = await self.inventory_cog.get_item_quantity(
            user_id, EXTRA_REEL_ITEM_ID
        )
        for _ in range(extra_reels):
            machine.add_reel(self.base_reelstrip.copy())
        window_expansions = await self.inventory_cog.get_item_properties(
            user_id, WINDOW_EXPANSION_ITEM_ID
        )
        for count, properties in window_expansions:
            for _ in range(count):
                machine.expand_window(properties["rows"], properties["wheels"])
        return machine

    @staticmethod
    def generate_slot_response(machine: Machine, result: List[List[Symbol]]) -> str:
        response = ""
        for row in range(machine.window.max_rows):
            for (widx, wheel) in enumerate(result):
                if machine.is_on_scoreline(widx, row):
                    response += "**" + wheel[row].name + "** "
                else:
                    response += wheel[row].name + " "
            if machine.is_on_scoreline(0, row):
                response += " <<<"
            response += "\n"
        return response

    @slots.error
    async def slots_error(self, interaction: discord.Interaction, error: Exception):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(
                f"Slot is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True,
            )
        else:
            raise error

    @staticmethod
    def render_payline_ascii(payline: Payline, window: Window):
        art = [
            [" " for _ in range(window.rows_per_column[c])]
            for c in range(window.wheels)
        ]

        for i in range(len(payline.indices) - 1):
            start_row = payline.indices[i]
            end_row = payline.indices[i + 1]
            if start_row == end_row:
                art[start_row] = ["―" for _ in range(window.wheels)]
            elif start_row < end_row:
                step = 1
                slope_char = "╲"
            else:
                step = -1
                slope_char = "╱"

            # Draw the slope between start_row and end_row
            if start_row != end_row:
                col_step = (window.wheels - 1) // (abs(end_row - start_row))
                for offset, row in enumerate(range(start_row, end_row + step, step)):
                    if (
                        0 <= row < window.rows_per_column[row]
                        and 0 <= offset * col_step < window.wheels
                    ):
                        art[row][offset * col_step] = slope_char

        # Handle the case when there is only one index or last index with a horizontal line
        if len(payline.indices) == 1 or payline.indices[-2] != payline.indices[-1]:
            last_row = payline.indices[-1]
            art[last_row] = ["―" for _ in range(window.wheels)]

        # Convert each row of the art to a string and join them with newlines
        return "\n".join("".join(row) for row in art)

    @app_commands.command()
    async def show_rules(self, interaction: discord.Interaction):
        """Show the rules and payouts for the slot machine."""
        response = f"**Cost per play**: ${self.slot_cost:,.2f}\n\n"
        response += "**Pay Rules**:\n"
        for game in self.slot_machine.games:
            response += f"*Game {game.name}*\n"
            for rule in game.pay_rules:
                response += f"{''.join(list(map(str, rule.symbol_pattern)))} --- ${rule.reward.value:,.2f}\n"
            response += "\n**Paylines**:\n"
            for payline in game.paylines:
                response += "```"
                response += self.render_payline_ascii(payline, self.slot_machine.window)
                response += "```\n\n"
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
            f"\n**Winnings**: ${winnings:,.2f}"
            f"\n**Losses**: ${losses:,.2f}"
            f"\n**Net**: ${winnings + losses:,.2f}"
            f"\n**Games Played**: {winnings_count + losses_count:,}"
            f"\n**Average Winnings**: ${avg_winnings:,.2f}"
            f"\n**Win Rate**: {(winnings_count / (winnings_count + losses_count)) * 100:,.2f}%",
            ephemeral=ephemeral,
        )

    async def add_slot_items(self):
        """Build slot machine inventory items in the database."""
        items = [
            (
                EXTRA_REEL_ITEM_ID,
                "Additional Reel",
                10_000,
                str({}),
                "Adds an additional reel to the slot machine.",
            ),
            (
                WINDOW_EXPANSION_ITEM_ID,
                "Window Expansion",
                50_000,
                str({"rows": 1, "wheels": 1}),
                "Expands the window of the slot machine by 1 each.",
            ),
        ]
        async with aiosqlite.connect("economy.db") as db:
            for i in items:
                await db.execute(
                    "INSERT OR IGNORE INTO items (item_id, name, cost, properties, description) VALUES (?, ?, ?, ?, ?)",
                    i,
                )
            await db.commit()
