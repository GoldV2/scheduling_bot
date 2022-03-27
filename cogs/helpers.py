from textwrap import dedent
from datetime import timedelta

from discord import Embed, Colour
from discord.utils import get
from discord.ext import commands, tasks
from cogs.email import Email

from db.db_management import DB
from cogs.constants import Constants


class Helpers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_evaluator_availability_message.start()
    
    @staticmethod    
    async def remove_role(member, name):
        role = get(member.guild.roles, name=name)
        await member.remove_roles(role)

    @staticmethod
    async def give_role(bot, member, name):
        role = get(bot.guilds[0].roles, name=name)
        await member.add_roles(role)

    #####################################################################

    @staticmethod
    def get_evaluator_availabilities():
        DB.c.execute("SELECT * FROM evaluators")
        evaluators = DB.c.fetchall()

        evaluator_avais = {}

        for evaluator in evaluators:
            for course in evaluator[2].split(','):
                if course not in evaluator_avais:
                    evaluator_avais[course] = {}

                evaluator_avai = evaluator[1].split(',')
                for week_day_index, times_of_day in enumerate(evaluator_avai):
                    week_day_name = Constants.week_days[week_day_index]
                    if week_day_name not in evaluator_avais[course] and times_of_day:
                        evaluator_avais[course][week_day_name] = {}

                    available_times_of_day = times_of_day.split(' and ')
                    if available_times_of_day != ['']:
                        for time_of_day in available_times_of_day:
                            if time_of_day not in evaluator_avais[course][week_day_name]:
                                evaluator_avais[course][week_day_name][time_of_day] = 0

                            evaluator_avais[course][week_day_name][time_of_day] += 1

        # sorting evaluator avais
        sorted_evaluator_avais = {}
        for course in evaluator_avais:
            sorted_evaluator_avais[course] = None
            week_days_avai = {}
            for week_day in evaluator_avais[course]:
                week_days_avai[week_day] = None
                times_of_day = {}
                for time_of_day in evaluator_avais[course][week_day]:
                    times_of_day[time_of_day] = evaluator_avais[course][week_day][time_of_day]
                
                times_of_day = {k: times_of_day[k] for k in sorted(times_of_day.keys(), key=list(Constants.times_of_day.keys()).index)}
                week_days_avai[week_day] = times_of_day
            
            week_days_avai = {k: week_days_avai[k] for k in sorted(week_days_avai.keys(), key=Constants.week_days.index)}
            sorted_evaluator_avais[course] = week_days_avai

        sorted_evaluator_avais = {k: sorted_evaluator_avais[k] for k in sorted(sorted_evaluator_avais.keys(), key=list(Constants.course_emojis.keys()).index)}

        return sorted_evaluator_avais

    @tasks.loop(minutes=60)
    async def update_evaluator_availability_message(self, bot):
        evaluator_avais = Helpers.get_evaluator_availabilities()
        for channel in bot.guilds[0].channels:
            if channel.name == 'evaluator-availability':
                break

        # limit should only be about 11, because there are onle 11 courses I believe, or 10...
        embeds = []
        for course in evaluator_avais:
            embed = Embed(title=course,
                                  colour=Colour.blue())

            if 'Python' in course:
                embed.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png') 

            if 'Java' in course:
                embed.set_thumbnail(url='https://www.puzzle.ch/wp-content/uploads/2020/11/java.jpg')
            
            if 'Scratch' in course:
                embed.set_thumbnail(url='https://yt3.ggpht.com/ytc/AKedOLRTem1QY-28jHnVUuBzDkxJJqnPwrli_b3skJhj=s900-c-k-c0x00ffffff-no-rj')

            for day in evaluator_avais[course]:
                day_field_value = ""
                for time_of_day in evaluator_avais[course][day]:
                    day_field_value += f"{time_of_day}: {evaluator_avais[course][day][time_of_day]} {'evaluator' if evaluator_avais[course][day][time_of_day] == 1 else 'evaluators'}\n"

                embed.add_field(name=day, value=day_field_value, inline=False)

            embeds.append(embed)

        msgs = await channel.history(limit=15).flatten()
        for i, msg in enumerate(msgs[::-1]):
            await msg.edit(embed=embeds[i])

    @staticmethod
    def find_evaluator_availables(bot, evaluation_info):
        COURSE = 0
        DAY = 1
        PERIOD = 2
        AVAILABLE_DAYS = 1
        EVALUATOR_COURSES = 2

        evaluators_available = []
        for member in bot.guilds[0].members:
            if any(role.name == 'Evaluator' for role in member.roles):
                DB.c.execute("SELECT * FROM evaluators WHERE id=?", (member.id,))
                evaluator = DB.c.fetchone()
                evaluator_available_days = evaluator[AVAILABLE_DAYS].split(',')
                evaluator_available_periods = evaluator_available_days[Constants.week_days.index(evaluation_info[DAY])]
                evaluator_courses = evaluator[EVALUATOR_COURSES]

                if (evaluation_info[COURSE] in evaluator_courses
                    and evaluation_info[PERIOD] in evaluator_available_periods):

                    evaluators_available.append(member)
        
        return evaluators_available

    #####################################################################

    def get_member(guild, info: str):
        discord_info, nickname = info.split(' AKA ')
        discord_name, discriminator = discord_info.split('#')
        for member in guild.members:
            if (member.nick == nickname 
                and member.discriminator == discriminator):

                return member

    # find_next_weekday
    def next_weekday(d, weekday):
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0: # Target day already happened this week
            days_ahead += 7

        return d + timedelta(days_ahead)

    @update_evaluator_availability_message.before_loop
    async def update_evaluator_availability_message_before(self):
        await self.client.wait_until_ready()

def setup(bot):
    bot.add_cog(Helpers(bot))