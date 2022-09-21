from discord.ext import commands

class Dev(commands.Cog):
    """Commands only for the bot owner"""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)
    
    @commands.command(aliases=['shutdown','fuckoff','close','cease'])
    async def stop(self, ctx):
        await ctx.send("seeya")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Dev(bot))