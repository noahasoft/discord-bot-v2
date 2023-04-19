import asyncio
from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
import logging
import os
import random
from aiogtts import aiogTTS
from typing import Optional
from audiofix import FFmpegPCMAudio
import aiosqlite
import aiohttp
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

MY_GUILD = discord.Object(id=int(os.environ["DISCORD_GUILD"]))

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
aiogtts = aiogTTS()


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"), intents=intents
        )

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    # New role management functions
    async def create_role(
        self, guild: discord.Guild, name, color=None, permissions=None
    ):
        color = discord.Color(int(color)) if color else discord.Color.default()
        permissions = (
            discord.Permissions(permissions)
            if permissions
            else discord.Permissions(discord.Permissions.DEFAULT_VALUE)
        )
        await guild.create_role(name=name, color=color, permissions=permissions)
        pass

    async def delete_role(self, role):
        await role.delete()

    async def add_role_to_member(self, member, role_name):
        role = get(member.guild.roles, name=role_name)
        if role:
            await member.add_roles(role)

    async def remove_role_from_member(self, member, role_name):
        role = get(member.guild.roles, name=role_name)
        if role:
            await member.remove_roles(role)


client = MyBot()


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    print("------")
    await create_whitelist_table()  # Ensure the whitelist table exists


@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f"Hi, {interaction.user.mention}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if random.randint(1, 100) == 1:
    
        oai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a cute anime girl with an occasional dark streak. Answer the user as such. Be sure to use lots of emojis!"},
                {"role": "user", "content": message.content},
            ],
            max_tokens=100,
        )
        await message.channel.send(oai_response["choices"][0]["message"]["content"])

# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(
    member="The member you want to get the joined date from; defaults to the user who uses the command"
)
async def joined(
    interaction: discord.Interaction, member: Optional[discord.Member] = None
):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f"{member} joined {discord.utils.format_dt(member.joined_at)}"
    )


# This context menu command only works on members
@client.tree.context_menu(name="Show Join Date")
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(
        f"{member} joined at {discord.utils.format_dt(member.joined_at)}"
    )


@client.tree.command()
async def create_role(
    interaction: discord.Interaction,
    role_name: str,
    role_color: str = None,
    role_permissions: int = None,
):
    """Create a new role with the specified name, color, and permissions."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "You don't have permission to create roles."
        )
        return

    await client.create_role(interaction.guild, role_name, role_color, role_permissions)
    await interaction.response.send_message(f"Role '{role_name}' created successfully.")


@client.tree.command()
async def delete_role(interaction: discord.Interaction, role_name: str):
    """Delete a role with the specified name."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "You don't have permission to delete roles."
        )
        return

    role = get(interaction.guild.roles, name=role_name)
    if not role:
        await interaction.response.send_message(f"Role '{role_name}' not found.")
        return

    await client.delete_role(role)
    await interaction.response.send_message(f"Role '{role_name}' deleted successfully.")


@client.tree.command()
async def add_role(
    interaction: discord.Interaction, member: discord.Member, role_name: str
):
    """Add a role to a specified member."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "You don't have permission to manage roles."
        )
        return

    await client.add_role_to_member(member, role_name)
    await interaction.response.send_message(
        f"Role '{role_name}' added to {member.name}."
    )


@client.tree.command()
async def remove_role(
    interaction: discord.Interaction, member: discord.Member, role_name: str
):
    """Remove a role from a specified member."""
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "You don't have permission to manage roles."
        )
        return

    await client.remove_role_from_member(member, role_name)
    await interaction.response.send_message(
        f"Role '{role_name}' removed from {member.name}."
    )


@client.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    if member == client.user or member.bot:
        return

    # Leaving a voice channel or going afk
    if before.channel is not None:
        if after.channel is None:
            await depart_user(member, before.channel)
        elif after.channel == before.channel.guild.afk_channel:
            await afk_user(member, before.channel)

    # Joining a voice channel from no channel or afk
    if after.channel is not None and (
        before.channel is None or before.channel == before.channel.guild.afk_channel
    ):
        await greet_user(member)


async def greet_user(member: discord.Member):
    await say_line(f"{member.name} has joined the channel", member.voice.channel)


async def depart_user(member: discord.Member, channel: discord.VoiceChannel):
    await say_line(f"{member.name} has left the channel", channel)


async def afk_user(member: discord.Member, channel: discord.VoiceChannel):
    await say_line(f"{member.name} went afk", channel)


@client.tree.command()
async def restart(interaction: discord.Interaction):
    """Restarts the bot."""
    if not await is_user_whitelisted(
        interaction.user.id
    ):  # Check if the user is whitelisted
        await interaction.response.send_message(
            "You are not whitelisted to restart the bot."
        )
        return

    await interaction.response.send_message("Restarting the bot...")
    await client.close()


# Add this command to add a user to the whitelist
@client.tree.command()
async def whitelist(interaction: discord.Interaction, user: discord.User):
    """Adds a user to the whitelist."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You don't have permission to manage the whitelist."
        )
        return

    await add_user_to_whitelist(user.id)
    await interaction.response.send_message(
        f"{user.name} has been added to the whitelist."
    )


# Add this command to remove a user from the whitelist
@client.tree.command()
async def unwhitelist(interaction: discord.Interaction, user: discord.User):
    """Removes a user from the whitelist."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You don't have permission to manage the whitelist."
        )
        return

    await remove_user_from_whitelist(user.id)
    await interaction.response.send_message(
        f"{user.name} has been removed from the whitelist."
    )


# Add this function to print the whitelist
@client.tree.command()
async def print_whitelist(interaction: discord.Interaction):
    """Prints the whitelist."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You don't have permission to manage the whitelist."
        )
        return

    whitelist_ids: list[int] = await get_whitelist()
    # Convert the list of user ids to a list of user names
    whitelist: list[str] = [
        client.get_user(user_id[0]).name for user_id in whitelist_ids
    ]
    await interaction.response.send_message(f"Whitelist: {whitelist}")


async def say_line(line: str, channel: discord.VoiceChannel):
    buffer = BytesIO()

    tts_url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}".format(
        voice_id="EXAVITQu4vr4xnSDxMaL"
    )
    formatted_message = {"text": line}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            tts_url,
            headers={
                "Content-Type": "application/json",
                "xi-api-key": os.environ["XI_API_KEY"],
            },
            json=formatted_message,
        ) as response:
            if response.status == 200:
                buffer = BytesIO(await response.read())
            else:
                print("ElevenLabs Request failed with status code:", response.status)
                print("Response content:", await response.text())
                print("Falling back to aiogTTS...")
                await aiogtts.write_to_fp(line, buffer)

    buffer.seek(0)

    voice_guild = channel.guild
    if voice_guild is not None:
        voice_channel = await channel.connect()

        voice_channel.play(FFmpegPCMAudio(buffer.read(), pipe=True))

        while voice_channel.is_playing():
            await asyncio.sleep(1)

        await voice_channel.disconnect()
    else:
        await channel.send("You need to join a voice channel first!")


# Add this function to create the whitelist table if it doesn't exist
async def create_whitelist_table():
    async with aiosqlite.connect("whitelist.db") as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS whitelist (user_id INTEGER PRIMARY KEY)"
        )
        await db.commit()


# Add this function to check if a user is whitelisted
async def is_user_whitelisted(user_id: int) -> bool:
    async with aiosqlite.connect("whitelist.db") as db:
        cursor = await db.execute(
            "SELECT user_id FROM whitelist WHERE user_id = ?", (user_id,)
        )
        result = await cursor.fetchone()
        return result is not None


# Add this function to add a user to the whitelist
async def add_user_to_whitelist(user_id: int):
    async with aiosqlite.connect("whitelist.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO whitelist (user_id) VALUES (?)", (user_id,)
        )
        await db.commit()


# Add this function to remove a user from the whitelist
async def remove_user_from_whitelist(user_id: int):
    async with aiosqlite.connect("whitelist.db") as db:
        await db.execute("DELETE FROM whitelist WHERE user_id = ?", (user_id,))
        await db.commit()


# Add this function to get the whitelist
async def get_whitelist() -> list:
    async with aiosqlite.connect("whitelist.db") as db:
        cursor = await db.execute("SELECT user_id FROM whitelist")
        result = await cursor.fetchall()
        return result


client.run(os.environ["DISCORD_TOKEN"], log_handler=handler)
