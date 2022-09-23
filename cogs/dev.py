from discord.ext import commands

class Dev(commands.Cog):
    """Commands only for the bot owner"""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.bot.process_commands(after) # enable edit commands
    
    @commands.command(aliases=['shutdown','fuckoff','cease'])
    async def stop(self, ctx):
        await ctx.send("seeya")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Dev(bot))