from typing import Optional, Union
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.games.stocks import (
    GBMSystem,
    Market,
    Stock,
)


@app_commands.guild_only()
class StocksCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot
        self.economy_cog = self.bot.get_cog("EconomyCog")
        # fmt: off
        self.market = Market.init_from_stocks(
            stocks=
            [
                Stock("Apple Inc.", "AAPL", GBMSystem(S0=150, mu=0.0001, sigma=0.01)),
                Stock("Microsoft Corporation", "MSFT", GBMSystem(S0=200, mu=0.0002, sigma=0.02)),
                Stock("Google LLC", "GOOGL", GBMSystem(S0=300, mu=0.0003, sigma=0.03)),
                Stock("Amazon.com Inc.", "AMZN", GBMSystem(S0=400, mu=0.0004, sigma=0.04)),
                Stock("Meta Platforms Inc.", "META", GBMSystem(S0=500, mu=0.0005, sigma=0.05)),
                Stock("Tesla Inc.", "TSLA", GBMSystem(S0=600, mu=0.0006, sigma=0.06)),
                Stock("NVIDIA Corporation", "NVDA", GBMSystem(S0=700, mu=0.0007, sigma=0.07)),
                Stock("PayPal Holdings Inc.", "PYPL", GBMSystem(S0=800, mu=0.0008, sigma=0.08)),
                Stock("Netflix Inc.", "NFLX", GBMSystem(S0=900, mu=0.0009, sigma=0.09)),
                Stock("Adobe Inc.", "ADBE", GBMSystem(S0=1000, mu=0.001, sigma=0.1)),
                Stock("Salesforce.com Inc.", "CRM", GBMSystem(S0=1100, mu=0.0011, sigma=0.11)),
                Stock("Zoom Video Communications Inc.", "ZM", GBMSystem(S0=1200, mu=0.0012, sigma=0.12)),
                Stock("Shopify Inc.", "SHOP", GBMSystem(S0=1300, mu=0.0013, sigma=0.13)),
                Stock("Spotify Technology S.A.", "SPOT", GBMSystem(S0=1400, mu=0.0014, sigma=0.14)),
                Stock("Square Inc.", "SQ", GBMSystem(S0=1500, mu=0.0015, sigma=0.15)),
                Stock("Roblox Corporation", "RBLX", GBMSystem(S0=1600, mu=0.0016, sigma=0.16)),
                Stock("Airbnb Inc.", "ABNB", GBMSystem(S0=1700, mu=0.0017, sigma=0.17)),
                Stock("DoorDash Inc.", "DASH", GBMSystem(S0=1800, mu=0.0018, sigma=0.18)),
                Stock("Coinbase Global Inc.", "COIN", GBMSystem(S0=1900, mu=0.0019, sigma=0.19)),
                Stock("Pinterest Inc.", "PINS", GBMSystem(S0=2000, mu=0.002, sigma=0.2)),
                Stock("Palantir Technologies Inc.", "PLTR", GBMSystem(S0=2100, mu=0.0021, sigma=0.21)),
            ]
        )
        # fmt: on

    async def cog_load(self) -> None:
        await self.create_stocks_table()
        await self.create_portfolio_table()
        await self.create_history_table()
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

    async def create_history_table(self) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    stock_symbol TEXT NOT NULL,
                    date TEXT NOT NULL DEFAULT (date('now')),
                    high REAL,
                    low REAL,
                    PRIMARY KEY (stock_symbol, date),
                    FOREIGN KEY (stock_symbol) REFERENCES stocks(symbol)
                )
                """
            )
            await db.commit()

    async def add_initial_stocks(self) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            for stock in self.market.stocks.values():
                await db.execute(
                    "INSERT OR IGNORE INTO stocks (name, symbol, price) VALUES (?, ?, ?)",
                    (stock.name, stock.symbol, stock.price),
                )
            await db.commit()

    async def get_stock(self, symbol: str) -> Optional[Stock]:
        async with aiosqlite.connect("stocks.db") as db:
            query = """
                SELECT s.name, s.symbol, s.price, h.date, h.high, h.low
                FROM stocks s
                LEFT JOIN history h ON s.symbol = h.stock_symbol
                WHERE s.symbol = ?
                ORDER BY h.date DESC
            """
            async with db.execute(query, (symbol,)) as cursor:
                stock = None
                async for row in cursor:
                    if not stock:
                        stock = Stock.from_row(row)
                return stock

    async def get_all_stocks(self) -> list[Stock]:
        async with aiosqlite.connect("stocks.db") as db:
            query = """
                SELECT s.name, s.symbol, s.price, h.date, h.high, h.low
                FROM stocks s
                LEFT JOIN history h ON s.symbol = h.stock_symbol
                ORDER BY s.symbol, h.date DESC
            """
            async with db.execute(query) as cursor:
                stocks = []
                current_symbol = None
                stock = None
                async for row in cursor:
                    if current_symbol != row[1]:
                        if stock:
                            stocks.append(stock)
                        current_symbol = row[1]
                        stock = Stock.from_row(row)
                if stock:
                    stocks.append(stock)
                return stocks

    async def update_stock_price(self, symbol: str, new_price: float) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            await db.execute(
                "UPDATE stocks SET price = ? WHERE symbol = ?", (new_price, symbol)
            )
            await db.commit()

    async def update_stock_history(self, symbol: str, new_price: float) -> None:
        async with aiosqlite.connect("stocks.db") as db:
            await db.execute(
                """
                INSERT INTO history (stock_symbol, high, low, date)
                VALUES (?, ?, ?, date('now'))
                ON CONFLICT(stock_symbol, date)
                DO UPDATE SET 
                    high = MAX(excluded.high, history.high),
                    low = MIN(excluded.low, history.low)
                """,
                (symbol, new_price, new_price),
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

    @tasks.loop(minutes=5)
    async def update_stock_prices(self):
        for stock in await self.get_all_stocks():
            new_price = stock.get_next()
            await self.update_stock_price(stock.symbol, new_price)
            await self.update_stock_history(stock.symbol, new_price)

    @app_commands.command()
    async def list_stocks(
        self, interaction: discord.Interaction, long_names: bool = False
    ) -> None:
        """
        Show a list of all available stocks and their prices.
        """
        stocks = await self.get_all_stocks()
        embed = discord.Embed(
            title="Current Market Prices (Low/High)", color=discord.Color.blurple()
        )
        for stock in stocks:
            name = f"{stock.name}(**{stock.symbol}**)" if long_names else stock.symbol
            val = f"${stock.price:,.2f} (${stock.low:,.2f}/${stock.high:,.2f})"
            embed.add_field(name=name, value=val, inline=True)
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
        if await self.economy_cog.get_balance(interaction.user.id) < price:
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
                SELECT stocks.name, stocks.symbol, portfolio.quantity, stocks.price, history.high, history.low 
                FROM portfolio
                JOIN stocks ON portfolio.stock_symbol = stocks.symbol
                JOIN history ON stocks.symbol = history.stock_symbol AND history.date = date('now')
                WHERE user_id = ? AND portfolio.quantity > 0
                """,
                (user_id,),
            ) as cursor:
                stocks = await cursor.fetchall()
        embed = discord.Embed(title="Portfolio", color=discord.Color.blurple())
        for name, symbol, quantity, price, high, low in stocks:
            high = high or price
            low = low or price
            embed.add_field(
                name=symbol,
                value=f"{name}: {quantity} shares * ${price:,.2f} = ${price*quantity:,.2f} | High: ${high:,.2f} Low: ${low:,.2f}",
                inline=True,
            )
        await interaction.response.send_message(embed=embed)
