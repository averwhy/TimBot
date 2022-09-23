import discord

SUPPORT_ROLE = 1022582007399714907

# Defines a simple View that persists between bot restarts
# In order a view to persist between restarts it needs to meet the following conditions:
# 1) The timeout of the View has to be set to None
# 2) Every item in the View has to have a custom_id set
# It is recommended that the custom_id be sufficiently unique to
# prevent conflicts with other buttons the bot sends.
# For this example the custom_id is prefixed with the name of the bot.
# Note that custom_ids can only be up to 100 characters long.
class TicketView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.green, custom_id='timbot:ticketcreate')
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if await self.bot.has_open_ticket(interaction.user):
                return await interaction.response.send_message("You already have an open ticket!", ephemeral=True)

            new_thread = await interaction.channel.create_thread(name=f'Support ticket for {interaction.user.name}',type=discord.ChannelType.private_thread, reason=f'Support ticket opened by {str(interaction.user)} ({interaction.user.id})')
            ticket = await self.bot.create_ticket(interaction.channel, new_thread, interaction.user)
            embed = discord.Embed(title=f"Ticket #{ticket['id']} - {str(interaction.user)}", description="Support staff will be with you shortly. In the meantime, describe your issue so we can help you!\nUse `?solved` to close the ticket.", color=discord.Color.green(), timestamp=discord.utils.utcnow())
            await new_thread.send(content=f"<@{SUPPORT_ROLE}> <@{interaction.user.id}>", embed=embed)
            await interaction.response.send_message(f"Your ticket was created in <#{new_thread.id}>!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"ERROR: {e}")