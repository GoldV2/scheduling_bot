from textwrap import dedent

from discord.channel import DMChannel
from discord.ext import commands

from utils import db_management
from cogs import helpers

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # if message.author == self.bot: == False
        if message.author.name == self.bot.user.name:
            return

        if isinstance(message.channel, DMChannel):
            await message.author.send(dedent("""
                Welcome to the AiGoLearning Evaluation Server!
                Please carefully read
                > https://discord.com/channels/881310619679219743/881310619679219746/900543222714081360
        
                **If you have any questions, contact a Manager**
                *This bot does not respond to DMs*"""))

        elif message.channel.name == 'edit-name' and message.author.id != message.guild.owner:
            await message.author.edit(nick=message.content)

            roles = [role.name for role in message.author.roles]
            # subtracting one from roles because everyone has the @everyone role.
            if not len(roles)-1 and 'New Teacher' not in roles:
                await helpers.Helpers.give_role(message, message.author, 'New Teacher')
                db_management.add_teacher(message.author.id, message.author.nick)

            await message.delete()

        print("Message sent by", message.author.name)
        print("-", message.content)

    @staticmethod
    @commands.Cog.listener()
    async def on_member_remove(member):
        db_management.remove_evaluator(member.id)
        db_management.remove_teacher(member.id)

        for role in member.roles:
            if role.name != "@everyone" and role.name != "Manager":
                await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            is_evaluator = False
            for role in after.roles:
                if role.name == 'Evaluator':
                    is_evaluator = True
                    db_management.update_evaluator_name(after.id, after.nick)
                    break

            if not is_evaluator:
                db_management.update_teacher_name(after.id, after.nick)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot connected successfully!")


def setup(bot):
    bot.add_cog(Events(bot))