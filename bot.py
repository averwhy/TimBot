from __future__ import annotations

from discord.ext import commands
import discord
from cogs.utils.config import Config
from cogs.utils.context import Context
import datetime
import logging
import traceback
import aiohttp
import sys
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Coroutine, Iterable, Optional, Union
import typing
from types import NoneType
from collections import Counter, defaultdict

import config
import asyncpg

if TYPE_CHECKING:
    from cogs.reminder import Reminder
    from cogs.config import Config as ConfigCog

from cogs.utils.views import TicketView, SDTRuleView
from config import ERROR_CHANNEL


description = """
Hello! I am a bot for the SNHU Esports Discord, put together by averwhy.
"""

log = logging.getLogger(__name__)

initial_extensions = (
    'cogs.meta',
    'cogs.rng',
    'cogs.mod',
    'cogs.tags',
    'cogs.admin',
    'cogs.buttons',
    'cogs.reminder',
    'cogs.stats',
    'cogs.emoji',
    'cogs.config',
    'cogs.funhouse',
    'cogs.todo',
    'cogs.minigames',

    #custom cogs:
    'cogs.ticketing',
    #'cogs.twitter',    # disabled bc of twitter api Classic
    'cogs.misc',
    'jishaku'
)


def _prefix_callable(bot: RoboTim, msg: discord.Message):
    user_id = bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ']
    if msg.guild is None:
        base.append('!')
        base.append('?')
    else:
        base.extend(bot.prefixes.get(msg.guild.id, ['?', '!']))
    return base


class ProxyObject(discord.Object):
    def __init__(self, guild: Optional[discord.abc.Snowflake]):
        super().__init__(id=0)
        self.guild: Optional[discord.abc.Snowflake] = guild


class RoboTim(commands.AutoShardedBot):
    user: discord.ClientUser
    pool: asyncpg.Pool
    command_stats: Counter[str]
    socket_stats: Counter[str]
    command_types_used: Counter[bool]
    logging_handler: Any
    bot_app_info: discord.AppInfo
    old_tree_error = Callable[[discord.Interaction, discord.app_commands.AppCommandError], Coroutine[Any, Any, None]]

    def __init__(self):
        allowed_mentions = discord.AllowedMentions(roles=True, everyone=True, users=True)
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True,
            message_content=True,
        )
        super().__init__(
            command_prefix=_prefix_callable,
            description=description,
            pm_help=None,
            help_attrs=dict(hidden=True),
            chunk_guilds_at_startup=False,
            heartbeat_timeout=150.0,
            allowed_mentions=allowed_mentions,
            intents=intents,
            enable_debug_events=True,
        )

        self.client_id: str = config.client_id

        # shard_id: List[datetime.datetime]
        # shows the last attempted IDENTIFYs and RESUMEs
        self.resumes: defaultdict[int, list[datetime.datetime]] = defaultdict(list)
        self.identifies: defaultdict[int, list[datetime.datetime]] = defaultdict(list)

        # in case of even further spam, add a cooldown mapping
        # for people who excessively spam commands
        self.spam_control = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)

        # A counter to auto-ban frequent spammers
        # Triggering the rate limit 5 times in a row will auto-ban the user from the bot.
        self._auto_spam_count = Counter()

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()
        # guild_id: list
        self.prefixes: Config[list[str]] = Config('prefixes.json')

        # guild_id and user_id mapped to True
        # these are users and guilds globally blacklisted
        # from using the bot
        self.blacklist: Config[bool] = Config('blacklist.json')

        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id

        self.add_view(SDTRuleView(self))
        self.add_view(TicketView(self)) # persistent ticket views

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                log.exception('Failed to load extension %s.', extension)

    
    async def get_id(self, thread: discord.Thread):
        """Gets a ticket ID from a thread ID."""
        result = await self.pool.fetch("SELECT id FROM tickets WHERE threadid = $1", thread.id)
        return result[0].get('id')

    async def create_ticket(self, channel: discord.TextChannel, from_message: discord.Message, thread: discord.Thread, author: discord.Member, form_response: list = None) -> int:
        """Creates a ticket internally.\nReturns: The ID for the newly created ticket."""
        if form_response is not None:
            await self.pool.execute("INSERT INTO tickets VALUES (DEFAULT, $1, $2, 0, $3, $4, DEFAULT, DEFAULT, NULL, DEFAULT, $5, $6) RETURNING id;", channel.id, from_message.id, author.id, thread.id, author.guild.id, [f.value for f in form_response])
        await self.pool.execute("INSERT INTO tickets VALUES (DEFAULT, $1, $2, 0, $3, $4, DEFAULT, DEFAULT, NULL, DEFAULT, $5) RETURNING id;", channel.id, from_message.id, author.id, thread.id, author.guild.id)
        tid = await self.get_id(thread)
        return int(tid)

    async def update_first_message(self, first_message: discord.Message, ticket_thread: discord.Thread):
        """Updates the ticket entry with the first message of the thread."""
        return await self.pool.execute("UPDATE tickets SET firstmessage = $1 WHERE threadid = $2", first_message.id, ticket_thread.id)

    async def get_tickets(self, ticket_id: int = None, thread_id: int = None, closed_by: int = None, closed: bool = None) -> typing.Union[tuple, typing.List[tuple], None]:
        """Searches and returns a ticket based on specified parameters.\nIf no parameters are specified, it returns a `list` of all tickets.\nIf no tickets are found, `None` is returned."""
        results = []
        if ticket_id:
            result = await self.pool.fetch("SELECT * FROM tickets WHERE id = $1", ticket_id)
            if result: 
                for r in result: results.append(r)
        if thread_id:
            result = await self.pool.fetch("SELECT * FROM tickets WHERE threadid = $1", thread_id)
            if result: 
                for r in result: results.append(r)
        if closed_by:
            result = await self.pool.fetch("SELECT * FROM tickets WHERE closed_by = $1", closed_by)
            if result: 
                for r in result: results.append(r)
        if closed is not None:
            if closed:
                result = await self.pool.fetch("SELECT * FROM tickets WHERE ticketstatus = 1")
            else:
                result = await self.pool.fetch("SELECT * FROM tickets WHERE ticketstatus = 0")
            if result: 
                for r in result: results.append(r)
        if all([isinstance(item, NoneType) for item in (ticket_id, thread_id, closed_by)]):
            return await self.pool.fetch("SELECT * FROM tickets")
        print(results)
        return results
    #TODO: Find out a way to combine results. Stuck because tuples are immutable
    # Maybe cast to list using list(results)?

    async def close_ticket(self, thread: discord.Thread, closed_by: discord.Member) -> None:
        """Closes a ticket. This justs updates the database with the status number and userid of who closed the ticket.
        It also makes the thread read-only."""
        await self.pool.execute("UPDATE tickets SET statuscode = 1, closed=$1, closed_by=$2 WHERE threadid = $3", discord.utils.utcnow().replace(tzinfo=None), closed_by.id, thread.id)
        await thread.send(embed=discord.Embed(description="This ticket was marked as resolved and has now been closed. If you need further support, feel free to open another ticket.", color=0x2F3136))
        await thread.edit(archived=True, locked=True, invitable=False, reason=f"Support thread closed by {str(closed_by)} ({closed_by.id})")

    async def is_ticket(self, ctx: commands.Context) -> bool:
        """Check if the context's channel is inside of a ticket."""
        result = await self.pool.execute("SELECT * FROM tickets WHERE threadid = $1 AND statuscode = 0", ctx.channel.id)
        if result:
            return True # is a ticket
        return False # is not a ticket

    async def has_open_ticket(self, user: typing.Union[discord.User, discord.Member]) -> bool:
        """Checks if an user has an open ticket already"""
        result = await self.pool.fetch("SELECT * FROM tickets WHERE ownerid = $1 AND statuscode = 0", user.id)
        if result:
            return True
        return False
    
    async def ticket_uses_form(self, message_id: int):
        result = await self.pool.fetch("SELECT use_form FROM ticket_messages WHERE messageid = $1", message_id)
        if result[0].get('use_form') is True:
            return True
        return False

    async def get_ticket_form_fields(self, message_id: int):
        results = await self.pool.fetch("SELECT * FROM ticket_form_values WHERE for_tid = $1", message_id)
        fields = []
        for r in results:
            fields.append([r.get('name'), r.get('required')])
        return fields

    async def get_ticket_prefix(self, message_id: int) -> str:
        """Gets the ticket menu's prefix from the database"""
        result = await self.pool.fetch("SELECT threadprefix FROM ticket_messages WHERE messageid = $1", message_id)
        return result[0].get('threadprefix')
    
    async def get_roles_to_ping(self, message_id: int) -> list:
        """Gets a list of role ID's to ping, based on the ticket"""
        result = await self.pool.fetch("SELECT rolestoping FROM ticket_messages WHERE messageid = $1", message_id)
        if result[0].get('rolestoping') is None:
            return None
        return list(result[0].get('rolestoping').strip(',').split(','))

    async def add_ticket_button(self, message: discord.InteractionResponse, channel: discord.TextChannel, ticket_prefix: str = '', roles: list = None):
        if roles is None or len(roles) == 0:
            return await self.pool.execute("INSERT INTO ticket_messages VALUES ($1, $2, $3)", channel.id, message.id, ticket_prefix)
        return await self.pool.execute("INSERT INTO ticket_messages VALUES ($1, $2, $3, $4)", channel.id, message.id, ticket_prefix, roles)

    async def get_target_category(self, message_id: int):
        return (await self.pool.fetch("SELECT * FROM channel_makers WHERE targetcategory = $1", message_id))[2]

    async def error_log(self, error: Exception = None, message: str = None):
        channel = await self.fetch_channel(ERROR_CHANNEL)
        msg = f"<@267410788996743168>: Error at {discord.utils.format_dt(discord.utils.utcnow(), 'R')}\n{error}\n{message}"
        await channel.send(msg)

    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner

    def _clear_gateway_data(self) -> None:
        one_week_ago = discord.utils.utcnow() - datetime.timedelta(days=7)
        for shard_id, dates in self.identifies.items():
            to_remove = [index for index, dt in enumerate(dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

        for shard_id, dates in self.resumes.items():
            to_remove = [index for index, dt in enumerate(dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

    async def before_identify_hook(self, shard_id: int, *, initial: bool):
        self._clear_gateway_data()
        self.identifies[shard_id].append(discord.utils.utcnow())
        await super().before_identify_hook(shard_id, initial=initial)

    async def on_command_error(self, ctx: Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                log.exception('In %s:', ctx.command.qualified_name, exc_info=original)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(str(error))

    def get_guild_prefixes(self, guild: Optional[discord.abc.Snowflake], *, local_inject=_prefix_callable) -> list[str]:
        proxy_msg = ProxyObject(guild)
        return local_inject(self, proxy_msg)  # type: ignore  # lying

    def get_raw_guild_prefixes(self, guild_id: int) -> list[str]:
        return self.prefixes.get(guild_id, ['?', '!'])

    async def set_guild_prefixes(self, guild: discord.abc.Snowflake, prefixes: list[str]) -> None:
        if len(prefixes) == 0:
            await self.prefixes.put(guild.id, [])
        elif len(prefixes) > 10:
            raise RuntimeError('Cannot have more than 10 custom prefixes.')
        else:
            await self.prefixes.put(guild.id, sorted(set(prefixes), reverse=True))

    async def add_to_blacklist(self, object_id: int):
        await self.blacklist.put(object_id, True)

    async def remove_from_blacklist(self, object_id: int):
        try:
            await self.blacklist.remove(object_id)
        except KeyError:
            pass

    async def query_member_named(
        self, guild: discord.Guild, argument: str, *, cache: bool = False
    ) -> Optional[discord.Member]:
        """Queries a member by their name, name + discrim, or nickname.

        Parameters
        ------------
        guild: Guild
            The guild to query the member in.
        argument: str
            The name, nickname, or name + discrim combo to check.
        cache: bool
            Whether to cache the results of the query.

        Returns
        ---------
        Optional[Member]
            The member matching the query or None if not found.
        """
        if len(argument) > 5 and argument[-5] == '#':
            username, _, discriminator = argument.rpartition('#')
            members = await guild.query_members(username, limit=100, cache=cache)
            return discord.utils.get(members, name=username, discriminator=discriminator)
        else:
            members = await guild.query_members(argument, limit=100, cache=cache)
            return discord.utils.find(lambda m: m.name == argument or m.nick == argument, members)

    async def get_or_fetch_member(self, guild: discord.Guild, member_id: int) -> Optional[discord.Member]:
        """Looks up a member in cache or fetches if not found.

        Parameters
        -----------
        guild: Guild
            The guild to look in.
        member_id: int
            The member ID to search for.

        Returns
        ---------
        Optional[Member]
            The member or None if not found.
        """

        member = guild.get_member(member_id)
        if member is not None:
            return member

        shard: discord.ShardInfo = self.get_shard(guild.shard_id)  # type: ignore  # will never be None
        if shard.is_ws_ratelimited():
            try:
                member = await guild.fetch_member(member_id)
            except discord.HTTPException:
                return None
            else:
                return member

        members = await guild.query_members(limit=1, user_ids=[member_id], cache=True)
        if not members:
            return None
        return members[0]

    async def resolve_member_ids(self, guild: discord.Guild, member_ids: Iterable[int]) -> AsyncIterator[discord.Member]:
        """Bulk resolves member IDs to member instances, if possible.

        Members that can't be resolved are discarded from the list.

        This is done lazily using an asynchronous iterator.

        Note that the order of the resolved members is not the same as the input.

        Parameters
        -----------
        guild: Guild
            The guild to resolve from.
        member_ids: Iterable[int]
            An iterable of member IDs.

        Yields
        --------
        Member
            The resolved members.
        """

        needs_resolution = []
        for member_id in member_ids:
            member = guild.get_member(member_id)
            if member is not None:
                yield member
            else:
                needs_resolution.append(member_id)

        total_need_resolution = len(needs_resolution)
        if total_need_resolution == 1:
            shard: discord.ShardInfo = self.get_shard(guild.shard_id)  # type: ignore  # will never be None
            if shard.is_ws_ratelimited():
                try:
                    member = await guild.fetch_member(needs_resolution[0])
                except discord.HTTPException:
                    pass
                else:
                    yield member
            else:
                members = await guild.query_members(limit=1, user_ids=needs_resolution, cache=True)
                if members:
                    yield members[0]
        elif total_need_resolution <= 100:
            # Only a single resolution call needed here
            resolved = await guild.query_members(limit=100, user_ids=needs_resolution, cache=True)
            for member in resolved:
                yield member
        else:
            # We need to chunk these in bits of 100...
            for index in range(0, total_need_resolution, 100):
                to_resolve = needs_resolution[index : index + 100]
                members = await guild.query_members(limit=100, user_ids=to_resolve, cache=True)
                for member in members:
                    yield member

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = discord.utils.utcnow()

        log.info('Ready: %s (ID: %s)', self.user, self.user.id)

    async def on_shard_resumed(self, shard_id: int):
        log.info('Shard ID %s has resumed...', shard_id)
        self.resumes[shard_id].append(discord.utils.utcnow())

    @discord.utils.cached_property
    def stats_webhook(self) -> discord.Webhook:
        wh_id, wh_token = self.config.stat_webhook
        hook = discord.Webhook.partial(id=wh_id, token=wh_token, session=self.session)
        return hook

    async def log_spammer(self, ctx: Context, message: discord.Message, retry_after: float, *, autoblock: bool = False):
        guild_name = getattr(ctx.guild, 'name', 'No Guild (DMs)')
        guild_id = getattr(ctx.guild, 'id', None)
        fmt = 'User %s (ID %s) in guild %r (ID %s) spamming, retry_after: %.2fs'
        log.warning(fmt, message.author, message.author.id, guild_name, guild_id, retry_after)
        if not autoblock:
            return

        wh = self.stats_webhook
        embed = discord.Embed(title='Auto-blocked Member', colour=0xDDA453)
        embed.add_field(name='Member', value=f'{message.author} (ID: {message.author.id})', inline=False)
        embed.add_field(name='Guild Info', value=f'{guild_name} (ID: {guild_id})', inline=False)
        embed.add_field(name='Channel Info', value=f'{message.channel} (ID: {message.channel.id}', inline=False)
        embed.timestamp = discord.utils.utcnow()
        return await wh.send(embed=embed)

    async def get_context(self, origin: Union[discord.Interaction, discord.Message], /, *, cls=Context) -> Context:
        return await super().get_context(origin, cls=cls)

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        if ctx.author.id in self.blacklist:
            return

        if ctx.guild is not None and ctx.guild.id in self.blacklist:
            return

        bucket = self.spam_control.get_bucket(message)
        current = message.created_at.timestamp()
        retry_after = bucket and bucket.update_rate_limit(current)
        author_id = message.author.id
        if retry_after and author_id != self.owner_id:
            self._auto_spam_count[author_id] += 1
            if self._auto_spam_count[author_id] >= 5:
                await self.add_to_blacklist(author_id)
                del self._auto_spam_count[author_id]
                await self.log_spammer(ctx, message, retry_after, autoblock=True)
            else:
                await self.log_spammer(ctx, message, retry_after)
            return
        else:
            self._auto_spam_count.pop(author_id, None)

        await self.invoke(ctx)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        if guild.id in self.blacklist:
            await guild.leave()

    async def close(self) -> None:
        await super().close()
        await self.session.close()

    async def start(self) -> None:
        await super().start(config.token, reconnect=True)

    @property
    def config(self):
        return __import__('config')

    @property
    def reminder(self) -> Optional[Reminder]:
        return self.get_cog('Reminder')  # type: ignore

    @property
    def config_cog(self) -> Optional[ConfigCog]:
        return self.get_cog('Config')  # type: ignore
