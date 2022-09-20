import discord
from discord import app_commands
from discord.ext import commands

class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command(aliases=['shutdown','fuckoff','close','cease'])
    async def stop(self, ctx):
        await ctx.send("seeya")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Dev(bot))