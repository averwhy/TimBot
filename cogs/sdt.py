import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands import RoleConverter
from cogs.utils.views import Questionnaire
from discord.ext.menus import views

ACCESS_ROLE = 1062105350368665640

class sdt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await interaction.response.send_message("An unexpected internal error occured. Let averwhy#3899 know this happened", ephemeral=True)
        raise error

    async def cog_unload(self):
        pass

async def setup(bot):
    await bot.add_cog(sdt(bot))