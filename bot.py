from types import NoneType
import typing
import discord
from discord.ext import commands
from cogs.utils.views import TicketView, SocialSource

VARSITY = discord.Object(id=375258840024743937) # will be deprecated soon
PUBLIC = discord.Object(id=628241341482139679)
TESTING = discord.Object(id=937440950739959808)

class TimBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents, command_prefix="?")

    async def setup_hook(self):
        self.tree.copy_global_to(guild=PUBLIC)
        await self.tree.sync(guild=PUBLIC)
        
        self.add_view(TicketView(self)) # persistent ticket views

    async def get_id(self, thread: discord.Thread):
        """Gets a ticket ID from a thread ID."""
        result = await self.db.fetch("SELECT id FROM tickets WHERE threadid = $1", thread.id)
        return result[0].get('id')

    async def create_ticket(self, channel: discord.TextChannel, from_message: discord.Message, thread: discord.Thread, author: discord.Member) -> int:
        """Creates a ticket internally.\nReturns: The ID for the newly created ticket."""
        await self.db.execute("INSERT INTO tickets VALUES (DEFAULT, $1, $2, 0, $3, $4, DEFAULT, DEFAULT, NULL, DEFAULT, $5) RETURNING id;", channel.id, from_message.id, author.id, thread.id, author.guild.id)
        tid = await self.get_id(thread)
        return int(tid)

    async def update_first_message(self, first_message: discord.Message, ticket_thread: discord.Thread):
        """Updates the ticket entry with the first message of the thread."""
        return await self.db.execute("UPDATE tickets SET firstmessage = $1 WHERE threadid = $2", first_message.id, ticket_thread.id)

    async def get_tickets(self, ticket_id: int = None, thread_id: int = None, closed_by: int = None, closed: bool = None) -> typing.Union[tuple, typing.List[tuple], None]:
        """Searches and returns a ticket based on specified parameters.\nIf no parameters are specified, it returns a `list` of all tickets.\nIf no tickets are found, `None` is returned."""
        results = []
        if ticket_id:
            result = await self.db.fetch("SELECT * FROM tickets WHERE id = $1", ticket_id)
            if result: 
                for r in result: results.append(r)
        if thread_id:
            result = await self.db.fetch("SELECT * FROM tickets WHERE threadid = $1", thread_id)
            if result: 
                for r in result: results.append(r)
        if closed_by:
            result = await self.db.fetch("SELECT * FROM tickets WHERE closed_by = $1", closed_by)
            if result: 
                for r in result: results.append(r)
        if closed is not None:
            if closed:
                result = await self.db.fetch("SELECT * FROM tickets WHERE ticketstatus = 1")
            else:
                result = await self.db.fetch("SELECT * FROM tickets WHERE ticketstatus = 0")
            if result: 
                for r in result: results.append(r)
        if all([isinstance(item, NoneType) for item in (ticket_id, thread_id, closed_by)]):
            return await self.db.fetch("SELECT * FROM tickets")
        print(results)
        return results
    #TODO: Find out a way to combine results. Stuck because tuples are immutable
    # Maybe cast to list using list(results)?

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

    async def has_open_ticket(self, user: typing.Union[discord.User, discord.Member]) -> bool:
        """Checks if an user has an open ticket already"""
        result = await self.db.fetch("SELECT * FROM tickets WHERE ownerid = $1 AND statuscode = 0", user.id)
        if result:
            return True
        return False

    async def get_ticket_prefix(self, message_id: int) -> str:
        """Gets the ticket menu's prefix from the database"""
        result = await self.db.fetch("SELECT threadprefix FROM ticket_messages WHERE messageid = $1", message_id)
        return result[0].get('threadprefix')
    
    async def get_roles_to_ping(self, message_id: int) -> list:
        """Gets a list of role ID's to ping, based on the ticket"""
        result = await self.db.fetch("SELECT rolestoping FROM ticket_messages WHERE messageid = $1", message_id)
        if result[0].get('rolestoping') is None:
            return None
        return list(result[0].get('rolestoping').strip(',').split(','))

    async def add_ticket_button(self, message: discord.InteractionResponse, channel: discord.TextChannel, ticket_prefix: str = '', roles: list = None):
        if roles is None or len(roles) == 0:
            return await self.db.execute("INSERT INTO ticket_messages VALUES ($1, $2, $3)", channel.id, message.id, ticket_prefix)
        return await self.db.execute("INSERT INTO ticket_messages VALUES ($1, $2, $3, $4)", channel.id, message.id, ticket_prefix, roles)