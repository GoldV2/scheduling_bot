import smtplib
from email.message import EmailMessage

from discord.ext import commands

# Send the message via our own SMTP server.


class Email(commands.Cog):
    
    FROM = 'rafaelpbcp@gmail.com'
    TO = ['office@aigolearning.org', 'rafaela@aigolearning.org']

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def send(subject: str, content: str) -> None:
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        s.starttls()
        # TODO use dotenv  to hide this password
        s.login(Email.FROM, 'rvljmowvcjphtzez')
        
        for recipient in Email.TO:
            msg = EmailMessage()
            msg.set_content(content + "\n\nThis email is from the Scheduling Bot")
            
            msg['Subject'] = subject
            msg['From'] = Email.FROM
            msg['To'] = recipient
            
            s.send_message(msg)
        
        s.quit()

def setup(bot):
    bot.add_cog(Email(bot))