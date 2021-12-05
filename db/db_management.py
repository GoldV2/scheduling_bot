import sqlite3
import os

from discord.ext import commands

# TODO create decorator call with_conn to avoid having to use a with statement everywhere

class DB(commands.Cog):
    
    path = os.path.dirname(os.path.realpath(__file__))
    conn = sqlite3.connect(path + '/' + 'members.db')
    # conn = sqlite3.connect(":memory:")

    c = conn.cursor()

    def __init__(self, bot):
        self.bot = bot
    
    @staticmethod
    def create_db():
        with DB.conn:
            DB.DB.c.execute("""CREATE TABLE members
                        (id integer,
                        name text,
                        evaluations text,
                        is_evaluator integer)""")

            DB.DB.c.execute("""CREATE TABLE evaluators
                        (id integer,
                        available text,
                        courses text)""")
    
    @staticmethod
    def add_member(id, name):
        with DB.conn:
            DB.c.execute("INSERT INTO members VALUES (?, ?, ?, ?)",
                (id, name, '', 0,))

    @staticmethod
    def remove_member(id):
        with DB.conn:
            DB.c.execute("DELETE FROM members WHERE id=?",
                (id,))

            DB.c.execute("SELECT * FROM evaluators WHERE id=?",
                (id,))
            
            evaluator = DB.c.fetchone()
            if evaluator:
                DB.c.execute("DELETE FROM evaluators WHERE id=?",
                    (id,))


    @staticmethod
    def update_member_name(id, name):
        with DB.conn:
            DB.c.execute("""UPDATE members SET name=? WHERE id=?""",
                        (name, id))
    
    @staticmethod
    def add_evaluation(id, evaluation):
        DB.c.execute("SELECT * FROM members WHERE id=?", (id,))
        member = DB.c.fetchone()
        
        if member[2]:
            evaluations = member[2] + "$$" + evaluation

        else:
            evaluations = evaluation

        with DB.conn:
            DB.c.execute("""UPDATE members SET evaluations=? WHERE id=?""",
                        (evaluations, id))
    
    @staticmethod
    def remove_evaluation(id, evaluation):
        DB.c.execute("SELECT * FROM members WHERE id=?", (id,))
        member = DB.c.fetchone()

        evaluations = member[2].split('$$')
        evaluations.remove('$'.join(evaluation))

        with DB.conn:
            DB.c.execute("""UPDATE members SET evaluations=? WHERE id=?""",
                        ('$$'.join(evaluations), id))
    
    @staticmethod
    def remove_evaluations(id):
        with DB.conn:
            DB.c.execute("""UPDATE members SET evaluations=? WHERE id=?""",
                        ('', id))

    #######################################################################
    
    @staticmethod
    def add_evaluator(id, available, courses):
        with DB.conn:
            DB.c.execute("INSERT INTO evaluators VALUES (?, ?, ?)",
                    (id, available, courses,))
    
            DB.c.execute("UPDATE members SET is_evaluator=? WHERE id=?",
                (1, id))

    @staticmethod
    def remove_evaluator(id):
        with DB.conn:
            DB.c.execute("DELETE FROM evaluators WHERE id=?",
                (id,))

            DB.c.execute("UPDATE members SET is_evaluator=? WHERE id=?",
                (0, id))

    @staticmethod
    def update_evaluator_availability(id, availability):
        with DB.conn:
            DB.c.execute("""UPDATE evaluators SET available=? WHERE id=?""",
                        (availability, id))
    
    @staticmethod
    def update_evaluator_courses(id, courses):
        with DB.conn:
            DB.c.execute("""UPDATE evaluators SET courses=? WHERE id=?""",
                        (courses, id))

    #######################################################################
    
    @staticmethod
    def fetch_all():
        with DB.conn:
            DB.c.execute("SELECT * FROM members")
            members = DB.c.fetchall()
            DB.c.execute("SELECT * FROM evaluators")
            evaluators = DB.c.fetchall()

            return members, evaluators

    @staticmethod
    def fetch_one(id):
        with DB.conn:
            DB.c.execute("SELECT * FROM members WHERE id=?",
                (id,))

            return DB.c.fetchone()

    @staticmethod
    def fetch_evaluator(id):
        with DB.conn:
            DB.c.execute("SELECT * FROM evaluators WHERE id=?",
                (id,))

            return DB.c.fetchone()

def setup(bot):
    bot.add_cog(DB(bot))

