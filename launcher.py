import discord
from bot import TimBot as bot
import config

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('--------------------------------------------------')

async def main():
    if __name__ == "__main__":
        for extension in initial_extensions:
            try: await bot.load_extension(extension)
            except Exception as e: print(f"Error loading {extension}....{e}")
        
        await bot.start(config.TOKEN)
