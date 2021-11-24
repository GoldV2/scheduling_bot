
from discord.ext import commands
from datetime import datetime

from utils import evaluation_sheet_management
from utils import db_management
from cogs import helpers
from cogs import constants

class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduling_now = []

    def schedule_check(ctx):
        return ctx.channel.name == '📅schedule-evaluation📅'

    @commands.command()
    @commands.check(schedule_check)
    async def schedule(self, ctx):
        
        #############################################################

        # creating variables to make the code easier to read
        teacher = ctx.author
        if teacher in self.scheduling_now:
            await teacher.send("Please finish scheduling or wait for an evaluator's response before scheduling another.")
            return

        self.scheduling_now.append(teacher)

        #############################################################

        def day_emojis_check(reaction, user):
            return user == teacher and reaction.emoji in constants.Constants.emoji_days and reaction.message == m

        def course_emojis_check(reaction, user):
            return user == teacher and reaction.emoji in constants.Constants.emoji_courses and reaction.message == m3

        def time_emojis_check(reaction, user):
            return user == teacher and reaction.emoji in constants.Constants.emoji_time_of_day and reaction.message == m2
        
        def tea_available_check(reaction, user):
            return user == teacher and reaction.emoji in constants.Constants.check_emojis and reaction.message == tea_msg

        def eval_available_check(reaction, user):
            return user in evals_received_msg and reaction.emoji in constants.Constants.check_emojis and reaction.message in eval_msgs

        def confirmation_check(reaction, user):
            if reaction.message == confirmation_msg:
                return user == teacher and reaction.emoji == '🛑'

            elif reaction.message in eval_msgs:
                return user in evals_received_msg and reaction.emoji in constants.Constants.check_emojis

        #############################################################

        # teacher can only see courses they have the role for
        teacher_courses = [role.name for role in teacher.roles]
        evaluator_avais = helpers.Helpers.get_evaluator_availabilities()

        courses_avais = {}
        for course in evaluator_avais:
            if course in teacher_courses:
                courses_avais[course] = evaluator_avais[course]

        if not courses_avais:
            await teacher.send("Sorry, there are no evaluators available.")
            return

        m3_content = 'Which course would you like to be evaluated on?'

        for course in courses_avais:
            m3_content += f'\n> {constants.Constants.course_emojis[course]}: {course}'

        # asking for which course to be tested on
        m3 = await teacher.send(m3_content)
        # probably shouldn't be passing in courses_avais as courses, but should work
        await helpers.Helpers.add_available_course_emojis(m3, courses_avais)
        # using the same check as when asking for the day of the week to meet, probably not good idea
        reaction3, user = await self.bot.wait_for('reaction_add', check=course_emojis_check)

        evaluation_course = constants.Constants.emoji_courses[reaction3.emoji]
        await teacher.send(f"Your evaluation will be on {evaluation_course}.")


        #############################################################

        m_content = 'What day of the week would you like to be evaluated?'
        days = list(courses_avais[evaluation_course].keys())
        for day in days:
            m_content += f'\n> {constants.Constants.day_emojis[day]}: {day}'

        # asking for what day the teacher wants to be evaluated
        m = await teacher.send(m_content)    

        await helpers.Helpers.add_day_emojis(m, days)
        reaction, user = await self.bot.wait_for('reaction_add', check=day_emojis_check)

        evaluation_day_index = int(reaction.emoji[0])-1
        await teacher.send(f"Your evaluation will be on a {constants.Constants.week_days[evaluation_day_index]}.")


        #############################################################

        m2_content = 'At what time of the day would you like to meet?'
        times_on_day = list(courses_avais[evaluation_course][constants.Constants.emoji_days[reaction.emoji]].keys())

        for time in times_on_day:
            m2_content += f'\n> {constants.Constants.time_of_day_emojis[time]}: {time}'

        # asking for what time of the day the teacher wants to be evaluated
        m2 = await teacher.send(m2_content)

        await helpers.Helpers.add_time_emojis(m2, times_on_day)
        # using the same check as when asking for the day of the week to meet, probably not good idea
        reaction2, user = await self.bot.wait_for('reaction_add', check=time_emojis_check)
        evaluation_time_of_day = constants.Constants.emoji_time_of_day[reaction2.emoji]

        await teacher.send(f"Your evaluation will be during the {evaluation_time_of_day}")

        #############################################################

        # arguments: (week_day of evolution, time_of_day of evaluation, course)
        # example: (0, 'm', 's')
        # example explained: (Monday, Morning 8:00am to 11:00am, Scratch - AI000, AI001, AI002)
        evaluation_time = (evaluation_day_index, evaluation_time_of_day,  evaluation_course)

        # not sure if the best thing to find guild is teacher.guild
        available_evaluators = helpers.Helpers.find_available_evaluators(evaluation_time, evaluation_course, ctx.guild)

        #############################################################

        # creating variables to make the code easier to understand
        # meeting week day
        evaluation_week_day = constants.Constants.week_days[evaluation_day_index]
        # similar to evaluation_course
        # evaluation course full name, instead of "s" it is "Scratch"

        while True:
            for time in constants.Constants.times_of_day[evaluation_time_of_day]:
                matched = False

                print(f"-----\n{teacher.nick} scheduled an evaluation.\nEvaluators: {[ev.name for ev in available_evaluators]}")
                tea_msg = await teacher.send(f"Is {evaluation_week_day} at {time} a good time for you to be evaluated? React with the appropriate emoji to agree.")
                await helpers.Helpers.add_checks(tea_msg)
                
                tea_reaction, user = await self.bot.wait_for('reaction_add', check=tea_available_check)
                if tea_reaction.emoji == '✅':
                    # send_evaluator_requests
                    # evaluators who received
                    evals_received_msg = []
                    # messages sent
                    eval_msgs = []
                    for evaluator in available_evaluators:
                        eval_msg = await evaluator.send(f"Can you evaluate {teacher.nick} on {evaluation_course} coming {evaluation_week_day} at {time}?")
                        await helpers.Helpers.add_checks(eval_msg)
                        evals_received_msg.append(evaluator)
                        eval_msgs.append(eval_msg)

                    confirmation_msg = await teacher.send(f'Your request was sent to all evaluators available. Please be patient, you will receive a confirmation message if an evaluator is available. React with the 🛑 to cancel.')
                    await confirmation_msg.add_reaction('🛑')

                    while True:
                        confirmation_reaction, evaluator_available = await self.bot.wait_for('reaction_add', check=confirmation_check)

                        if confirmation_reaction.emoji == '✅':
                            evals_received_msg.remove(evaluator_available)
                            for eval_received in evals_received_msg:
                                await eval_received.send(f"The evaluation for {teacher.nick} on {evaluation_course} coming {evaluation_week_day} at {time} has been accepeted by another evaluator.")

                            matched = True

                            await helpers.Helpers.give_role(ctx, teacher, "Pending Evaluation")

                            # finding which day of he month is the next evaluation_week_day
                            evaluation_date = helpers.Helpers.next_weekday(datetime.now(), constants.Constants.week_days.index(evaluation_week_day))
                            # finding evaluation hour and converting to military time
                            evaluation_hour = int(time.split(':')[0]) if time[-2:] == 'am' else int(time.split(':')[0])  + 12
                            evaluation_date = evaluation_date.replace(hour=evaluation_hour, minute=0, second=0)

                            await teacher.send(f"Evaluation confirmed! Take note of day and time, {evaluation_date.month}/{evaluation_date.day} at {time}. Say hi to your evaluator on Discord by adding them, {evaluator_available.name}#{evaluator_available.discriminator}")
                            await evaluator_available.send(f"Evaluation confirmed! Take note of day and time, {evaluation_date.month}/{evaluation_date.day} at {time}. Say hi to the teacher you will evaluate on Discord by adding them, {teacher.name}#{teacher.discriminator}")

                            break

                        elif confirmation_reaction.emoji == '🛑':
                            for eval_received_msg in evals_received_msg:
                                await eval_received_msg.send(f"{teacher.nick} canceled their {evaluation_course} evaluation that was coming {evaluation_week_day} at {time}")

                            await teacher.send('Your evaluation request was canceled. Use the "!schedule" command again in the server to reschedule.')
                            # should probably put this at the end so I do not have to repeat it when if matched:
                            self.scheduling_now.remove(teacher)

                            print(f"{teacher.name} aka {teacher.nick} canceled an unconfirmed evaluation")

                            return

                        else:
                            evals_received_msg.remove(evaluator_available)

                        if not evals_received_msg:
                            await teacher.send(f"Sorry, there are no {evaluation_course} evaluators available on {evaluation_week_day} at {time}.")
                            
                            break


        
                if matched:
                    # converting user object, evaluator available, to member object to access their .nick
                    for member in ctx.guild.members:
                        if member.id == evaluator_available.id:
                            evaluator_available = member
                            break

                    evaluation = [f"{evaluator_available.name}#{evaluator_available.discriminator} AKA {evaluator_available.nick}",
                                    f"{teacher.name}#{teacher.discriminator} AKA {teacher.nick}",
                                    f"{evaluation_date.strftime('%m/%d/%Y %H:%M:%S')}",
                                    evaluation_course,
                                    datetime.now().strftime('%m/%d/%Y %H:%M:%S')]

                    print('-----')
                    print(f"Evaluation confirmed: {evaluation}")

                    evaluation_sheet_management.append_confirmed_evaluation(evaluation)

                    # adding this evaluation to the database of evaluator and teacher
                    db_management.add_evaluator_evaluation(evaluator_available.id, '$'.join(evaluation))
                    db_management.add_teacher_evaluation(teacher.id, '$'.join(evaluation))

                    self.scheduling_now.remove(teacher)

                    return
            
            await teacher.send(f"Try evaluating for another time of the day.")

            # make it so that the code funels down to this somehow so I don't have to repeat it
            self.scheduling_now.remove(teacher)

            return

def setup(bot):
    bot.add_cog(Schedule(bot))