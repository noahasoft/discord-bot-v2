import discord
from discord import app_commands
from discord.ext import commands


@app_commands.guild_only()
class UtilitiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelist_cog = self.bot.get_cog("WhitelistCog")

    @app_commands.command()
    async def restart(self, interaction: discord.Interaction):
        """Restarts the bot."""
        if not await self.whitelist_cog.is_user_whitelisted(
            interaction.user.id
        ):  # Check if the user is whitelisted
            await interaction.response.send_message(
                "You are not whitelisted to restart the bot."
            )
            return

        await interaction.response.send_message("Bot restarting, please wait.")
        await self.bot.close()
