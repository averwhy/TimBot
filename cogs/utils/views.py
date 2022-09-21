from discord.ext import commands
import discord
from bot import TimBot

# Define a simple View that persists between bot restarts
# In order a view to persist between restarts it needs to meet the following conditions:
# 1) The timeout of the View has to be set to None
# 2) Every item in the View has to have a custom_id set
# It is recommended that the custom_id be sufficiently unique to
# prevent conflicts with other buttons the bot sends.
# For this example the custom_id is prefixed with the name of the bot.
# Note that custom_ids can only be up to 100 characters long.
class TicketView(discord.ui.View):
    def __init__(self, bot: TimBot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.green, custom_id='timbot:ticketcreate')
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        #await interaction.response.send_message('This is green.', ephemeral=True)
        new_thread = await interaction.channel.create_thread(name=f'Support ticket for {interaction.user.name}',type=discord.ChannelType.private_thread, reason=f'Support ticket opened by {str(interaction.user)} ({interaction.user.id})')
        ticket_id = await self.bot.create_ticket(interaction.channel, new_thread, interaction.user)