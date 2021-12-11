
from time import sleep
from discord.ext import commands
from datetime import datetime

import discord
from sheets.evaluation_sheet_management import EvaluationSheet
from db.db_management import DB
from cogs.helpers import Helpers
from cogs.constants import Constants

# TODO refactor this so these classes aren't so repetitive
class CourseDropDown(discord.ui.Select):
    def __init__(self, courses):
    
        self.my_options = []

        for course in courses:
            self.my_options.append(discord.SelectOption(label=course,
                emoji=Constants.course_emojis[course]))

        super().__init__(placeholder='Select a course', min_values=1, max_values=1, options=self.my_options)

    async def callback(self, interaction):
        self.disabled = True
        self.view.course = self.values[0]

        for option in self.my_options:
            if option.label == self.values[0]:
                option.default = True
                break

        await interaction.response.edit_message(view=self.view)

        self.view.stop()

class CourseView(discord.ui.View):
    def __init__(self, courses):
        super().__init__(timeout=None)

        self.add_item(CourseDropDown(courses))

class DayDropdown(discord.ui.Select):
    def __init__(self, days):
    
        self.my_options = []

        for day in days:
            self.my_options.append(discord.SelectOption(label=day,
                emoji=Constants.day_emojis[day]))

        super().__init__(placeholder='Select a day', min_values=1, max_values=1, options=self.my_options)

    async def callback(self, interaction):
        self.disabled = True
        self.view.day = self.values[0]

        for option in self.my_options:
            if option.label == self.values[0]:
                option.default = True
                break
        
        await interaction.response.edit_message(view=self.view)

        self.view.stop()

class DayView(discord.ui.View):
    def __init__(self, days):
        super().__init__(timeout=None)

        self.add_item(DayDropdown(days))

class PeriodDropDown(discord.ui.Select):
    def __init__(self, periods):
    
        self.my_options = []

        for period in periods:
            self.my_options.append(discord.SelectOption(label=period,
                emoji=Constants.time_of_day_emojis[period]))

        super().__init__(placeholder='Select a time of the day', min_values=1, max_values=1, options=self.my_options)

    async def callback(self, interaction):
        self.disabled = True
        self.view.period = self.values[0]
        
        for option in self.my_options:
            if option.label == self.values[0]:
                option.default = True
                break
        
        await interaction.response.edit_message(view=self.view)

        self.view.stop()

class PeriodView(discord.ui.View):
    def __init__(self, periods):
        super().__init__(timeout=None)

        self.add_item(PeriodDropDown(periods))

class Teacher:
    def __init__(self, user):
        self.user = user
        self.roles = [role.name for role in user.roles]

    def get_courses_available(self):
        teacher_courses = [role.name for role in self.user.roles]
        evaluators_courses = Helpers.get_evaluator_availabilities()

        courses_available = {}
        for course in evaluators_courses:
            if course in teacher_courses:
                courses_available[course] = evaluators_courses[course]

        return courses_available

    async def ask_course(self, courses_available):
        view = CourseView(courses_available)
        await self.user.send(content='Select a course to be evaluated on.', view=view)

        await view.wait()
        return view.course

    async def ask_week_day(self, available_days):
        view = DayView(available_days)
        await self.user.send(content='Select a day to be evaluated on.', view=view)

        await view.wait()
        return view.day  

    async def ask_period_of_day(self, available_periods_of_day):
        view = PeriodView(available_periods_of_day)
        await self.user.send(content='Select a period of the day to be evaluated on.', view=view)

        await view.wait()
        return view.period

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

class HourDropDown(discord.ui.Select):
    def __init__(self, hours):
    
        self.my_options = []

        for hour in hours:
            self.my_options.append(discord.SelectOption(label=hour))

        super().__init__(placeholder='Select an hour', min_values=1, max_values=1, options=self.my_options)

    async def callback(self, interaction):
        for item in self.view.children:
            item.disabled = True

        self.view.hour = self.values[0]

        for option in self.my_options:
            if option.label == self.values[0]:
                option.default = True
                break
        
        await interaction.response.edit_message(view=self.view)

        self.view.stop()

class HourView(discord.ui.View):
    def __init__(self, period):
        super().__init__(timeout=None)

        self.add_item(HourDropDown(period))

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.hour = None

        self.stop()

class EvaluatorConfirmationView(discord.ui.View):
    def __init__(self, evaluators_requested):
        super().__init__(timeout=None)

        self.evaluators_requested = evaluators_requested
        self.evaluator_available = None
    
    # TODO checking for IDs, I'd rather check for the user instance itself
    async def interaction_check(self, interaction):
        return interaction.user.id in [user.id for user in self.evaluators_requested]

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no(self, button, interaction):
        await interaction.response.defer()
        await interaction.message.edit(content=interaction.message.content + '\n*You refused this evaluation request*')
        for evaluator in self.evaluators_requested:
            if evaluator.id == interaction.user.id:
                self.evaluators_requested.remove(evaluator)
                break

        for item in self.children:
            item.disabled = True
        
        await interaction.message.edit(view=self)

        if not self.evaluators_requested:
            self.stop()

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes(self, button, interaction):
        for item in self.children:
            item.disabled = True

        for evaluator in self.evaluators_requested:
            if evaluator.id == interaction.user.id:
                self.evaluators_requested.remove(evaluator)
                break

        await interaction.response.edit_message(view=self)

        self.evaluator_available = interaction.user

        self.stop()

class TeacherCancelView(discord.ui.Select):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        for item in self.view.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.canceled = True
        self.stop()

class ScheduleView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)

        self.bot = bot
        self.scheduling_now = []

    async def interaction_check(self, interaction):
        member = Teacher(interaction.user)
        if 'Evaluation Ready' not in member.roles:
            await interaction.response.send_message('Only evaluation ready teachers can do this.', ephemeral=True)
            return False

        elif interaction.user in self.scheduling_now:
            await interaction.response.send_message('Finish scheduling a previous evaluation before trying again.', ephemeral=True)
            return False

        return True

    @discord.ui.button(label='Schedule Evaluation', style=discord.ButtonStyle.blurple, custom_id='schedule_evaluation_button')
    async def schedule(self, button, interaction):
        await interaction.response.defer()
        teacher = Teacher(interaction.guild.get_member(interaction.user.id))
        self.scheduling_now.append(interaction.user)

        # indexes of each piece of information in evaluation_info
        COURSE = 0
        DAY = 1
        PERIOD = 2
        HOUR = 3
        evaluation_info = await teacher.ask_evaluation_info()

        evaluators_available = Helpers.find_evaluator_availables(self.bot, evaluation_info)

        def find_evaluation_date(evaluation_info):
            hour = evaluation_info[HOUR]

            # finding next calendar day for the given week day
            evaluation_date = Helpers.next_weekday(datetime.now(), Constants.week_days.index(evaluation_info[DAY]))
            # finding evaluation hour and converting to military time
            evaluation_hour = int(hour.split(':')[0]) if hour[-2:] == 'am' else int(hour.split(':')[0])  + 12
            
            evaluation_date = evaluation_date.replace(hour=evaluation_hour, minute=0, second=0)

            return evaluation_date

        print(f"-----\n{teacher.user.nick} scheduled an evaluation.\nEvaluators: {[ev.name for ev in evaluators_available]}")
        hours = Constants.times_of_day[evaluation_info[PERIOD]].copy()
        while hours:
            hour_view = HourView(hours)

            await teacher.user.send(f"Select the hour you'd like to be evaluated on.", view=hour_view)
            await hour_view.wait()
            hour = hour_view.hour

            if hour:
                hours.remove(hour)
                evaluation_info[HOUR] = hour

                evaluation_confirmation_view = EvaluatorConfirmationView(evaluators_available.copy())
                evaluator_requests_sent = []
                for evaluator in evaluators_available:
                    msg = await evaluator.send(f"Can you evaluate {teacher.user.nick} on {evaluation_info[COURSE]} coming {evaluation_info[DAY]} at {evaluation_info[HOUR]}?",
                        view=evaluation_confirmation_view)
                    evaluator_requests_sent.append((msg, evaluator))

                await teacher.user.send(f'Your request was sent to all evaluators available. Please be patient, you will receive a confirmation message if an evaluator is available')

                await evaluation_confirmation_view.wait()
                if evaluation_confirmation_view.evaluator_available:
                    # for unanswered_eval in evaluation_confirmation_view.evaluators_requested:
                    MSG = 0
                    EVALUATOR = 1
                    id_evaluators_requested = [e.id for e in evaluation_confirmation_view.evaluators_requested]
                    for unanswered_request_message in evaluator_requests_sent:
                        if unanswered_request_message[EVALUATOR].id in id_evaluators_requested:
                            await unanswered_request_message[MSG].edit(content='*This evaluation was accepted by another evaluator.*', view=None)

                    evaluator_available = evaluation_confirmation_view.evaluator_available
                    for member in interaction.guild.members:
                        if member.id == evaluator_available.id:
                            evaluator_available = member
                            break
        
                    evaluation_date = find_evaluation_date(evaluation_info)

                    evaluation = [f"{evaluator_available.name}#{evaluator_available.discriminator} AKA {evaluator_available.nick}",
                                    f"{teacher.user.name}#{teacher.user.discriminator} AKA {teacher.user.nick}",
                                    f"{evaluation_date.strftime('%m/%d/%Y %H:%M:%S')}",
                                    evaluation_info[COURSE],
                                    datetime.now().strftime('%m/%d/%Y %H:%M:%S')]

                    EvaluationSheet.append_confirmed_evaluation(evaluation)

                    # adding this evaluation to the database of evaluator and teacher
                    DB.add_evaluation(evaluator_available.id, '$'.join(evaluation))
                    DB.add_evaluation(teacher.user.id, '$'.join(evaluation))

                    await Helpers.give_role(self.bot, teacher.user, "Pending Evaluation")

                    await teacher.user.send(f"Evaluation confirmed! Take note of day and time, {evaluation_date.month}/{evaluation_date.day} at {evaluation_info[HOUR]}. Say hi to your evaluator on Discord by adding them, {evaluator_available.name}#{evaluator_available.discriminator}")
                    await evaluator_available.send(f"Evaluation confirmed! Take note of day and time, {evaluation_date.month}/{evaluation_date.day} at {evaluation_info[HOUR]}. Say hi to the teacher you will evaluate on Discord by adding them, {teacher.user.name}#{teacher.user.discriminator}")

                    print(f"Evaluation confirmed: {evaluation}")
                    break

                else:
                    await teacher.user.send("All evaluators refused your request.")

            else:
                await teacher.user.send('Evaluation scheduling process canceled.')
                break

            if not hours:
                await teacher.user.send('Sorry, there are no evaluators available.')

        self.scheduling_now.remove(interaction.user)

class ScheduleCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def sent_in_schedule_evaluation(ctx):
        return ctx.channel.name == '📅schedule-evaluation📅'

    @commands.command()
    @commands.is_owner()
    async def update_schedule_message(self, ctx):
        msgs = await ctx.channel.history().flatten()
        for msg in msgs:
            await msg.delete()
        await ctx.send('\u200b', view=ScheduleView(self.bot))

def setup(bot):
    global instance 
    instance = ScheduleCommand(bot)
    bot.add_cog(instance)