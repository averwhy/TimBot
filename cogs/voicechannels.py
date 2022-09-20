import discord
from discord import app_commands
from discord.ext import commands

class VCs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #TODO: design a system that will create a VC when one vc has 2 or more people in it
    # it should also rename a vc based on what majority of users are playing in that vc
    # example: 3/5 players are playing valorant (and it is visible in their activity status)
    # the bot would rename the channel they are in to 'Gaming (Valorant)'

async def setup(bot):
    await bot.add_cog(VCs(bot))