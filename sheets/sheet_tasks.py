from discord.ext import tasks, commands

from db.db_management import DB
from sheets.evaluation_sheet_management import EvaluationSheet
from sheets.db_sheet_management import DBSheet
from cogs.helpers import Helpers

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
                DB.c.execute("SELECT * FROM members WHERE evaluations LIKE ?", (f"%{'$'.join(evaluation[:-2])}%",))
                teacher = DB.c.fetchone()
                
                member = self.bot.guilds[0].get_member(int(teacher[0]))
                await Helpers.give_role(self.bot, member, f"Evaluated on {evaluation[3]}")

                DB.remove_evaluation(teacher[0], evaluation[:-2])

                # I have to fetch again because I changed the database
                teacher = DB.fetch_one(teacher[0])

                if not teacher[2]:
                    await Helpers.remove_role(self.bot, member, 'Pending Evaluation')

                DB.c.execute("SELECT * FROM members WHERE evaluations LIKE ?", (f"%{'$'.join(evaluation[:-2])}%",))
                evaluator = DB.c.fetchone()

                DB.remove_evaluation(evaluator[0], evaluation[:-2])

            EvaluationSheet.update_completed_evaluations(completed_evaluations, to_delete)

        canceled_evaluations, to_delete = EvaluationSheet.find_canceled_evaluations()
        if canceled_evaluations:
            # not sure if it is the best place to be
            for evaluation in canceled_evaluations:
                await Helpers.evaluation_canceled_warning(self.bot, evaluation)

                DB.c.execute("SELECT * FROM members WHERE evaluations LIKE ?", (f"%{'$'.join(evaluation[:-3])}%",))
                teacher = DB.c.fetchone()

                DB.remove_evaluation(teacher[0], evaluation[:-3])

                DB.c.execute("SELECT * FROM members WHERE id=?", (teacher[0],))
                teacher = DB.c.fetchone()

                member = self.bot.guilds[0].get_member(int(teacher[0]))
                if not teacher[2]:
                    print('Passed the teacher 2 if statement')
                    await Helpers.remove_role(self.bot, member, 'Pending Evaluation')
                    print('Pending evaluation remove')

                DB.c.execute("SELECT * FROM members WHERE evaluations LIKE ?", (f"%{'$'.join(evaluation[:-3])}%",))
                evaluator = DB.c.fetchone()

                DB.remove_evaluation(evaluator[0], evaluation[:-3])

            EvaluationSheet.update_canceled_evaluations(canceled_evaluations, to_delete)

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