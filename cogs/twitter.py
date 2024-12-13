import discord
import tweepy
import asyncio
from discord import app_commands
from discord.ext import commands
import config
from tweepy.asynchronous.streaming import AsyncStreamingClient
from tweepy.asynchronous import AsyncClient

TWITTER_CHANNEL = 1035600425195413504

class EsportsStream(AsyncStreamingClient):
    def __init__(self, bot, token):
        self.bot = bot
        super().__init__(bearer_token=token, wait_on_rate_limit=True)

    async def on_tweet(self, tweet): 
        if tweet.created_at is None:
            tweet_created = discord.utils.utcnow()
        else: tweet_created = tweet.created_at
        channel = await self.bot.fetch_channel(TWITTER_CHANNEL)
        msg = await channel.send(content=f"{discord.utils.format_dt(tweet_created, 'R')}, https://twitter.com/SNHUEsports/status/{tweet.id}")
        await asyncio.sleep(0.1)
        await msg.publish()
    
    async def on_closed(self, resp):
        await self.bot.error_log(message=f"Twitter closed the stream for some reason: {resp}")

class twitter(commands.Cog):
    def __init__(self, bot, twitter_task: asyncio.Task) -> None:
        self.bot = bot
        self.channel_id = 1035600425195413504
        self.bot.twitter_task = twitter_task
    
    async def cog_unload(self):
        self.bot.twitter_task.disconnect()
    
async def setup(bot: commands.Bot):
    rule = tweepy.StreamRule(value="from:SNHUesports", tag="esports", id="esports")
    stream = EsportsStream(bot, bearer_token=config.TWITTER.TOKEN)
    #print(await stream.get_rules())
    await stream.add_rules(add=rule)
    twitter_task = stream.filter(user_fields=['username'])
    await bot.add_cog(twitter(bot, twitter_task))