from http.client import CONFLICT
import discord
import asyncio
import asyncpg
import config
import os
from bot import TimBot
from cogs.utils.db import database

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 
os.environ["JISHAKU_HIDE"] = "True"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = TimBot(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('--------------------------------------------------')

async def main():
    if __name__ == "__main__":
        for extension in config.COGS:
            print(f"loading {extension}...",end='')
            try: 
                await bot.load_extension(extension)
                print(" done")
            except Exception as e: print(f"error...{e}")
        
        try:
        # if True:
            pool = await asyncpg.create_pool(user=config.POSTGRES.USER, password=config.POSTGRES.PASSWORD, host=config.POSTGRES.HOST, database=config.POSTGRES.DATABASE)
            bot.db = database(pool) # little wrapper class to make interacting with the database easier
        except Exception as e:
            print(f"fatal: could not load postgres pool. {e}")
        
        await bot.start(config.TOKEN)

asyncio.run(main())