import os
import sys
import traceback

from discord import Intents
from discord.ext import commands
from discord import Embed
from dotenv import load_dotenv

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'),
    owner_id=250782339758555136,
    intents=Intents.all(),
    max_messages=3000)

@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

path = os.path.dirname(os.path.realpath(__file__))
if path not in sys.path:
    sys.path.insert(1, path)

if __name__ == "__main__":
    for folder in os.listdir(path):
        if '__' not in folder and '.' not in folder:
            for file in os.listdir(path + f"/{folder}"):
                if file.endswith(".py"):
                    bot.load_extension(f"{folder}.{file[:-3]}")

    load_dotenv("token.env")
    bot.run(os.getenv('DISCORD_TOKEN'))