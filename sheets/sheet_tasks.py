from textwrap import dedent

from discord.ext import tasks, commands

from db.db_management import DB
from sheets.evaluation_sheet_management import EvaluationSheet
from sheets.db_sheet_management import DBSheet
from cogs.helpers import Helpers
from cogs.constants import Constants
from cogs.email import Email

class SheetTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_evaluation_sheet.start()
        self.update_database_sheet.start()

    @tasks.loop(minutes=10)
    async def update_evaluation_sheet(self):
        completed_evaluations, to_delete = EvaluationSheet.find_completed_evaluations()
        if completed_evaluations:
            for evaluation in completed_evaluations:
                DB.c.execute("SELECT * FROM members WHERE evaluations LIKE ? AND is_evaluator=?", (f"%{'$'.join(evaluation[:-2])}%", 0,))
                teacher = DB.c.fetchone()
                
                member = self.bot.guilds[0].get_member(int(teacher[0]))
                await Helpers.give_role(self.bot, member, f"Evaluated on {evaluation[3]}")

                DB.remove_evaluation(teacher[0], evaluation[:-2])

                # I have to fetch again because I changed the database
                teacher = DB.fetch_one(teacher[0])

                if not teacher[2]:
                    await Helpers.remove_role(member, 'Pending Evaluation')

                DB.c.execute("SELECT * FROM members WHERE evaluations LIKE ? AND is_evaluator=?", (f"%{'$'.join(evaluation[:-2])}%", 1,))
                evaluator = DB.c.fetchone()

                DB.remove_evaluation(evaluator[0], evaluation[:-2])

            EvaluationSheet.update_completed_evaluations(completed_evaluations, to_delete)

            for evaluation in completed_evaluations:
                n = '\n'
                Email.send("Evaluation Completed",
                    f'Evaluation marked as complete and added to the sheet.\n\nInformation\n{n.join([f"{it}: {iv}" for it, iv in zip(Constants.info_order, evaluation)])}')

        canceled_evaluations, to_delete = EvaluationSheet.find_canceled_evaluations()
        if canceled_evaluations:
            # not sure if it is the best place to be
            for evaluation in canceled_evaluations:
                await SheetTasks.evaluation_canceled_warning(self.bot, evaluation)

                DB.c.execute("SELECT * FROM members WHERE evaluations LIKE ? AND is_evaluator=?", (f"%{'$'.join(evaluation[:-3])}%", 0,))
                teacher = DB.c.fetchone()

                DB.remove_evaluation(teacher[0], evaluation[:-3])

                DB.c.execute("SELECT * FROM members WHERE id=? AND is_evaluator=?", (teacher[0], 0,))
                teacher = DB.c.fetchone()

                member = self.bot.guilds[0].get_member(int(teacher[0]))
                if not teacher[2]:
                    await Helpers.remove_role(member, 'Pending Evaluation')

                DB.c.execute("SELECT * FROM members WHERE evaluations LIKE ? AND is_evaluator=?", (f"%{'$'.join(evaluation[:-3])}%",1,))
                evaluator = DB.c.fetchone()

                DB.remove_evaluation(evaluator[0], evaluation[:-3])

            EvaluationSheet.update_canceled_evaluations(canceled_evaluations, to_delete)

    # TODO delete this function and simply use the one-liner forloop with zip
    # TODO maybe create a function that does the one-liner forlooop
    @staticmethod
    async def evaluation_canceled_warning(bot, evaluation):
        Email.send('Evaluatoin Canceled',
            dedent(f"""
                    Reason: {evaluation[7]}
                    Evaluator: {evaluation[0]}
                    Teacher: {evaluation[1]}
                    Evaluation Time: {evaluation[2]}
                    Course: {evaluation[3]}
                    Evaluation Confirmation Time: {evaluation[4]}"""))

        evaluator = Helpers.get_member(bot.guilds[0], evaluation[0])
        if evaluation[7] == 'Not completed before cancelation time':
            await evaluator.send(f"Hello, this is a warning message! An evaluation you were supposed to complete on {evaluation[2]} on {evaluation[3]} for {evaluation[1]} was marked as incomplete by me because it was never marked as complete. Please contact a Manager immediately!")

    @staticmethod
    @tasks.loop(minutes=10)
    async def update_database_sheet():
        members, evaluators = DB.fetch_all()

        DBSheet.update_database_sheet(members, evaluators)

    @update_evaluation_sheet.before_loop
    async def before_tasks(self):
        await self.bot.wait_until_ready()
    
def setup(bot):
    bot.add_cog(SheetTasks(bot))