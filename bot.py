import discord
from discord.ext import commands
from cogs.utils.views import TicketView

VARSITY = discord.Object(id=375258840024743937)
PUBLIC = discord.Object(id=628241341482139679)
TESTING = discord.Object(id=1019294397768138872)

class TimBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents, command_prefix="?")

    async def setup_hook(self):
        self.tree.copy_global_to(guild=TESTING)
        await self.tree.sync(guild=TESTING)
        
        self.add_view(TicketView()) # persistent ticket views

    async def create_ticket(self, ctx: commands.Context):
        """Creates a ticket internally."""
        #async with self.db.pool.acquire() as con:
            #await con.execute("")
        pass
    
    async def inside_ticket(self, ctx: commands.Context):
        """Check if the context's channel is inside of a ticket."""
        pass #TODO: make this a method