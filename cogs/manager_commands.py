import os
from datetime import datetime

from discord.ext import commands

from bot import path
from cogs import events
from cogs import sheet_tasks
from utils import db_management
from cogs import helpers


class ManagerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def manager_command_check(ctx):
        return ctx.channel.name == 'manager-commands'

    @commands.command()
    @commands.check(manager_command_check)
    async def make_evaluator(self, ctx, evaluator_id):

        evaluator = ctx.guild.get_member(int(evaluator_id))
        if "Evaluator" not in [role.name for role in evaluator.roles]:
            db_management.remove_teacher(evaluator.id)

            availability = await helpers.Helpers.ask_availability(evaluator, self.bot)
            courses = await helpers.Helpers.ask_courses(evaluator, self.bot)
            
            db_management.add_evaluator(evaluator.id, evaluator.nick, availability, courses)
            await helpers.Helpers.give_role(ctx, evaluator, 'Evaluator')

            await helpers.Helpers.update_evaluator_availability_message(ctx, helpers.Helpers.get_evaluator_availabilities())

        else:
            print("User is already an evaluator.")

    @commands.command()
    @commands.check(manager_command_check)
    async def reset_member(self, ctx, member_id):
        member = ctx.guild.get_member(int(member_id))
        await events.Events.on_member_remove(member)

        await helpers.Helpers.update_evaluator_availability_message(ctx, helpers.Helpers.get_evaluator_availabilities())

    @commands.command()
    @commands.check(manager_command_check)
    async def update_database_sheet(self, ctx):
        await sheet_tasks.SheetTasks.update_database_sheet()

    @commands.command()
    @commands.check(manager_command_check)
    async def update_evaluation_sheet(self, ctx):
        sheet_tasks.update_evaluation_sheet()

    @commands.command()
    @commands.is_owner()
    async def view_db(self, ctx):
        db_management.c.execute("SELECT * FROM teachers")
        teachers = db_management.c.fetchall()
        db_management.c.execute("SELECT * FROM evaluators")
        evaluators = db_management.c.fetchall()

        print(teachers, "teachers")
        print(evaluators, 'evaluators')

    @commands.command()
    @commands.is_owner()
    async def reload_cogs(self, ctx):
        for file in os.listdir(path + "/cogs"):
            if file.endswith(".py"):
                self.bot.reload_extension(f"cogs.{file[:-3]}")

        print(f"Cogs reloaded successfuly on {datetime.now()}")

    @commands.command()
    @commands.is_owner()
    async def clear_evaluations(self, ctx, member_id):
        member = ctx.guild.get_member(int(member_id))
        if 'Evaluator' in [role.name for role in member.roles]:
            db_management.evaluator_remove_evaluations(int(member_id))
        
        else:
            db_management.teacher_remove_evaluations(int(member_id))


def setup(bot):
    bot.add_cog(ManagerCommands(bot))