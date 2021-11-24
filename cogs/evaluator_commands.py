from discord.ext import commands

from cogs import helpers
from utils import db_management

class EvaluatorCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.updating_now = []

    def evaluator_command_check(ctx):
        return ctx.channel.name == 'evaluator-commands'

    @commands.command()
    @commands.check(evaluator_command_check)
    async def update_availability(self, ctx):
        evaluator = ctx.author

        # could put this in evaluator_command_check but it will give me a huge error whenever the check fails
        if evaluator in self.updating_now:
            await evaluator.send("Please finish updating before trying again.")
            return

        self.updating_now.append(evaluator)

        availability = await helpers.Helpers.ask_availability(evaluator, self.bot)
        db_management.update_evaluator_availability(evaluator.id, availability)

        await helpers.Helpers.update_evaluator_availability_message(ctx, helpers.Helpers.get_evaluator_availabilities())

        self.updating_now.remove(evaluator)
        await ctx.message.delete()

    @commands.command()
    @commands.check(evaluator_command_check)
    async def update_courses(self, ctx):
        evaluator = ctx.author

        if evaluator in self.updating_now:
            await evaluator.send("Please finish updating before trying again.")
            return

        self.updating_now.append(evaluator)

        courses = await helpers.Helpers.ask_courses(evaluator, self.bot)
        db_management.update_evaluator_courses(evaluator.id, courses)

        evaluator_avai = helpers.Helpers.get_evaluator_availabilities()

        await helpers.Helpers.update_evaluator_availability_message(ctx, evaluator_avai)

        self.updating_now.remove(evaluator)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(EvaluatorCommands(bot))