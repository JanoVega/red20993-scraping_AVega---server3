
# permite la salida con el puerto 25:
# sudo ufw allow 25 ### HECHO ###

# Import smtplib for the actual sending function
import smtplib
import re
# Import the email modules we'll need
from email.message import EmailMessage

from utils.date_utils import get_date


def send_check_msg():

    date = get_date('hoy')    
    date = re.sub('/', '.', date)

    textfile = 'check_informe_'+date+'.txt'
    # Open the plain text file whose name is in textfile for reading.
    with open(textfile) as fp:
        # Create a text/plain message
        msg = EmailMessage()
        msg.set_content(fp.read())

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = f'The contents of {textfile}'
    msg['From'] = 'test de jano'
    msg['To'] = 'a.vega06@ufromail.cl'
    # Send the message via our own SMTP server.
    s = smtplib.SMTP('localhost', port=25)
    #s.starttls()
    s.send_message(msg)
    s.quit()


def send_informe_msg():

    date = get_date('hoy')    
    date = re.sub('/', '.', date)
    textfile = 'informe'+date+'.txt'
    # Open the plain text file whose name is in textfile for reading.
    with open(textfile) as fp:
        # Create a text/plain message
        msg = EmailMessage()
        msg.set_content(fp.read())

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = f'The contents of {textfile}'
    msg['From'] = 'test de jano'
    msg['To'] = 'a.vega06@ufromail.cl'
    # Send the message via our own SMTP server.
    s = smtplib.SMTP('localhost', port=25)
    #s.starttls()
    s.send_message(msg)
    s.quit()

def send_err_msg():
    return 0