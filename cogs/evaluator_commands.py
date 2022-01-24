from textwrap import dedent

import discord
from discord.embeds import Embed
from discord.ext import commands
from discord.utils import get

from db.db_management import DB
from cogs.helpers import Helpers
from cogs.constants import Constants

class AvailabilityDropDown(discord.ui.Select):
    def __init__(self):
    
        options = []

        for week_day in Constants.day_emojis:
            options.append(discord.SelectOption(label=week_day,
                emoji=Constants.day_emojis[week_day]))

        super().__init__(placeholder='Select a day', min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        for button in self.view.children:
            if isinstance(button, discord.ui.Button):
                if button.label != 'Confirm':
                    if button.time_of_day in self.view.availability[self.values[0]]:
                        button.style = discord.ButtonStyle.green
                    else:
                        button.style = discord.ButtonStyle.gray

                    button.label = f"{self.values[0][:3]} {button.time_of_day}"
                    
        await interaction.response.edit_message(content=f'Currently editing availability for {self.values[0]}. Press the "Confirm" button **only** after you are done setting your availability for every day.', view=self.view)

class AvailabilityButton(discord.ui.Button):
    def __init__(self, time_of_day):
        super().__init__(style=discord.ButtonStyle.gray, label=time_of_day)
        self.time_of_day = time_of_day

    async def callback(self, interaction):
        if self.label == self.time_of_day:
            old_content = interaction.message.content
            if 'Please select a day first' in old_content:
                return
            
            else:
                await interaction.response.edit_message(content=old_content + '\n*Please select a day first*')
                return

        view = self.view

        for dropdown in self.view.children:
            if isinstance(dropdown, discord.ui.Select):
                break

        if self.style == discord.ButtonStyle.gray:
            if view.availability[dropdown.values[0]]:
                view.availability[dropdown.values[0]] += f' and {self.time_of_day}'

            else:
                view.availability[dropdown.values[0]] = self.time_of_day
            self.style = discord.ButtonStyle.green

        else:
            current = view.availability[dropdown.values[0]].split(' and ')
            current.remove(self.time_of_day)  
            view.availability[dropdown.values[0]] = ' and '.join(current)
            self.style = discord.ButtonStyle.gray

        await interaction.response.edit_message(view=view)

class AvailabilityView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(AvailabilityDropDown())
        for time_of_day in Constants.time_of_day_emojis:
            self.add_item(AvailabilityButton(time_of_day))

        self.availability = {key: '' for key in Constants.week_days}

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.red)
    async def confirm(self, button, interaction):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

        self.stop()

class CoursesDropDown(discord.ui.Select):
    def __init__(self):
    
        options = []

        for course in Constants.course_emojis:
            options.append(discord.SelectOption(label=course,
                emoji=Constants.course_emojis[course]))

        super().__init__(placeholder='Select the courses you can evaluate for', min_values=1, max_values=len(Constants.emoji_courses), options=options)

    async def callback(self, interaction):
        self.disabled = True
        self.view.courses = ','.join(self.values)
        
        await interaction.response.edit_message(view=self.view)

        self.view.stop()

class CoursesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(CoursesDropDown())

class ProfileView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)

        self.bot = bot
        self.updating_now = []

    async def interaction_check(self, interaction):
        # passing in None as bot because I don't use any methods that require member.bot
        member = Member(None, interaction.user)
        if not member.is_in_db and member.is_evaluator():
            await interaction.response.send_message('Only evaluators can do this.', ephemeral=True)
            return False

        elif interaction.user in self.updating_now:
            await interaction.response.send_message('Finish updating before trying again.', ephemeral=True)
            return False

        return True

    @discord.ui.button(label='View Profile', style=discord.ButtonStyle.blurple, custom_id='view_profile_button')
    async def view_profile(self, button, interaction):
        embed = Embed(title='Your Profile', description=f'Discord user ID: {interaction.user.id}')
        name = interaction.guild.get_member(interaction.user.id).nick
        if interaction.user.avatar:
            embed.set_author(name=name, icon_url=interaction.user.avatar.url)

        else:
            embed.set_author(name=name)

        user = DB.fetch_one(interaction.user.id)
        evaluator = DB.fetch_evaluator(interaction.user.id)

        available = evaluator[1].split(',')
        availability = ''
        for index, week_day in enumerate(Constants.week_days):
            if available[index]:
                availability += f'{week_day}: {available[index]}\n'
        if availability:   
            embed.add_field(name='Availability', value=availability)

        courses = evaluator[2].replace(',', '\n')
        embed.add_field(name='Courses', value=courses)

        evaluations = user[2].split('$$')
        if evaluations != ['']:
            evaluations_value = ''
            for evaluation in evaluations:
                evaluation = evaluation.split('$')
                evaluations_value += f'{evaluation[1]} on {evaluation[2]} on {evaluation[3]}\n'

            embed.add_field(name='Evaluations', value=evaluations_value)

        await interaction.response.send_message(content='\u200b', embed=embed, ephemeral=True)

    @discord.ui.button(label='Update Availability', style=discord.ButtonStyle.gray, custom_id='update_availability_button')
    async def update_availability(self, button, interaction):
        await interaction.response.defer()
        member = Member(None, interaction.user)
        evaluator = member.member

        self.updating_now.append(evaluator)

        availability = await member.ask_availability()
        DB.update_evaluator_availability(evaluator.id, availability)

        self.updating_now.remove(evaluator)
        await interaction.user.send("Successfully set availability!")

    @discord.ui.button(label='Update Courses', style=discord.ButtonStyle.gray, custom_id='update_courses_button')
    async def update_courses(self, button, interaction):
        await interaction.response.defer()
        member = Member(None, interaction.user)
        evaluator = member.member

        self.updating_now.append(evaluator)

        courses = await member.ask_courses()
        DB.update_evaluator_courses(evaluator.id, courses)

        self.updating_now.remove(evaluator)
        await interaction.user.send("Successfully set courses!")

class Member:
    def __init__(self, bot, member):
        self.bot = bot
        self.member = member
        self.roles = [role.name for role in member.roles]

    def is_in_db(self):
        return DB.fetch_one(self.member.id) and 'New Teacher' in self.roles

    def is_evaluator(self):
        IS_EVALUATOR = 0
        return int(DB.fetch_one(self.member.id)[IS_EVALUATOR]) and 'Evaluator' in self.roles

    # TODO make it so that I don't have to reformat the output
    async def ask_availability(self):
        view = AvailabilityView()
        await self.member.send(content='Select a day of the week on the drop-down menu then press the corresponding buttons for when you are available that day. Press the "Confirm" button **only** after you are done setting your availability for every day.',
            view=view)
        
        await view.wait()
        return ','.join(view.availability.values())

    async def ask_courses(self):
        view = CoursesView()
        await self.member.send(content='Select all the courses that you can evaluator for', view=view)

        await view.wait()
        return view.courses

    async def become_evaluator(self):
        await Helpers.remove_role(self.member, 'Evaluator')
        
        available = await self.ask_availability()
        courses = await self.ask_courses()
        await Helpers.give_role(self.bot, self.member, 'Evaluator')

        DB.add_evaluator(self.member.id, available, courses)
        await self.member.send('You successfully became an evaluator!')

class EvaluatorCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.becoming_evaluator = []

    @commands.Cog.listener('on_member_update')
    async def make_evaluator(self, before, after):
        member = Member(self.bot, after)

        before_roles = [role.name for role in before.roles]
        if ('Evaluator' not in before_roles
              and 'Evaluator' in member.roles
              and after not in self.becoming_evaluator):

            if not member.is_in_db():
                await Helpers.remove_role(member.member, 'Evaluator')
                assert member.is_in_db(), f'{member.member.name}#{member.member.discriminator} not in DB, edit name first.'

            self.becoming_evaluator.append(after)
            await member.become_evaluator()
            self.becoming_evaluator.remove(after)

        elif ('Evaluator' in before_roles
              and 'Evaluator' not in member.roles
              and after not in self.becoming_evaluator):

            DB.remove_evaluator(after.id)
    
    @commands.command()
    @commands.is_owner()
    async def update_profile_message(self, ctx):
        await ctx.send('\u200b', view=ProfileView(self.bot))

def setup(bot):
    bot.add_cog(EvaluatorCommands(bot))