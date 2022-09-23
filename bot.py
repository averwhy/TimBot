import typing
import discord
from discord.ext import commands
from cogs.utils.views import TicketView

VARSITY = discord.Object(id=375258840024743937) # will be deprecated soon
PUBLIC = discord.Object(id=628241341482139679)
TESTING = discord.Object(id=1019294397768138872)

class TimBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents, command_prefix="?")

    async def setup_hook(self):
        self.tree.copy_global_to(guild=TESTING)
        await self.tree.sync(guild=TESTING)
        
        self.add_view(TicketView(self)) # persistent ticket views

    async def create_ticket(self, channel: discord.TextChannel, thread: discord.Thread, author: discord.Member) -> int:
        """Creates a ticket internally.\nReturns: The ID for the newly created ticket."""
        result = await self.db.execute("INSERT INTO tickets VALUES (DEFAULT, $1, $2, $3, DEFAULT, DEFAULT, NULL, DEFAULT) RETURNING id;", channel.id, author.id, thread.id)
        return result
    
    async def get_tickets(self, t_id: int = None, channel_id: int = None, thread_id: int = None, closed_by: int = None) -> typing.Union[tuple, typing.List[tuple], None]:
        """Searches and returns a ticket based on specified parameters.\nIf no parameters are specified, it returns a `list` of all tickets.\nIf no tickets are found, `None` is returned."""
        pass

    async def close_ticket(self, thread: discord.Thread, closed_by: discord.Member) -> None:
        """Closes a ticket. This justs updates the database with the status number and userid of who closed the ticket.
        It also makes the thread read-only."""
        await self.db.execute("UPDATE tickets SET status = 1, closed=$1, closed_by=$2 WHERE threadid = $3", discord.utils.utcnow(), closed_by.id, thread.id)
        await thread.edit(locked=True, invitable=False, reason=f"Support thread closed by {str(closed_by)} ({closed_by.id})")
        print(f"closed thread {thread.id}")

    async def is_ticket(self, ctx: commands.Context) -> bool:
        """Check if the context's channel is inside of a ticket."""
        result = await self.db.execute("SELECT * FROM tickets WHERE threadid = $1 AND status = 0", ctx.channel.id)
        if result:
            return True # is a ticket
        return False # is not a ticket