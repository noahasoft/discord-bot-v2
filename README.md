# DiscordBotv2

## Description

Simple discord.py bot to announce when users enter and leave voice channels.

Also included some tree commands as a test. I might add more commands in the future.

## Requirements

Requirements can be found in the `requirements.txt` file, but the primary libraries are `discord.py`, `aiogtts`, `aiohttp`, and `aiosqlite`.

## Running

 1. Install the requirements in a virtual environment.

 2. Set the following environmental variables:
    - `DISCORD_TOKEN`: The token of the bot.
    - `DISCORD_GUILD`: The guild to apply the command tree to.

3. Run the bot with `python3 main.py`.