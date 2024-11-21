import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import getenv
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SMTP_PASSWORD = getenv("GOOGLE_SMTP_PASSWORD", None)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/backend/email.log"),
        logging.StreamHandler(),
    ],
)


def send_email_via_gmail(subject: str, body: str, to_email: str):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  
    sender_email = "kcw2371@gmail.com" 
    sender_password = GOOGLE_SMTP_PASSWORD 

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
    except Exception as e:
        logging.error(e)



