import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import getenv

from dotenv import load_dotenv

from database.enum import EnvironmentType

load_dotenv()

ENVIRONMENT = getenv("ENVIRONMENT", None)
GOOGLE_SMTP_PASSWORD = getenv("GOOGLE_SMTP_PASSWORD", None)
SENDER_EMAIL = getenv("SENDER_EMAIL", None)
SMTP_SERVER = getenv("SMTP_SERVER", None)
SMTP_PORT = getenv("SMTP_PORT", None)


logger = logging.getLogger("email")
logger.setLevel(logging.INFO)


if ENVIRONMENT == EnvironmentType.PROD:
    file_handler = logging.FileHandler("/home/backend/email.log", delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)


def send_email(subject: str, body: str, to_email: str) -> bool:
    if not SMTP_SERVER or not SMTP_PORT or not SENDER_EMAIL or not GOOGLE_SMTP_PASSWORD:
        return False

    smtp_server = SMTP_SERVER
    smtp_port = SMTP_PORT
    sender_email = SENDER_EMAIL
    sender_password = GOOGLE_SMTP_PASSWORD

    if sender_password is None:
        return False

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
    except Exception as e:
        logging.error(e)

    return True
