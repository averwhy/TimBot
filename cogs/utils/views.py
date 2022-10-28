import traceback
import discord
from discord import PartialEmoji
from discord.ext import menus
from discord.ui import view
from discord import ButtonStyle
SUPPORT_ROLE = 1022582007399714907

# Defines a simple View that persists between bot restarts
# In order a view to persist between restarts it needs to meet the following conditions:
# 1) The timeout of the View has to be set to None
# 2) Every item in the View has to have a custom_id set
# It is recommended that the custom_id be sufficiently unique to
# prevent conflicts with other buttons the bot sends.
# For this example the custom_id is prefixed with the name of the bot.
# Note that custom_ids can only be up to 100 characters long.

twitter = PartialEmoji(name='twitter', id=1027993173663940619)
twitch = PartialEmoji(name='Twitch', id=1027993337757700116)
instagram = PartialEmoji(name='instagram', id=1027993404250017802)
youtube = PartialEmoji(name='youtube', id=1027993434792931404)

class TicketView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.green, custom_id='timbot:ticketcreate')
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if await self.bot.has_open_ticket(interaction.user):
                return await interaction.response.send_message("You already have an open ticket!", ephemeral=True)

            prefix = await self.bot.get_ticket_prefix(interaction.message.id)
            new_thread = await interaction.channel.create_thread(name=f'{prefix} | {str(interaction.user)}',type=discord.ChannelType.private_thread, reason=f'Support ticket opened by {str(interaction.user)} ({interaction.user.id})')
            ticket = await self.bot.create_ticket(interaction.channel, interaction.message, new_thread, interaction.user)
            result = await self.bot.get_roles_to_ping(interaction.message.id)
            roles = [f"<@&{r}>" for r in result]
            embed = discord.Embed(title=f"Ticket #{ticket} - {interaction.user.name}", description="Support staff will be with you shortly. In the meantime, let us know what you need help with!\nUse `?solved` to close the ticket once you're all set.", color=discord.Color.green(), timestamp=discord.utils.utcnow())
            first_message = await new_thread.send(content=f"{' '.join(roles)} <@{interaction.user.id}>", embed=embed)
            await self.bot.update_first_message(first_message, new_thread)
            await interaction.response.send_message(f"Your ticket was created in <#{new_thread.id}>!", ephemeral=True)
        except Exception as e:
            print(traceback.format_exc())

class TicketResultSource(menus.ListPageSource):
    def __init__(self, data, bot):
        self.bot = bot
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        result = [v for i,v in enumerate(entries, start=offset)]
        prefix = await self.bot.get_ticket_prefix(result[2])
        embed = discord.Embed(title=f"Ticket {prefix}-{result[0]}", description=f"Page {menu.current_page+1}/{self.get_max_pages()}")
        owner = await self.bot.fetch_user(result[4])
        jump_link = f"https://discord.com/channels/{result[10]}/{result[5]}/{result[3]}"
        embed.add_field(name='Ticket Owner', value=f'{str(owner)} ({owner.id})')
        embed.add_field(name='Ticket location', value=f'<#{result[3]}>, or [this jumplink]({jump_link})')
        embed.add_field(name='Created', value=f'{discord.utils.format_dt(result[6], "R")}')
        if result[7] == 0: # open ticket
            embed.add_field(name='Status', value='Open')
        if result[7] == 1: # closed ticket
            closedby = await self.bot.fetch_user(result[9])
            embed.add_field(name='Status', value=f'Closed | by {str(closedby)}, {discord.utils.format_dt(result[8], "R")}')
        return embed

class SocialSource(view.View):
    def __init__(self):
        super().__init__()
        self.twitch = "https://www.twitch.tv/snhuesports"
        self.twitter = "https://twitter.com/snhuesports"
        self.instagram = "https://www.instagram.com/snhuesports/"
        self.youtube = "https://www.youtube.com/channel/UC7z4gUo60wx_5Dn5ewuGwwg"
        self.add_item(discord.ui.Button(label='Twitch', url=self.twitch, emoji=twitch, style=ButtonStyle.link))
        self.add_item(discord.ui.Button(label='Twitter', url=self.twitter, emoji=twitter, style=ButtonStyle.link))
        self.add_item(discord.ui.Button(label='Instagram', url=self.instagram, emoji=instagram, style=ButtonStyle.link))
        self.add_item(discord.ui.Button(label='Youtube', url=self.youtube, emoji=youtube, style=ButtonStyle.link))

class Dropdown(discord.ui.Select):
    def __init__(self):
        self.faq_key = {
            1: '**What esports teams are at SNHU?**\nCurrently we have 5 teams that compete! We have Valorant, League of Legends, Overwatch, Super Smash Bros, and Rocket league teams.',
            2: '**How would I join a team?**\nTo join one of our teams, you must be living on campus or close enough to commute since players are required to play in the arena. Keep an eye out for tryout announcements, and good luck!',
            3: '**Where is the arena?**\nOn campus, the Arena is located in the Green Center (Same building as Residence Life and Academic Advising) towards the back of the building. It\'s also close to SETA, if you exited SETA it would be almost straight ahead.',
            4: '**When is the arena open?**\nThese hours are subject to change, but our current open hours are __11am - 5pm__ during the weekdays. We\'re closed on weekends, but keep an eye out for events that are usually on Saturdays!',
            5: '**When do the esports teams play?**\nWe have matches every weeknight! Valorant plays on Monday, Smash Bros play on Tuesday, League of Legends play on Wednesday, Overwatch plays on Thursday, and Rocket League plays on Friday! Our Twitter (`/socials`) has more information on these matches.',
            6: '**Can I watch matches live?**\nYes! If we\'re live casting a match, chances are you can come in and spectate. Bring some friends too!'
        }
        # Set the options that will be presented inside the dropdown
        options = [
            discord.SelectOption(label='What esports teams are at SNHU?', value=1),
            discord.SelectOption(label='How would I join a team?', value=2),
            discord.SelectOption(label='Where is the arena?', value=3),
            discord.SelectOption(label='When is the arena open?', value=4),
            discord.SelectOption(label='When do the esports teams play?', value=5),
            discord.SelectOption(label='Can I watch matches live?', value=6)
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Choose a frequently asked question...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        await interaction.response.send_message(embed=discord.Embed(description=f'{self.faq_key[int(self.values[0])]}', color=discord.Color.gold()), ephemeral=False)


class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        # Adds the dropdown to our view object.
        self.add_item(Dropdown())