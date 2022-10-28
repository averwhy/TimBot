import discord
from discord.ext import commands
from discord.ext.commands.converter import PartialEmojiConverter, PartialEmojiConversionFailure

class Dev(commands.Cog):
    """Commands only for the bot owner"""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.bot.process_commands(after) # enable edit commands
    
    @commands.command(aliases=['shutdown','fuckoff','cease'], hidden=True)
    async def stop(self, ctx):
        await ctx.send("seeya")
        await self.bot.close()
    
    @commands.command(hidden=True, aliases=['ce'])
    async def clone_emote(self, ctx, emote: str, name: str = None):
        """Clones emote to the server this is called in. Can specify a name but it's optional"""
        converter = PartialEmojiConverter()
        try:
            emote = await converter.convert(ctx, emote)
        except PartialEmojiConversionFailure:
            return await ctx.send("Couldn't convert that emote, try again")
        
        try:
            new_emote = await ctx.guild.create_custom_emoji(name=(name or emote.name), image=await emote.read(), reason=f"Cloned emote done by {str(ctx.author)}")
            return await ctx.send(f"Done, heres the new emote: {new_emote} ({new_emote.id})")
        except discord.Forbidden:
            return await ctx.send("I don't have permissions to clone the emote lol")


async def setup(bot):
    await bot.add_cog(Dev(bot))