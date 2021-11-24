from discord.ext import commands

class Constants(commands.Cog):
    
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_emojis = {'Monday': '1️⃣', 'Tuesday': '2️⃣', 'Wednesday': '3️⃣', 'Thursday': '4️⃣', 'Friday': '5️⃣', 'Saturday': '6️⃣', 'Sunday': '7️⃣'}
    # reversing the dictionary "day_emojis"
    emoji_days = {'1️⃣': 'Monday', '2️⃣': 'Tuesday', '3️⃣': 'Wednesday', '4️⃣': 'Thursday', '5️⃣': 'Friday', '6️⃣': 'Saturday', '7️⃣': 'Sunday'}
    # emoji_days = {value : key for (key, value) in day_emojis.items()}

    
    # avail_emoji_time_of_day = {'1️⃣': 'Morning', '2️⃣': 'Afternoon', '3️⃣': 'Evening',
    #                            '4️⃣': 'Morning and Afternoon', '5️⃣': 'Morning and Evening',
    #                            '6️⃣': 'Afternoon and Evening', '0️⃣': ''}

    # avail_emoji_time_of_day = {'🌇': 'Morning', '🏙️': 'Afternoon', '🌃': 'Evening'}

    emoji_time_of_day = {'🌇': 'Morning', '🏙️': 'Afternoon', '🌃': 'Evening'}
    time_of_day_emojis = {'Morning': '🌇', 'Afternoon': '🏙️', 'Evening': '🌃'} 

    times_of_day = {'Morning': ['8:00am', '9:00am', '10:00am', '11:00am'],
                   'Afternoon': ['2:00pm', '3:00pm', '4:00pm', '5:00pm'],
                   'Evening': ['6:00pm', '7:00pm', '8:00pm', '9:00pm']}


    emoji_courses = {'0️⃣': '000 Scratch Junior', '1️⃣': '001 Scratch Introduction',
                     '🔼': '001+ Scratch Game Design', '2️⃣': '002 Scratch+AI',
                     '3️⃣': '003 Python', '🔽': '003+ Python Pygame',
                     '5️⃣': '005 Java', '6️⃣': '006 Data Structures',
                     '📕': '101 Arduino', '📙': '201 HTML/CSS', '📗': '301 Python+AI'}
    # reversing the dictionary "emoji_courses"
    course_emojis = {'000 Scratch Junior': '0️⃣', '001 Scratch Introduction': '1️⃣',
                     '001+ Scratch Game Design': '🔼', '002 Scratch+AI': '2️⃣',
                     '003 Python': '3️⃣', '003+ Python Pygame': '🔽',
                     '005 Java': '5️⃣', '006 Data Structures': '6️⃣',
                     '101 Arduino': '📕', '201 HTML/CSS': '📙', '301 Python+AI': '📗'}
    # course_emojis = {value : key for (key, value) in emoji_courses.items()}

    check_emojis = '✅❌'

    def __init__(self, bot):
        self.bot = bot
    
def setup(bot):
    bot.add_cog(Constants(bot))