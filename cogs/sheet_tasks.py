from discord.ext import tasks, commands

from utils import db_management
from utils import db_sheet_management
from utils import evaluation_sheet_management
from cogs import helpers

class SheetTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_evaluation_sheet.start()
        self.update_database_sheet.start()

    @tasks.loop(minutes=10)
    async def update_evaluation_sheet(self):
        completed_evaluations, to_delete = evaluation_sheet_management.find_completed_evaluations()
        if completed_evaluations:
            for evaluation in completed_evaluations:
                db_management.c.execute("SELECT * FROM teachers WHERE evaluations LIKE ?", (f"%{'$'.join(evaluation[:-2])}%",))
                teacher = db_management.c.fetchone()
                
                member = self.bot.guilds[0].get_member(int(teacher[0]))
                await helpers.Helpers.give_role(member, member, f"Evaluated on {evaluation[3]}")

                db_management.teacher_remove_evaluation(teacher[0], evaluation[:-2])

                db_management.c.execute("SELECT * FROM teachers WHERE id=?", (teacher[0],))
                teacher = db_management.c.fetchone()

                if not teacher[2]:
                    await helpers.Helpers.remove_role(member, member, 'Pending Evaluation')

                db_management.c.execute("SELECT * FROM evaluators WHERE evaluations LIKE ?", (f"%{'$'.join(evaluation[:-2])}%",))
                evaluator = db_management.c.fetchone()

                db_management.evaluator_remove_evaluation(evaluator[0], evaluation[:-2])

            evaluation_sheet_management.update_completed_evaluations(completed_evaluations, to_delete)

        canceled_evaluations, to_delete = evaluation_sheet_management.find_canceled_evaluations()
        if canceled_evaluations:
            # not sure if it is the best place to be
            for evaluation in canceled_evaluations:
                await helpers.Helpers.evaluation_canceled_warning(self.bot, evaluation)

                db_management.c.execute("SELECT * FROM teachers WHERE evaluations LIKE ?", (f"%{'$'.join(evaluation[:-3])}%",))
                teacher = db_management.c.fetchone()

                db_management.teacher_remove_evaluation(teacher[0], evaluation[:-3])

                db_management.c.execute("SELECT * FROM teachers WHERE id=?", (teacher[0],))
                teacher = db_management.c.fetchone()

                member = self.bot.guilds[0].get_member(int(teacher[0]))
                if not teacher[2]:
                    await helpers.Helpers.remove_role(member, member, 'Pending Evaluation')

                db_management.c.execute("SELECT * FROM evaluators WHERE evaluations LIKE ?", (f"%{'$'.join(evaluation[:-3])}%",))
                evaluator = db_management.c.fetchone()

                db_management.evaluator_remove_evaluation(evaluator[0], evaluation[:-3])

            evaluation_sheet_management.update_canceled_evaluations(canceled_evaluations, to_delete)

    @staticmethod
    @tasks.loop(minutes=10)
    async def update_database_sheet():
        teachers, evaluators = db_management.fetch_all()

        db_sheet_management.update_database_sheet(teachers, evaluators)

    # error AttributeError: 'staticmethod' object has no attribute 'before_loop'
    # @update_database_sheet.before_loop
    @update_evaluation_sheet.before_loop
    async def before_tasks(self):
        await self.bot.wait_until_ready()
    
def setup(bot):
    bot.add_cog(SheetTasks(bot))