import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands import RoleConverter
from cogs.utils.views import TicketView, TicketResultSource
from discord.ext.menus import views

ADMIN = 628244086369026118

class Ticketing(commands.Cog):
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
  
  async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    await interaction.response.send_message("An unexpected internal error occured. Let averwhy#3899 know this happened", ephemeral=True)
    raise error

  @commands.Cog.listener()
  async def on_raw_message_delete(self, payload):
    result = await self.bot.db.execute("SELECT * FROM ticket_messages WHERE messagedid = $1", payload.message_id)
    if int(result[7]) != 0: # No results from select
      return # Ignore

    # So now we've detected that a ticket message was deleted, lets update our database
    await self.bot.db.execute("UPDATE ticket_messages SET deleted = true WHERE messageid = $1", payload.message_id)

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
  @app_commands.describe(title='The title of the embed (Required)',
    description='The description of the embed',
    color='The color of the embed',
    thumbnail_url='The direct URL link to an image that will be displayed as the thumbail',
    image_url='The direct URL link to an image that will be displayed as a full image',
    author='The text to display in the \'author\' section of the embed',
    footer='The text to display in the footer of the embed',
    ticket_prefix='The prefix that appears at the beginning of the thread\'s name. Max 4 characters.',
    roles_to_ping='The roles to ping when a ticket is created. Can be multiple roles, and also can be role names or ID\'s.'
  )
  async def setup(self, interaction: discord.Interaction, title: str, description: str = None, color: str = None,
  thumbnail_url: str = None, image_url: str = None, author: str = None, footer: str = None,
  ticket_prefix: str = None, *, roles_to_ping: str = None) -> None:
    """Sets up a customizable ticketing system. Admins only."""
    #if (ADMIN not in [r.id for r in interaction.user.roles]) or (interaction.user.id != self.bot.owner_id):
    #  return await interaction.response.send_message("You must be an admin to run this command!", ephemeral=True)

    ctx = await self.bot.get_context(interaction)
    if ticket_prefix:
      if len(ticket_prefix) > 4:
        return await interaction.response.send_message("The ticket prefix cannot be longer than 4 characters!", ephemeral=True)
      ticket_prefix = ticket_prefix.upper()
    
    try: color = await commands.ColorConverter().convert(ctx, color)
    except commands.BadArgument:
      return await interaction.response.send_message(f"I couldn't convert the color {color} for you. Try again?", ephemeral=True)

    roles = ""
    if roles_to_ping:
      for r in roles_to_ping:
        converter = RoleConverter()
        try: result = await converter.convert(ctx, r)
        except Exception:
          continue
        roles += f"{result.id},"
      roles = roles.strip(',')
    
    embed = discord.Embed(title=title or 'Open a ticket',
      description=description or 'Need help? Click the button below to open a ticket!',
      color=color or discord.Color.green(),
    )
    if thumbnail_url:
      embed.set_thumbnail(url=thumbnail_url)
    if image_url:
      embed.set_image(url=image_url)
    if author:
      embed.set_author(name=author)
    if footer:
      embed.set_footer(text=footer)
    tview = TicketView(self.bot)

    msg = await interaction.channel.send(embed=embed, view=tview)
    await self.bot.add_ticket_button(msg, interaction.channel, ticket_prefix, roles)
    await interaction.response.send_message(f"Done! To remove the ticket embed, use the command `?config remove {msg.id}`", ephemeral=True)

  @group.command(name="search")
  @app_commands.describe(ticket_id='ID of the ticket',
                        thread_id='ID of the thread that the ticket was in',
                        closed_by='The ID of the user who closed the ticket',
                        closed='Whether or not the ticket is closed')
  async def search(self, interaction: discord.Interaction, ticket_id: int = None, thread_id: int = None, closed_by: int = None, closed: bool = None) -> None:
    """Searches all tickets for matching parameters. Leave all arguments blank for a list of all tickets."""
    # if ADMIN not in interaction.user.roles or interaction.user.id != self.bot.owner_id:
    #   return await interaction.response.send_message("You must be an admin to run this command!", ephemeral=True)
    result = await self.bot.get_tickets(ticket_id=ticket_id, thread_id=thread_id, closed_by=closed_by, closed=closed)
    pages = views.ViewMenuPages(source=TicketResultSource(result, self.bot), clear_reactions_after=True)
    await pages.start(interaction, channel=interaction.channel, bot=self.bot)

async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(Ticketing(bot))