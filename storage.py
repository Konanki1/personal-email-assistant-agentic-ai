import json
import logging
import os
from email_client import get_emails
from analyzer import analyze_email

DATA_FOLDER = "data"

FILE_PATH = (
    f"{DATA_FOLDER}/analyzed_emails.json"
)


def save_analysis(data):

    logging.info(
        "Saving analyzed email data"
    )

    os.makedirs(
        DATA_FOLDER,
        exist_ok=True
    )

    with open(
        FILE_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            default=str
        )

    logging.info(
        "Analysis saved successfully"
    )