import os

from dotenv import load_dotenv


load_dotenv()


MAILPIT_SMTP_HOST = os.getenv(
    "MAILPIT_SMTP_HOST"
)

MAILPIT_SMTP_PORT = int(
    os.getenv("MAILPIT_SMTP_PORT")
)

MAILPIT_API_URL = os.getenv(
    "MAILPIT_API_URL"
)

USER_EMAIL = os.getenv(
    "USER_EMAIL"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)