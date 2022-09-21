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
        
        self.add_view(TicketView()) # persistent ticket views

    async def create_ticket(self, channel: discord.TextChannel, thread: discord.Thread, author: discord.Member) -> int:
        """Creates a ticket internally.\nReturns: The ID for the newly created ticket."""
        result = await self.db.execute("INSERT INTO tickets VALUES")
        pass
    
    async def get_tickets(t_id: int = None, channel_id: int = None, thread_id: int = None, closed_by: int = None) -> typing.Union[tuple, typing.List[tuple], None]:
        """Searches and returns a ticket based on specified parameters.\nIf no parameters are specified, it returns a `list` of all tickets.\nIf no tickets are found, `None` is returned."""
        pass

    async def is_ticket(self, ctx: commands.Context) -> bool:
        """Check if the context's channel is inside of a ticket."""
        #async with self.db.pool.acquire() as con:
            #await con.execute("")
        pass