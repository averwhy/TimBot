import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils.views import TicketView

class Ticketing(commands.Cog):
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
  
  @commands.command(aliases=['close'])
  async def solved(self, ctx):
    """Marks a ticket as solved and closes it. Only works in tickets."""
    if not await self.bot.is_ticket(ctx):
      return # Not in a ticket, so ignore
    
    if not isinstance(ctx.channel, discord.Thread):
      print("The bot thought we were in a ticket however we are not in a thread!????")
      return # Somethings wrong. we should be in a thread

    await ctx.message.add_reaction('✅')
    await self.bot.close_ticket(ctx.channel, ctx.author)
  
  group = app_commands.Group(name="ticket", description="Parent ticket command")

  @group.command(name='setup')
  async def setup(self, interaction: discord.Interaction) -> None:
    """Sets up a ticketing system within the channel that this command was run"""
    try:
      embed = discord.Embed(title="Support Ticket",
        description="Need help? Click the button below to open a ticket!",
        color=discord.Color.green()
      )
      tview = TicketView(self.bot)
      msg = await interaction.response.send_message(embed=embed, view=tview, ephemeral=False)
      await self.bot.add_ticket_button(msg, interaction.channel)
    except Exception as e:
      await interaction.response.send_message(f'ERROR! `{e}`', ephemeral=False)
    
  @group.command(name="list")
  async def _list(self, interaction: discord.Interaction) -> None:
    """View list of tickets"""
    await interaction.response.send_message("-list of tickets-", ephemeral=False)

  @group.command(name="search")
  @app_commands.describe(id="The ticket ID to search for")
  async def search(self, interaction: discord.Interaction, id: int) -> None:
    """Searches all tickets for specified parameter"""
    await interaction.response.send_message(f"ID specified: {id}", ephemeral=False)

async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(Ticketing(bot))