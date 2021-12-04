import os
import sys
import traceback

from discord import Intents
from discord.ext import commands
from discord import Embed
from dotenv import load_dotenv

bot = commands.Bot(command_prefix='!', owner_id=250782339758555136,
                   intents=Intents.all())

@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

@bot.event
async def on_error(event, *args, **kwargs):
    for channel in bot.guilds[0].channels:
        if channel.name == 'warnings':
            break

    await channel.send('@Manager error')

    type, value, tb = sys.exc_info()
    tb_string = traceback.format_tb(tb)

    member = args[0]
    author = member.name + "#" + member.discriminator
    embed = Embed(title=value, description=f"Event: {event}\nType: {str(type)}\nBy: {author}")
    for part, line in enumerate(tb_string):
        embed.add_field(name=part, value=line, inline=False)

    await channel.send('@Manager', embed=embed)

path = os.path.dirname(os.path.realpath(__file__))
if path not in sys.path:
    sys.path.insert(1, path)

if __name__ == "__main__":
    for file in os.listdir(path + "/cogs"):
        if file.endswith(".py"):
            bot.load_extension(f"cogs.{file[:-3]}")

    load_dotenv("token.env")
    bot.run(os.getenv('DISCORD_TOKEN'))