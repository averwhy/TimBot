import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils.views import SocialSource, DropdownView

class misc(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.Thread): # Is a thread
            messages = [message async for message in message.channel.history(limit=2)]
            if len(messages) == 1: # First message in the thread
                if message.content.strip().lower() == "log book": # Is log book
                    await message.add_reaction("\U0001fab5")

    @app_commands.command(name="socials")
    async def socials(self, interaction: discord.Interaction) -> None:
        """Show's SNHU Esports social links!"""
        view = SocialSource()
        embed = discord.Embed(title="SNHU Esports Socials", description="For a full list of important links, see [this Linktree](https://linktr.ee/snhuesports)", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name='faq')
    async def faq(self, interaction: discord.Interaction) -> None:
        """Frequently asked questions about SNHU Esports!"""
        view = DropdownView()
        embed = discord.Embed(title="Frequently Asked Questions", description="Select a question from the dropdown below to view it's answer!\nDidn't find what you were looking for? Open a ticket!", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(misc(bot))