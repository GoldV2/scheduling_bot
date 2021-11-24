from textwrap import dedent
from datetime import timedelta

from discord import Embed, Colour
from discord.utils import get
from discord.ext import commands

from utils import db_management
from cogs.constants import Constants


class Helpers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def add_availability_emojis(msg):
        for emoji in Constants.emoji_time_of_day:
            await msg.add_reaction(emoji)

        await msg.add_reaction('👍')

    @staticmethod
    async def add_course_availability_emojis(msg):
        await Helpers.add_course_emojis(msg)
        await msg.add_reaction('👍')

    @staticmethod
    async def add_course_emojis(msg):
        for emoji in Constants.emoji_courses:
            await msg.add_reaction(emoji)

    #####################################################################

    @staticmethod
    async def remove_role(ctx, member, name):
        role = get(ctx.guild.roles, name=name)
        await member.remove_roles(role)

    @staticmethod
    async def give_role(ctx, member, name):
        role = get(ctx.guild.roles, name=name)
        await member.add_roles(role)

    #####################################################################

    @staticmethod
    def get_evaluator_availabilities():
        db_management.c.execute("SELECT * FROM evaluators")
        evaluators = db_management.c.fetchall()

        evaluator_avais = {}

        for evaluator in evaluators:
            for course in evaluator[3].split(','):
                if course not in evaluator_avais:
                    evaluator_avais[course] = {}

                evaluator_avai = evaluator[2].split(',')
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

    @staticmethod
    async def update_evaluator_availability_message(ctx, evaluator_avais):
        for channel in ctx.guild.channels:
            if channel.name == 'evaluator-availability':
                break
        
        # it writes one message, message goes over 2k characters
        # msg = (await channel.history(limit=1).flatten())[0]
        # if not msg:
        #     channel.send('')
        #     msg = (await channel.history(limit=1).flatten())[0]

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

        



        # messages = []
        
        # for course in evaluator_avais:
        #     content = ''
        #     content += f"\n**{course}**\n"
        #     for day in evaluator_avais[course]:
        #         day_content = f"> {day}\n"
        #         for time_of_day in evaluator_avais[course][day]:
        #             day_content += f"\t\t{time_of_day}: {evaluator_avais[course][day][time_of_day]} {'evaluator' if evaluator_avais[course][day][time_of_day] == 1 else 'evaluators'}\n"

        #         content += f"{day_content[:-1]}\n"

        #     messages.append(content)


        # if messages:
        #     for message in messages:
        #         await channel.send(content=message)

    @staticmethod
    # evaluation_time: (evaluation_day_index, evaluation_time_of_day)
    def find_evaluator_availables(evaluation_info, guild):
        COURSE = 0
        DAY = 1
        PERIOD = 2
        AVAILABLE_DAYS = 2
        EVALUATOR_COURSES = 3

        evaluators_available = []
        for member in guild.members:
            if any(role.name == 'Evaluator' for role in member.roles):
                print(member.id, "id")
                print(member.name, member.nick)
                db_management.c.execute("SELECT * FROM evaluators WHERE id=?", (member.id,))
                evaluator = db_management.c.fetchone()
                print(evaluator, 'evaluator')
                evaluator_available_days = evaluator[AVAILABLE_DAYS].split(',')
                evaluator_available_periods = evaluator_available_days[Constants.week_days.index(evaluation_info[DAY])]
                evaluator_courses = evaluator[EVALUATOR_COURSES]

                if (evaluation_info[COURSE] in evaluator_courses
                    and evaluation_info[PERIOD] in evaluator_available_periods):

                    evaluators_available.append(member)
        
        return evaluators_available

    #####################################################################

    @staticmethod
    async def ask_availability(evaluator, bot):
        def availabiity_confimation_check(reaction, user):
            return user == evaluator and str(reaction.emoji) and reaction.emoji == '👍'

        await evaluator.send(dedent("""
            You will be sent 7 messages, one for each day of the week.
            React with the times of the day you are available, then press the 👍 to confirm.
            > 🌇: Morning
            > 🏙️: Afternoon
            > 🌃: Evening
            > React only with the 👍 if you are not available that day"""))

        availability = ''
        for day in Constants.week_days:
            m = await evaluator.send(f"When are you available on {day}?")
            await Helpers.add_availability_emojis(m)
            
            reaction, user = await bot.wait_for('reaction_add', check=availabiity_confimation_check)

            msg = get(bot.cached_messages, id=m.id)
            reactions = msg.reactions
            reactions.remove(reaction)

            day_avai = ''
            for reac in msg.reactions:
                if reac.count > 1:
                    day_avai += Constants.emoji_time_of_day[reac.emoji] + ' and '
            
            day_avai = day_avai[:-5]
            availability += day_avai + ',' if day != 'Sunday' else day_avai

        await evaluator.send("Availability set succesfully!")

        return availability

    @staticmethod
    async def ask_courses(evaluator, bot):
        def course_emojis_check(reaction, user):
            return user == evaluator and reaction.emoji == '👍' and reaction.message == m

        msg_content = "React with the courses you can evaluate for then press the 👍 to confirm.\n"
        for key, value in Constants.emoji_courses.items():
            msg_content += f'> {key}: {value}\n'
        
        m = await evaluator.send(msg_content)
        await Helpers.add_course_availability_emojis(m)

        reaction, user = await bot.wait_for('reaction_add', check=course_emojis_check)

        msg = get(bot.cached_messages, id=m.id)
        reactions = msg.reactions
        reactions.remove(reaction)

        courses = ''
        for reac in msg.reactions:
            if reac.count > 1:
                courses += Constants.emoji_courses[reac.emoji] + ','
        
        courses = courses[:-1]

        await evaluator.send("Courses set succesfully!")

        return courses

    #####################################################################

    # every time an evaluation is cancelled, send a message to the "warnings" channel in Discord
    async def evaluation_canceled_warning(bot, evaluation):
        for channel in bot.guilds[0].channels:
            if channel.name == 'warnings':
                break
        await channel.send(dedent(f"""
                            Evaluation Canceled
                            Reason: {evaluation[7]}
                            Evaluator: {evaluation[0]}
                            Teacher: {evaluation[1]}
                            Evaluation Time: {evaluation[2]}
                            Course: {evaluation[3]}
                            Evaluation Confirmation Time: {evaluation[4]}"""))

    # find_next_weekday
    def next_weekday(d, weekday):
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0: # Target day already happened this week
            days_ahead += 7

        return d + timedelta(days_ahead)

def setup(bot):
    bot.add_cog(Helpers(bot))