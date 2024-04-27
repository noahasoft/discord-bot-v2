import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite


@app_commands.guild_only()
class InventoryCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot
        self.economy_cog = self.bot.get_cog("EconomyCog")

    async def cog_load(self) -> None:
        await self.create_inventory_table()
        await super().cog_load()

    async def create_inventory_table(self):
        async with aiosqlite.connect("economy.db") as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS items ("
                "item_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT NOT NULL, "
                "cost INTEGER NOT NULL, "
                "properties TEXT, "
                "description TEXT)"
            )
            await db.execute(
                "CREATE TABLE IF NOT EXISTS inventory ("
                "inventory_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "user_id INTEGER NOT NULL, "
                "item_id INTEGER NOT NULL, "
                "quantity INTEGER NOT NULL DEFAULT 1, "
                "FOREIGN KEY(item_id) REFERENCES items(item_id))"
            )
            await db.commit()

    async def purchase_item(self, user_id: int, item_id: int):
        # Check if the user has enough balance
        cost = await self.get_item_cost(item_id)
        balance = await self.economy_cog.get_balance(user_id)
        if balance < cost:
            return "Insufficient funds."

        # Perform the transaction
        await self.economy_cog.withdraw_money(user_id, cost)
        async with aiosqlite.connect("economy.db") as db:
            # Check if the user already owns the item
            async with db.execute(
                "SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Update quantity if already owned
                    await db.execute(
                        "UPDATE inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_id = ?",
                        (user_id, item_id),
                    )
                else:
                    # Add new item to inventory
                    await db.execute(
                        "INSERT INTO inventory (user_id, item_id) VALUES (?, ?)",
                        (user_id, item_id),
                    )
            await db.commit()
        return "Purchase successful."

    async def get_item_cost(self, item_id: int):
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute(
                "SELECT cost FROM items WHERE item_id = ?", (item_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None

    async def get_inventory(self, user_id: int):
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute(
                "SELECT items.name, inventory.quantity FROM inventory "
                "JOIN items ON inventory.item_id = items.item_id "
                "WHERE inventory.user_id = ?",
                (user_id,),
            ) as cursor:
                return await cursor.fetchall()

    async def add_item(self, name: str, cost: int, properties: dict, description: str):
        properties_str = json.dumps(properties)
        async with aiosqlite.connect("economy.db") as db:
            await db.execute(
                "INSERT INTO items (name, cost, properties) VALUES (?, ?, ?, ?)",
                (name, cost, properties_str, description),
            )
            await db.commit()

    async def get_item_quantity(self, user_id: int, item_id: int) -> int:
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute(
                "SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    @app_commands.command()
    async def show_inventory(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        inventory = await self.get_inventory(user_id)
        if not inventory:
            await interaction.response.send_message("Your inventory is empty.")
            return

        response = "Your Inventory:\n"
        for item_name, quantity in inventory:
            response += f"{item_name}: {quantity}\n"
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command()
    async def buy_item(self, interaction: discord.Interaction, item_id: int):
        user_id = interaction.user.id
        response = await self.purchase_item(user_id, item_id)
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command()
    async def list_shop(self, interaction: discord.Interaction):
        response = "Items:\n"
        response += "ID: Name | Cost | Properties | Description\n"
        async with aiosqlite.connect("economy.db") as db:
            async with db.execute("SELECT * FROM items") as cursor:
                items = await cursor.fetchall()
                for item in items:
                    item_id, name, cost, properties, description = item
                    response += f"**{item_id}**: {name} | ${cost} | ({properties}) | {description}\n"
        await interaction.response.send_message(response, ephemeral=True)

    # Trading system
    @app_commands.command()
    async def gift_item(
        self,
        interaction: discord.Interaction,
        recipient: discord.Member,
        item_id: int,
        quantity: int = 1,
    ):
        user_id = interaction.user.id
        recipient_id = recipient.id
        # Check if the user has the item
        user_quantity = await self.get_item_quantity(user_id, item_id)
        if user_quantity < quantity:
            await interaction.response.send_message(
                "You do not have enough of that item.", ephemeral=True
            )
            return

        # Perform the trade
        async with aiosqlite.connect("economy.db") as db:
            # Update the user's inventory
            await db.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?",
                (quantity, user_id, item_id),
            )
            # Check if the recipient already owns the item
            async with db.execute(
                "SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?",
                (recipient_id, item_id),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Update quantity if already owned
                    await db.execute(
                        "UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_id = ?",
                        (quantity, recipient_id, item_id),
                    )
                else:
                    # Add new item to recipient's inventory
                    await db.execute(
                        "INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)",
                        (recipient_id, item_id, quantity),
                    )
            await db.commit()
        await interaction.response.send_message(
            f"Trade successful. {recipient.mention} now owns {quantity} of that item.",
            ephemeral=True,
        )
