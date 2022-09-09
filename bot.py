import discord
from discord.ext import commands

VARSITY = discord.Object(id=375258840024743937)
PUBLIC = discord.Object(id=628241341482139679)
TESTING = discord.Object(id=724456699280359425)

class TimBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

