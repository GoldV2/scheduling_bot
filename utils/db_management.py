import sqlite3
import os

path = os.path.dirname(os.path.realpath(__file__))

conn = sqlite3.connect(path + '/' + 'users.db')
# conn = sqlite3.connect(":memory:")

#######################################################################

c = conn.cursor()

# c.execute("""CREATE TABLE teachers
#              (id integer,
#               name text,
#               evaluations text)""")

# c.execute("""CREATE TABLE evaluators
#              (id integer,
#               name text,
#               available text,
#               courses text,
#               evaluations text)""")

#######################################################################

def add_teacher(id, name):
    with conn:
        c.execute("INSERT INTO teachers VALUES (?, ?, ?)",
                   (id, name, ''))

def remove_teacher(id):
    with conn:
        c.execute("DELETE from teachers WHERE id=?",
                  (id,))

# not being used
def update_teacher_name(id, name):
    with conn:
        c.execute("""UPDATE teachers SET name=? WHERE id=?""",
                     (name, id))

def add_teacher_evaluation(id, evaluation):
    c.execute("SELECT * FROM teachers WHERE id=?", (id,))
    teacher = c.fetchone()
    
    if teacher[2]:
        evaluations = teacher[2] + "$$" + evaluation

    else:
        evaluations = evaluation

    with conn:
        c.execute("""UPDATE teachers SET evaluations=? WHERE id=?""",
                     (evaluations, id))

def teacher_remove_evaluation(id, evaluation):
    c.execute("SELECT * FROM teachers WHERE id=?", (id,))
    teacher = c.fetchone()

    evaluations = teacher[2].split('$$')
    evaluations.remove('$'.join(evaluation))

    with conn:
        c.execute("""UPDATE teachers SET evaluations=? WHERE id=?""",
                     ('$$'.join(evaluations), id))

def teacher_remove_evaluations(id):
    c.execute("SELECT * FROM teachers WHERE id=?", (id,))
    teacher = c.fetchone()

    with conn:
        c.execute("""UPDATE teachers SET evaluations=? WHERE id=?""",
                     ('', id))

#######################################################################

def add_evaluator(id, name, available, courses):
    with conn:
        c.execute("INSERT INTO evaluators VALUES (?, ?, ?, ?, ?)",
                   (id, name, available, courses, ''))

def remove_evaluator(id):
    with conn:
        c.execute("DELETE from evaluators WHERE id=?",
                  (id,))

# not being used
def update_evaluator_name(id, name):
    with conn:
        c.execute("""UPDATE evaluators SET name=? WHERE id=?""",
                     (name, id))

def update_evaluator_availability(id, availability):
    with conn:
        c.execute("""UPDATE evaluators SET available=? WHERE id=?""",
                     (availability, id))

def update_evaluator_courses(id, courses):
    with conn:
        c.execute("""UPDATE evaluators SET courses=? WHERE id=?""",
                     (courses, id))

def add_evaluator_evaluation(id, evaluation):
        c.execute("SELECT * FROM evaluators WHERE id=?", (id,))
        evaluator = c.fetchone()
        
        if evaluator[4]:
            evaluations = evaluator[4] + "$$" + evaluation

        else:
            evaluations = evaluation

        with conn:
            c.execute("""UPDATE evaluators SET evaluations=? WHERE id=?""",
                     (evaluations, id))

def evaluator_remove_evaluation(id, evaluation):
    c.execute("SELECT * FROM evaluators WHERE id=?", (id,))
    evaluator = c.fetchone()

    evaluations = evaluator[4].split('$$')
    evaluations.remove('$'.join(evaluation))

    with conn:
        c.execute("""UPDATE evaluators SET evaluations=? WHERE id=?""",
                     ('$$'.join(evaluations), id))

def evaluator_remove_evaluations(id):
    c.execute("SELECT * FROM evaluators WHERE id=?", (id,))
    evaluator = c.fetchone()

    with conn:
        c.execute("""UPDATE evaluators SET evaluations=? WHERE id=?""",
                     ('', id))

#######################################################################

def fetch_all():
    c.execute("SELECT * FROM teachers")
    teachers = c.fetchall()
    c.execute("SELECT * FROM evaluators")
    evaluators = c.fetchall()

    return teachers, evaluators