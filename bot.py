import typing
import discord
from discord.ext import commands
from cogs.utils.views import TicketView

VARSITY = discord.Object(id=375258840024743937) # will be deprecated soon
PUBLIC = discord.Object(id=628241341482139679)
TESTING = discord.Object(id=937440950739959808)

class TimBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents, command_prefix="?")

    async def setup_hook(self):
        self.tree.copy_global_to(guild=TESTING)
        await self.tree.sync(guild=TESTING)
        
        self.add_view(TicketView(self)) # persistent ticket views

    async def get_id(self, thread: discord.Thread):
        """Gets a ticket ID from a thread ID."""
        result = await self.db.fetch("SELECT id FROM tickets WHERE threadid = $1", thread.id)
        return result[0]

    async def create_ticket(self, channel: discord.TextChannel, thread: discord.Thread, author: discord.Member) -> int:
        """Creates a ticket internally.\nReturns: The ID for the newly created ticket."""
        await self.db.execute("INSERT INTO tickets VALUES (DEFAULT, $1, $2, $3, DEFAULT, DEFAULT, NULL, DEFAULT) RETURNING id;", channel.id, author.id, thread.id)
        tid = await self.get_id(thread)
        return tid

    async def get_tickets(self, t_id: int = None, channel_id: int = None, thread_id: int = None, closed_by: int = None) -> typing.Union[tuple, typing.List[tuple], None]:
        """Searches and returns a ticket based on specified parameters.\nIf no parameters are specified, it returns a `list` of all tickets.\nIf no tickets are found, `None` is returned."""
        pass

    async def close_ticket(self, thread: discord.Thread, closed_by: discord.Member) -> None:
        """Closes a ticket. This justs updates the database with the status number and userid of who closed the ticket.
        It also makes the thread read-only."""
        await self.db.execute("UPDATE tickets SET statuscode = 1, closed=$1, closed_by=$2 WHERE threadid = $3", discord.utils.utcnow().replace(tzinfo=None), closed_by.id, thread.id)
        await thread.send(embed=discord.Embed(description="This ticket was marked as resolved and has now been closed. If you need further support, feel free to open another ticket.", color=0x2F3136))
        await thread.edit(archived=True, locked=True, invitable=False, reason=f"Support thread closed by {str(closed_by)} ({closed_by.id})")

    async def is_ticket(self, ctx: commands.Context) -> bool:
        """Check if the context's channel is inside of a ticket."""
        result = await self.db.execute("SELECT * FROM tickets WHERE threadid = $1 AND statuscode = 0", ctx.channel.id)
        if result:
            return True # is a ticket
        return False # is not a ticket

    async def has_open_ticket(self, user: typing.Union[discord.User, discord.Member]):
        """Checks if an user has an open ticket already"""
        result = await self.db.fetch("SELECT * FROM tickets WHERE ownerid = $1 AND statuscode = 0", user.id)
        print(result)
        if result:
            return True
        return False

    async def add_ticket_button(self, message: discord.InteractionResponse, channel: discord.TextChannel):
        await self.db.execute("INSERT INTO ticket_messages VALUES ($1, $2)", channel.id, message.id)