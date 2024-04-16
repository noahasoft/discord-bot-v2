import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional


@app_commands.guild_only()
class JoinedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Show Join Date", callback=self.show_join_date
        )
        self.bot.tree.add_command(self.ctx_menu)

    @app_commands.command()
    @app_commands.describe(
        member="The member you want to get the joined date from; defaults to the user who uses the command"
    )
    async def joined(
        self, interaction: discord.Interaction, member: Optional[discord.Member] = None
    ):
        """Says when a member joined."""
        # If no member is explicitly provided then we use the command user here
        member = member or interaction.user

        # The format_dt function formats the date time into a human readable representation in the official client
        await interaction.response.send_message(
            f"{member} joined {discord.utils.format_dt(member.joined_at)}"
        )

    async def show_join_date(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        await interaction.response.send_message(
            f"{message.author.display_name} joined at {discord.utils.format_dt(message.author.joined_at)}"
        )


# @client.tree.command()
# @app_commands.describe(
#     member="The member you want to get the joined date from; defaults to the user who uses the command"
# )
# async def joined(
#     interaction: discord.Interaction, member: Optional[discord.Member] = None
# ):
#     """Says when a member joined."""
#     # If no member is explicitly provided then we use the command user here
#     member = member or interaction.user

#     # The format_dt function formats the date time into a human readable representation in the official client
#     await interaction.response.send_message(
#         f"{member} joined {discord.utils.format_dt(member.joined_at)}"
#     )


# # This context menu command only works on members
# @client.tree.context_menu(name="Show Join Date")
# async def show_join_date(interaction: discord.Interaction, member: discord.Member):
#     # The format_dt function formats the date time into a human readable representation in the official client
#     await interaction.response.send_message(
#         f"{member} joined at {discord.utils.format_dt(member.joined_at)}"
#     )
