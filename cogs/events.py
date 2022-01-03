from textwrap import dedent

import discord
from discord.channel import DMChannel
from discord.ext import commands

from db.db_management import DB
from cogs.helpers import Helpers
from cogs.evaluator_commands import ProfileView
from cogs.schedule import ScheduleView

class Member:
    def __init__(self, bot, member):
        self.bot = bot
        self.member = member
        self.nick = self.member.nick
        self.roles = [role.name for role in self.member.roles]

    def is_in_db(self):
        return True if DB.fetch_one(self.member.id) and 'New Teacher' in self.roles else False

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

        elif message.channel.name == 'edit-name':
            await message.author.edit(nick=message.content)
            await message.delete()

        print("Message sent by", message.author.name)
        print("-", message.content)

    @staticmethod
    @commands.Cog.listener()
    async def on_member_remove(member):
        DB.remove_member(member.id)

        try:
            for role in member.roles:
                if role.name != "@everyone" and role.name != "Manager":
                    await member.remove_roles(role)

        except:
            print(member.nick, member.name, "left the server.")

    @commands.Cog.listener('on_member_update')
    async def update_member_nick(self, before, after):
        member = Member(self.bot, after)

        if before.nick != after.nick:
            if member.is_in_db():
                DB.update_member_name(after.id, after.nick)

            else:
                DB.add_member(after.id, after.nick)
                await Helpers.give_role(self.bot, after, 'New Teacher')

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ProfileView(self.bot))
        self.bot.add_view(ScheduleView(self.bot))

        for channel in self.bot.guilds[0].channels:
            if 'Bot Status:' in channel.name:
                break
        
        await channel.edit(name='Bot Status: Online')

def setup(bot):
    bot.add_cog(Events(bot))