import discord
import typing
import importlib
import traceback, sys
from discord import app_commands, ui
from discord.ext import commands
from discord.ext.commands import RoleConverter
from cogs.utils.views import TicketView, TicketResultSource, CustomTicketQuestionnaire
from discord.ext.menus.views import ViewMenuPages

ADMIN = 628244086369026118

class Ticketing(commands.Cog):
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot

  async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    print('Ignoring exception in Ticketing: ', file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    await interaction.response.send_message(f"An unexpected internal error occured:\n{error}``", ephemeral=True)
    raise error

  @commands.Cog.listener()
  async def on_raw_message_delete(self, payload):
    result = await self.bot.pool.execute("SELECT * FROM ticket_messages WHERE messageid = $1", payload.message_id)
    if int(result[7]) != 0: # No results from select
      return # Ignore

    # So now we've detected that a ticket message was deleted, lets update our database
    await self.bot.pool.execute("UPDATE ticket_messages SET deleted = true WHERE messageid = $1", payload.message_id)

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
  
  @commands.hybrid_group()
  async def ticket(self, ctx):
    """Parent ticket command"""
    pass

  @ticket.command(name='setup')
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
  async def setup(self, interaction, title: str, description: str = None, color: str = None,
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

  @ticket.command(name="search")
  @app_commands.describe(ticket_id='ID of the ticket',
                        thread_id='ID of the thread that the ticket was in',
                        closed_by='The ID of the user who closed the ticket',
                        closed='Whether or not the ticket is closed')
  async def search(self, interaction, ticket_id: typing.Union[int, None] = None, thread_id: typing.Union[int, None] = None, closed_by: typing.Union[int, None] = None, closed: typing.Union[bool, None] = None) -> None:
    """Searches all tickets for matching parameters. Leave all arguments blank for a list of all tickets.
    If you're using the none slash command version and want to, for example, search for only closed tickets,
    you would use this syntax: `?ticket search None None None True`
    Or, closed tickets by a certain user: `?ticket search none none @averwhy True"""
    # if ADMIN not in interaction.user.roles or interaction.user.id != self.bot.owner_id:
    #   return await interaction.response.send_message("You must be an admin to run this command!", ephemeral=True)
    result = await self.bot.get_tickets(ticket_id=ticket_id, thread_id=thread_id, closed_by=closed_by, closed=closed)
    if len(result) == 0:
      await interaction.send("No tickets found with those parameters")
    pages = ViewMenuPages(source=TicketResultSource(result, self.bot), clear_reactions_after=True)
    await pages.start(interaction, channel=interaction.channel)

  @ticket.command(name="for")
  @app_commands.describe(user='The user to create the ticket for', ticket="The ticket prefix e.g. 'TECH' to create the ticket under")
  async def ticket_for(self, interaction, ticket: str, user: discord.Member):
    """Creates a ticket for a specified user. Arena Operations and Moderator+ only."""
    result = await self.bot.pool.execute("SELECT channelid, messageid FROM ticket_messages WHERE threadprefix = $1", ticket)
    if result[0].get('channelid') is None:
      return await interaction.send("Couldn't find the ticket type from that prefix")
    channel = self.bot.get_channel(result[0].get('channelid'))
    message = await channel.fetch_message(result[0].get('messageid'))

    new_interaction = None
    form_results = []
    if await self.bot.ticket_uses_form(message.id):
      form_questions = await self.bot.get_ticket_form_fields(message.id)
      if len(form_questions) <= 0:
          # eeeh
          pass
      form = CustomTicketQuestionnaire()
      for q in form_questions:
          form.add_item(ui.TextInput(label=q[0], required=q[1], style=discord.TextStyle.long))
      # TODO: \/ that
      await interaction.response.send_modal(form)
      await form.wait()
      new_interaction = form.interaction
      form_results = form.children

    prefix = await self.bot.get_ticket_prefix(message.id)
    new_thread = await channel.create_thread(name=f'{prefix} | {str(user)}',type=discord.ChannelType.private_thread, reason=f'Support ticket opened by {str(user)} ({user.id})')
    ticket = await self.bot.create_ticket(channel, message, new_thread, user, form_response=form_results)
    result = await self.bot.get_roles_to_ping(message.id)
    roles = [f"<@&{r}>" for r in result]
    embed = discord.Embed(title=f"Ticket #{ticket} - {user.name}", description="Support staff will be with you shortly. In the meantime, let us know what you need help with!\nUse `?solved` to close the ticket once you're all set.", color=discord.Color.green(), timestamp=discord.utils.utcnow())
    if new_interaction is not None: # this will run if the ticket has a form
      interaction = new_interaction #if there was a form that was done, we will use the old interaction to create everything needed, then respond using the new inteaction from the form
      for r in form_results:
        embed.add_field(name=r.label, value=(r.value if len(r.value) != 0 else "*No response*"))
    first_message = await new_thread.send(content=f"{' '.join(roles)} <@{user.id}>", embed=embed)
    await self.bot.update_first_message(first_message, new_thread)
    await interaction.response.send_message(f"Your ticket was created in <#{new_thread.id}>!", ephemeral=True)

  @ticket.command(name="edit")
  async def edit(self, interaction):
    """Edits a existing ticket system. Admins only. 
    **WIP**"""
    pass
  


async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(Ticketing(bot))