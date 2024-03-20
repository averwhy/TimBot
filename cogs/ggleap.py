import discord
import csv
import humanize
from dateutil import parser
from discord.ext import commands
from discord import File, app_commands
from .utils.ggLeap import ggAPI, JWT

ACCESS_ROLE = 1062105350368665640
OPERATIONS = 1034506846884610078

class GGLeapCSV:
    data = []
    def __init__(self, file: discord.File):
        file = file.fp()
        with open(file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=' ', quotechar='|')
            for row in reader:
                self.data.append(row)
            print(self.data)
        
    def get_row(self, query: str):
        pass

class ggleap(commands.Cog):
    """Various GGLeap related commands.
    GGLeap is the software used in the SNHU Esports Arena, so if you've created an account in the arena before, you can view it using `?gg user your_username`"""
    def __init__(self, bot):
        self.bot = bot
        with open("GGAUTH.txt", 'r') as t:
            self.tk = t.readline()

        self.jwt = JWT()
        self.api = ggAPI(self.jwt, self.tk)

    def process_csv(self):
        """Processes given CSV's"""

    async def cog_command_error(self, ctx, error: Exception) -> None:
        return await super().cog_command_error(ctx, error)

    async def cog_load(self):
        await self.jwt.renew(self.tk)

    async def cog_unload(self):
        #this should (keyword: should) cleanup ggAPI
        pass

    @commands.command()
    @commands.is_owner()
    async def get_jwt(self, ctx):
        j = JWT()
        await (j).renew(self.tk.strip())
        await ctx.send(f"Response: ```{j.value}\n```")

    @commands.hybrid_group(name='gg')
    async def gg_parent_command(self, ctx):
        """Parent command for interacting with ggLeap. This command does nothing."""
        pass

    @gg_parent_command.command(name='user')
    @commands.guild_only()
    @app_commands.describe(username='The username to search for')
    async def gg_user(self, ctx, username: str):
        """Searches for a ggLeap user and shows their matching profile."""
        await ctx.channel.typing()
        user = None
        if len(username) == 0 or username is None:
            return await ctx.send("Invalid username specified")
        try: user = (await self.api.get_user(username))["User"]
        except KeyError:
            if user is None:
                return await ctx.send("Couldn't find that user <a:no:798969459645218879>")
            #something was returned in a way we weren't expecting
            return await ctx.send("Something went wrong with fetching that user. Tell avery to debug it <:Weirdge:821906833848533075>")

        uuid = user['Uuid']
        created = discord.utils.format_dt(parser.parse(user["RegisteredAt"]), 'R')
        created_full = discord.utils.format_dt(parser.parse(user["RegisteredAt"]), 'F')
        last_seen = discord.utils.format_dt(parser.parse(user["LastSeen"]), 'R')
        last_seen_full = discord.utils.format_dt(parser.parse(user["LastSeen"]), 'F')
        embed = discord.Embed(title=user['Username'], description=f"Registered {created} ({created_full})", color=0x6ba8d4)
        time = humanize.precisedelta((await self.api.get_time(username))['Ttls'][uuid])
        student_id = (user['UserCustomFields']['49b72531-9201-4a6f-a293-8630c2a4051b']['SerializedValue']) if OPERATIONS in [r.id for r in ctx.author.roles] else ("Insufficent Permissions")
        embed.add_field(name="Name", value=f"{user['FirstName']} {user['LastName']}")
        embed.add_field(name="Email", value=user['Email'])
        embed.add_field(name="Time left", value=time)
        embed.add_field(name="Student ID", value=student_id)
        embed.add_field(name="Last seen", value=f"{last_seen} ({last_seen_full})")
        
        await ctx.send(embed=embed)

    @gg_parent_command.command(name='coins')
    @app_commands.describe(username='The username to search for')
    async def gg_coins(self, ctx, username: str):
        """Get's a ggLeap user's coins"""
        if len(username) == 0 or username is None:
            return await ctx.send("Invalid username specified")
        u = await self.api.get_coins(username)
        await ctx.send(u)

    @gg_parent_command.command(name='games')
    async def gg_games(self, ctx):
        """Shows enabled games in the SNHU Esports Arena"""
        raw = await self.api.all_games()

        try: 
            if raw['Apps'] is None:
                return await ctx.send("There are... no games enabled?")
        except KeyError:
            return await ctx.send("Something went wrong. This is GGLeap's fault")
        games = []
        for g in raw['Apps']:
            games.append(g['Name'])
        
        embed = discord.Embed(title="All Games", description="\n".join(games), color=0x6ba8d4)
        embed.set_footer(text="All games available in the SNHU Esports Arena")
        await ctx.send(embed=embed)

    @gg_parent_command.command(name='machines')
    async def gg_pcs(self, ctx):
        """Shows PC's in the SNHU Esports Arena
        ...May include PC's in our Practice room"""
        raw = await self.api.all_games()
        try: 
            if raw['Machines'] is None:
                return await ctx.send("There are... no PC's?")
        except KeyError:
            return await ctx.send("Something went wrong. This is GGLeap's fault")
        games = []
        for g in raw['Machines']:
            games.append(g['Name'])
        
        embed = discord.Embed(title="All PC's", description="\n".join(games), color=0x6ba8d4)
        embed.set_footer(text="All PC's in the SNHU Esports Arena")
        await ctx.send(embed=embed)


    @commands.command(name='csv')
    async def csvproc(self, ctx, csvfile: File = None):
        if csvfile is None:
            try: csvfile = await ctx.message.attachments[0].to_file()
            except IndexError: return await ctx.send("Missing CSV file attachment.. <:gun2:798930540429705256> <:SNHUayayaya:1204573668538327070>")
        ggcsv = GGLeapCSV(csvfile)
        await ctx.send(f"{csv.filename}:\nlen: {len(ggcsv.data)}\n```{ggcsv.data}\n```")

async def setup(bot):
    await bot.add_cog(ggleap(bot))