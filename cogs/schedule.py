
from discord.ext import commands
from discord import Member
from datetime import datetime


from utils import evaluation_sheet_management
from utils import db_management
from cogs.helpers import Helpers
from cogs.constants import Constants

class Teacher:
    def __init__(self, user):
        self.user = user

    def is_currently_scheduling(self):
        if self.user in ScheduleCommand.scheduling_now:
            return True
        
        else:
            return False

    def get_courses_available(self):
        teacher_courses = [role.name for role in self.user.roles]
        evaluators_courses = Helpers.get_evaluator_availabilities()

        courses_available = {}
        for course in evaluators_courses:
            if course in teacher_courses:
                courses_available[course] = evaluators_courses[course]

        return courses_available

    async def ask_course(self, courses_available):
        def course_emojis_check(reaction, user):
            return (user == self.user
                    and reaction.emoji in Constants.emoji_courses
                    and reaction.message == msg)

        async def add_available_course_emojis(msg, courses):
            for course in courses:
                await msg.add_reaction(Constants.course_emojis[course])

        # creating and sending message
        msg_content = 'Which course would you like to be evaluated on?'
        for course in courses_available:
            msg_content += f'\n> {Constants.course_emojis[course]}: {course}'
        msg = await self.user.send(msg_content)

        # waiting for reaction
        await add_available_course_emojis(msg, courses_available)
        reaction, user = await instance.bot.wait_for('reaction_add', check=course_emojis_check)

        # getting course and sending confirmation
        evaluation_course = Constants.emoji_courses[reaction.emoji]
        await self.user.send(f"Your evaluation will be on {evaluation_course}.")

        return evaluation_course

    async def ask_week_day(self, available_days):
        def day_emojis_check(reaction, user):
            return (user == self.user
                    and reaction.emoji in Constants.emoji_days
                    and reaction.message == msg)

        async def add_week_day_emojis(msg, days):
            for day in days:
                await msg.add_reaction(Constants.day_emojis[day])
        
        # creating and sending message
        msg_content = 'What day of the week would you like to be evaluated?'
        for day in available_days:
            msg_content += f'\n> {Constants.day_emojis[day]}: {day}'
        msg = await self.user.send(msg_content)    

        # waiting for reaction
        await add_week_day_emojis(msg, available_days)
        reaction, user = await instance.bot.wait_for('reaction_add', check=day_emojis_check)

        # getting week_day and sending confirmation
        evaluation_week_day_index = int(reaction.emoji[0])-1
        evaluation_week_day = Constants.week_days[evaluation_week_day_index]
        await self.user.send(f"Your evaluation will be on a {evaluation_week_day}.")

        return evaluation_week_day

    async def ask_period_of_day(self, available_periods_of_day):
        def period_of_day_reaction_check(reaction, user):
            return (user == self.user
                    and reaction.emoji in Constants.emoji_time_of_day
                    and reaction.message == msg)
        
        async def add_periods_of_day_reactions(msg, times):
            for time in times:
                await msg.add_reaction(Constants.time_of_day_emojis[time])

        # creating and sending message
        msg_content = 'At what time of the day would you like to meet?'
        for period in available_periods_of_day:
            msg_content += f'\n> {Constants.time_of_day_emojis[period]}: {period}'
        msg = await self.user.send(msg_content)

        # waiting for reaction
        await add_periods_of_day_reactions(msg, available_periods_of_day)
        reaction, user = await instance.bot.wait_for('reaction_add', check=period_of_day_reaction_check)
        
        # getting evaluation_period_of and sending confirmation
        evaluation_period_of_day = Constants.emoji_time_of_day[reaction.emoji]
        await self.user.send(f"Your evaluation will be during the {evaluation_period_of_day}")

        return evaluation_period_of_day

    async def ask_evaluation_info(self):
        courses_available = self.get_courses_available()
        evaluation_course = await self.ask_course(courses_available)
        
        available_days = courses_available[evaluation_course]
        evaluation_week_day = await self.ask_week_day(available_days)

        available_periods_of_day = courses_available[evaluation_course][evaluation_week_day]
        evaluation_period_of_day = await self.ask_period_of_day(available_periods_of_day)

        evaluation_hour = None
        evaluation_info = [evaluation_course,
                           evaluation_week_day,
                           evaluation_period_of_day,
                           evaluation_hour]

        return evaluation_info

    async def is_available(self, evaluation_week_day, time):
        async def add_checks(msg):
            for emoji in Constants.check_emojis:
                await msg.add_reaction(emoji)
        
        def available_check(reaction, user):
            return (user == self.user
                    and reaction.emoji in Constants.check_emojis
                    and reaction.message == msg)

        msg = await self.user.send(f"Is {evaluation_week_day} at {time} a good time for you to be evaluated? React with the appropriate emoji to agree.")
        
        await add_checks(msg)
        reaction, user = await instance.bot.wait_for('reaction_add', check=available_check)

        return reaction.emoji == '✅'

class ScheduleCommand(commands.Cog):
    scheduling_now = []
    
    def __init__(self, bot):
        self.bot = bot

    def sent_in_schedule_evaluation(ctx):
        return ctx.channel.name == '📅schedule-evaluation📅'

    @commands.command()
    @commands.check(sent_in_schedule_evaluation)
    async def schedule(self, ctx):
        teacher = Teacher(ctx.author)
        if teacher.is_currently_scheduling():
            await teacher.user.send("Please finish scheduling or wait for an evaluator's response before scheduling another.")
            return

        ScheduleCommand.scheduling_now.append(teacher)

        # indexes of each piece of information in evaluation_info
        COURSE = 0
        DAY = 1
        PERIOD = 2
        HOUR = 3
        evaluation_info = await teacher.ask_evaluation_info()

        evaluators_available = Helpers.find_evaluator_availables(evaluation_info,
                                                                         ctx.guild)

        #############################################################

        async def send_request_to_evaluators(evaluators_available, teacher, evaluation_info):
            async def add_checks(msg):
                for emoji in Constants.check_emojis:
                    await msg.add_reaction(emoji)
            
            evaluators_requested = []
            evaluator_request_msgs = []
            for evaluator in evaluators_available:
                msg = await evaluator.send(f"Can you evaluate {teacher.user.nick} on {evaluation_info[COURSE]} coming {evaluation_info[DAY]} at {evaluation_info[HOUR]}?")
                await add_checks(msg)
                
                evaluators_requested.append(evaluator)
                evaluator_request_msgs.append(msg)

            return evaluators_requested, evaluator_request_msgs

        async def wait_for_confirmation(evaluators_requested, evaluator_request_msgs, evaluation_info):
            def confirmation_check(reaction, user):
                if reaction.message == confirmation_msg:
                    return user == teacher.user and reaction.emoji == '🛑'

                elif reaction.message in evaluator_request_msgs:
                    return user in evaluators_available and reaction.emoji in Constants.check_emojis

            async def send_msg_to_evaluators_requested(evaluators_requested, msg_content):
                for evaluator_requested in evaluators_requested:
                    await evaluator_requested.send(msg_content)

            # continously waits for a reaction from the teacher or any evaluator
            while evaluators_requested:
                confirmation_reaction, evaluator_available = await self.bot.wait_for('reaction_add', check=confirmation_check)

                if confirmation_reaction.emoji == '✅':
                    evaluators_requested.remove(evaluator_available)
                    
                    accepted_by_another_evaluator_msg_content = f"The evaluation for {teacher.user.nick} on {evaluation_info[COURSE]} coming {evaluation_info[DAY]} at {evaluation_info[HOUR]} has been accepeted by another evaluator."
                    await send_msg_to_evaluators_requested(evaluators_requested, accepted_by_another_evaluator_msg_content)
                    
                    return "confirmed", evaluator_available

                elif confirmation_reaction.emoji == '🛑':
                    print(f"{teacher.user.name} aka {teacher.user.nick} canceled an unconfirmed evaluation")

                    canceled_by_teacher_msg_content = f"{teacher.user.nick} canceled their {evaluation_info[COURSE]} evaluation that was coming {evaluation_info[DAY]} at {evaluation_info[HOUR]}"
                    await send_msg_to_evaluators_requested(evaluators_requested, canceled_by_teacher_msg_content)

                    await teacher.user.send('Your evaluation request was canceled. Use the "!schedule" command again in the server to reschedule.')

                    return "cancelled by teacher", None

                else:
                    evaluators_requested.remove(evaluator_available)

            await teacher.user.send(f"Sorry, there are no {evaluation_info[COURSE]} evaluators available on {evaluation_info[DAY]} at {evaluation_info[HOUR]}.")
            return "evaluators unavailable", None

        def find_evaluation_date(evaluation_info):
            hour = evaluation_info[HOUR]

            # finding next calendar day for the given week day
            evaluation_date = Helpers.next_weekday(datetime.now(), Constants.week_days.index(evaluation_info[DAY]))
            # finding evaluation hour and converting to military time
            evaluation_hour = int(hour.split(':')[0]) if hour[-2:] == 'am' else int(hour.split(':')[0])  + 12
            
            evaluation_date = evaluation_date.replace(hour=evaluation_hour, minute=0, second=0)

            return evaluation_date

        print(f"-----\n{teacher.user.nick} scheduled an evaluation.\nEvaluators: {[ev.name for ev in evaluators_available]}")
        for hour in Constants.times_of_day[evaluation_info[PERIOD]]:
            matched = False

            evaluation_info[HOUR] = hour

            teacher_available = False
            if await teacher.is_available(evaluation_info[DAY], evaluation_info[HOUR]):
                teacher_available = True

                evaluators_requested, evaluator_request_msgs = await send_request_to_evaluators(evaluators_available,
                                                                                            teacher,
                                                                                            evaluation_info)
                
                confirmation_msg = await teacher.user.send(f'Your request was sent to all evaluators available. Please be patient, you will receive a confirmation message if an evaluator is available. React with the 🛑 to cancel.')
                await confirmation_msg.add_reaction('🛑')

                matched, evaluator_available = await wait_for_confirmation(evaluators_requested, evaluator_request_msgs, evaluation_info)

            if matched == "confirmed":
                # converting user object, evaluator_available, to member object to access their .nick
                for member in ctx.guild.members:
                    if member.id == evaluator_available.id:
                        evaluator_available = member
                        break
    
                evaluation_date = find_evaluation_date(evaluation_info)

                evaluation = [f"{evaluator_available.name}#{evaluator_available.discriminator} AKA {evaluator_available.nick}",
                                f"{teacher.user.name}#{teacher.user.discriminator} AKA {teacher.user.nick}",
                                f"{evaluation_date.strftime('%m/%d/%Y %H:%M:%S')}",
                                evaluation_info[COURSE],
                                datetime.now().strftime('%m/%d/%Y %H:%M:%S')]

                evaluation_sheet_management.append_confirmed_evaluation(evaluation)

                # adding this evaluation to the database of evaluator and teacher
                db_management.add_evaluator_evaluation(evaluator_available.id, '$'.join(evaluation))
                db_management.add_teacher_evaluation(teacher.user.id, '$'.join(evaluation))

                await Helpers.give_role(ctx, teacher.user, "Pending Evaluation")

                await teacher.user.send(f"Evaluation confirmed! Take note of day and time, {evaluation_date.month}/{evaluation_date.day} at {evaluation_info[HOUR]}. Say hi to your evaluator on Discord by adding them, {evaluator_available.name}#{evaluator_available.discriminator}")
                await evaluator_available.send(f"Evaluation confirmed! Take note of day and time, {evaluation_date.month}/{evaluation_date.day} at {evaluation_info[HOUR]}. Say hi to the teacher you will evaluate on Discord by adding them, {teacher.user.name}#{teacher.user.discriminator}")

                print(f"Evaluation confirmed: {evaluation}")
                break

            elif matched == "cancelled by teacher":
                break

        if not teacher_available:
            await teacher.user.send(f"These are the only hours available during the {evaluation_info[PERIOD]}. If none are good for you, try evaluation for another day or another period of the day.")
    
        if matched == "evaluators unavailable":
            await teacher.user.send(f"Try evaluating for another time of the day.")

        ScheduleCommand.scheduling_now.remove(teacher)

        return

def setup(bot):
    global instance 
    instance = ScheduleCommand(bot)
    bot.add_cog(instance)