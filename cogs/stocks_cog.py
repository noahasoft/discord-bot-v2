from typing import Optional, Union
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.games.stocks import (
    GBMSystem,
    Stock,
)


@app_commands.guild_only()
class StocksCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot
        self.economy_cog = self.bot.get_cog("EconomyCog")

    async def cog_load(self) -> None:
        await self.create_stocks_table()
        await self.create_portfolio_table()
        await self.add_initial_stocks()
        self.update_stock_prices.start()
        await super().cog_load()

    async def cog_unload(self) -> None:
        self.update_stock_prices.stop()
        await super().cog_unload()

    async def create_stocks_table(self) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS stocks (
                    name TEXT NOT NULL,
                    symbol TEXT NOT NULL PRIMARY KEY,
                    price REAL NOT NULL
                )
                """
            )
            await db.commit()

    async def create_portfolio_table(self) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio (
                    user_id INTEGER NOT NULL,
                    stock_symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (user_id, stock_symbol),
                    FOREIGN KEY (stock_symbol) REFERENCES stocks(symbol)
                )
                """
            )
            await db.commit()

    async def add_initial_stocks(self) -> None:
        stocks = [
            Stock("Apple Inc.", GBMSystem(S0=150, mu=0.0001, sigma=0.01), "AAPL"),
            Stock(
                "Microsoft Corporation",
                GBMSystem(S0=200, mu=0.0002, sigma=0.02),
                "MSFT",
            ),
            Stock("Google LLC", GBMSystem(S0=300, mu=0.0003, sigma=0.03), "GOOGL"),
            Stock("Amazon.com Inc.", GBMSystem(S0=400, mu=0.0004, sigma=0.04), "AMZN"),
            Stock(
                "Meta Platforms Inc.", GBMSystem(S0=500, mu=0.0005, sigma=0.05), "META"
            ),
            Stock("Tesla Inc.", GBMSystem(S0=600, mu=0.0006, sigma=0.06), "TSLA"),
            Stock(
                "NVIDIA Corporation", GBMSystem(S0=700, mu=0.0007, sigma=0.07), "NVDA"
            ),
            Stock(
                "PayPal Holdings Inc.", GBMSystem(S0=800, mu=0.0008, sigma=0.08), "PYPL"
            ),
            Stock("Netflix Inc.", GBMSystem(S0=900, mu=0.0009, sigma=0.09), "NFLX"),
            Stock("Adobe Inc.", GBMSystem(S0=1000, mu=0.001, sigma=0.1), "ADBE"),
            Stock(
                "Salesforce.com Inc.", GBMSystem(S0=1100, mu=0.0011, sigma=0.11), "CRM"
            ),
            Stock(
                "Zoom Video Communications Inc.",
                GBMSystem(S0=1200, mu=0.0012, sigma=0.12),
                "ZM",
            ),
            Stock("Shopify Inc.", GBMSystem(S0=1300, mu=0.0013, sigma=0.13), "SHOP"),
            Stock(
                "Spotify Technology S.A.",
                GBMSystem(S0=1400, mu=0.0014, sigma=0.14),
                "SPOT",
            ),
            Stock("Square Inc.", GBMSystem(S0=1500, mu=0.0015, sigma=0.15), "SQ"),
            Stock(
                "Roblox Corporation", GBMSystem(S0=1600, mu=0.0016, sigma=0.16), "RBLX"
            ),
            Stock("Airbnb Inc.", GBMSystem(S0=1700, mu=0.0017, sigma=0.17), "ABNB"),
            Stock("DoorDash Inc.", GBMSystem(S0=1800, mu=0.0018, sigma=0.18), "DASH"),
            Stock(
                "Coinbase Global Inc.",
                GBMSystem(S0=1900, mu=0.0019, sigma=0.19),
                "COIN",
            ),
            Stock("Pinterest Inc.", GBMSystem(S0=2000, mu=0.002, sigma=0.2), "PINS"),
            Stock(
                "Palantir Technologies Inc.",
                GBMSystem(S0=2100, mu=0.0021, sigma=0.21),
                "PLTR",
            ),
        ]
        async with aiosqlite.connect("stocks.db") as db:
            for stock in stocks:
                await db.execute(
                    "INSERT OR IGNORE INTO stocks (name, symbol, price) VALUES (?, ?, ?)",
                    (stock.name, stock.symbol, stock.price),
                )
            await db.commit()

    async def get_stock(self, symbol: str) -> Optional[Stock]:
        async with aiosqlite.connect("stocks.db") as db:
            async with db.execute(
                "SELECT * FROM stocks WHERE symbol = ?", (symbol,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Stock.from_row(row)
                else:
                    return None

    async def get_all_stocks(self) -> list[Stock]:
        async with aiosqlite.connect("stocks.db") as db:
            async with db.execute("SELECT * FROM stocks") as cursor:
                return [Stock.from_row(row) async for row in cursor]

    async def update_stock_price(self, symbol: str, price: float) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            await db.execute(
                "UPDATE stocks SET price = ? WHERE symbol = ?", (price, symbol)
            )
            await db.commit()

    async def give_stock(
        self, user: Union[discord.User, discord.Member], stock: Stock, amount: int
    ) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            await db.execute(
                "INSERT INTO portfolio (user_id, stock_symbol, quantity) VALUES (?, ?, ?)",
                (user.id, stock.symbol, amount),
            )
            await db.commit()

    async def remove_stock(
        self, user: Union[discord.User, discord.Member], stock: Stock, amount: int
    ) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            await db.execute(
                "UPDATE portfolio SET quantity = quantity - ? WHERE user_id = ? AND stock_symbol = ?",
                (amount, user.id, stock.symbol),
            )
            await db.commit()

    async def get_stock_quantity(
        self, user: Union[discord.User, discord.Member], stock: Stock
    ) -> int:
        async with aiosqlite.connect("stocks.db") as db:
            async with db.execute(
                "SELECT quantity FROM portfolio WHERE user_id = ? AND stock_symbol = ?",
                (user.id, stock.symbol),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # Every 5 minutes update the stock prices
    @tasks.loop(minutes=5)
    async def update_stock_prices(self):
        for stock in await self.get_all_stocks():
            # Simulate a stock price change
            new_price = stock.get_next()
            await self.update_stock_price(stock.symbol, new_price)

    @app_commands.command()
    async def list_stocks(self, interaction: discord.Interaction) -> None:
        """
        Show a list of all available stocks and their prices.
        """
        stocks = await self.get_all_stocks()
        embed = discord.Embed(title="Stocks", color=discord.Color.blurple())
        for stock in stocks:
            embed.add_field(
                name=stock.symbol, value=f"${stock.price:,.2f}", inline=True
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def buy_stock(
        self, interaction: discord.Interaction, symbol: str, amount: int
    ) -> None:
        """
        Purchase a stock by its symbol and the amount of shares.
        """
        stock = await self.get_stock(symbol)
        if not stock:
            await interaction.response.send_message("Stock not found", ephemeral=True)
            return
        price = stock.price * amount
        if self.economy_cog.get_balance(interaction.user.id) < price:
            await interaction.response.send_message(
                "You don't have enough money to buy this stock", ephemeral=True
            )
            return
        await self.economy_cog.withdraw_money(interaction.user.id, price)
        await self.give_stock(interaction.user, stock, amount)
        await interaction.response.send_message(
            f"Bought {amount} shares of {stock.name} for ${price:,.2f}"
        )

    @app_commands.command()
    async def sell_stock(
        self, interaction: discord.Interaction, symbol: str, amount: int
    ) -> None:
        """
        Sell a stock by its symbol and the amount of shares.
        """
        stock = await self.get_stock(symbol)
        if not stock:
            await interaction.response.send_message("Stock not found", ephemeral=True)
            return
        quantity = await self.get_stock_quantity(interaction.user, stock)
        if quantity < amount:
            await interaction.response.send_message(
                f"You don't have enough shares of {stock.name}", ephemeral=True
            )
            return
        price = stock.price * amount
        await self.economy_cog.deposit_money(interaction.user.id, price)
        await self.remove_stock(interaction.user, stock, amount)
        await interaction.response.send_message(
            f"Sold {amount} shares of {stock.name} for ${price:,.2f}"
        )

    @app_commands.command()
    async def list_portfolio(self, interaction: discord.Interaction) -> None:
        """
        Show a list of all stocks in the user's portfolio.
        """
        user_id = interaction.user.id
        async with aiosqlite.connect("stocks.db") as db:
            async with db.execute(
                """
                SELECT stocks.name, stocks.symbol, portfolio.quantity, stocks.price
                FROM portfolio
                JOIN stocks ON portfolio.stock_symbol = stocks.symbol
                WHERE user_id = ?
                """,
                (user_id,),
            ) as cursor:
                stocks = await cursor.fetchall()
        embed = discord.Embed(title="Portfolio", color=discord.Color.blurple())
        for name, symbol, quantity, price in stocks:
            embed.add_field(
                name=symbol, value=f"{name}: {quantity} {price:,.2f}", inline=True
            )
        await interaction.response.send_message(embed=embed)
