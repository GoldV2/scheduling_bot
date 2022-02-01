# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.message import EmailMessage

# Open the plain text file whose name is in textfile for reading.
msg = EmailMessage()
msg.set_content("Test email coming from the Scheduling Bot")

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = f'Scheduling Bot Test Email'
msg['From'] = 'rafaelpbcp@gmail.com'
msg['To'] = 'office@aigolearning.org'

# Send the message via our own SMTP server.
s = smtplib.SMTP(host='smtp.gmail.com', port=587)
s.starttls()
s.login('rafaelpbcp@gmail.com', 'rvljmowvcjphtzez')
s.send_message(msg)
s.quit()