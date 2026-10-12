import json
import logging
import os
import requests

from config import MAILPIT_API_URL


# ==========================================
# ASSISTANT EMAIL ADDRESS
# ==========================================

ASSISTANT_EMAIL = "assistant@example.com"

PROCESSED_FILE = "processed_emails.json"


# ==========================================
# LOAD PROCESSED EMAIL IDS
# ==========================================

def load_processed_ids():

    if not os.path.exists(PROCESSED_FILE):
        return set()

    try:

        with open(
            PROCESSED_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return set(str(item) for item in data)

        return set()

    except Exception as e:

        logging.warning(
            "Could not read processed_emails.json: %s",
            e
        )

        return set()


# ==========================================
# SAVE PROCESSED EMAIL ID
# ==========================================

def mark_email_processed(email_id):

    if not email_id:
        return

    processed_ids = load_processed_ids()

    processed_ids.add(str(email_id))

    try:

        with open(
            PROCESSED_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                sorted(processed_ids),
                file,
                indent=4
            )

    except Exception as e:

        logging.error(
            "Failed to save processed email ID: %s",
            e
        )


# ==========================================
# CHECK ASSISTANT EMAIL
# ==========================================

def is_assistant_email(email):

    sender = email.get("From", "")

    if isinstance(sender, dict):

        sender_email = (
            sender.get("Address")
            or sender.get("Email")
            or ""
        )

    else:

        sender_email = str(sender)

    sender_email = (
        sender_email
        .strip()
        .lower()
    )

    return (
        sender_email
        == ASSISTANT_EMAIL.lower()
    )


# ==========================================
# GET INCOMING EMAILS
# ==========================================

def get_emails():

    logging.info(
        "Fetching email list from Mailpit"
    )

    processed_ids = load_processed_ids()

    try:

        response = requests.get(
            f"{MAILPIT_API_URL}/api/v1/messages",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        all_emails = data.get(
            "messages",
            []
        )

        logging.info(
            "Total emails in Mailpit: %d",
            len(all_emails)
        )

        incoming_emails = []

        skipped_assistant = 0
        skipped_processed = 0

        for email in all_emails:

            email_id = str(
                email.get("ID", "")
            )

            subject = email.get(
                "Subject",
                "Unknown Subject"
            )

            # ==================================
            # SKIP ASSISTANT'S OWN EMAILS
            # ==================================

            if is_assistant_email(email):

                skipped_assistant += 1

                logging.info(
                    "Skipping assistant email: %s",
                    subject
                )

                continue

            # ==================================
            # SKIP ALREADY PROCESSED EMAILS
            # ==================================

            if email_id and email_id in processed_ids:

                skipped_processed += 1

                logging.info(
                    "Skipping already processed email: %s",
                    subject
                )

                continue

            incoming_emails.append(email)

        logging.info(
            "Assistant emails skipped: %d",
            skipped_assistant
        )

        logging.info(
            "Already processed emails skipped: %d",
            skipped_processed
        )

        logging.info(
            "New incoming emails returned: %d",
            len(incoming_emails)
        )

        return incoming_emails

    except requests.RequestException as e:

        logging.error(
            "Failed to fetch emails from Mailpit: %s",
            e
        )

        return []


# ==========================================
# GET EMAIL DETAILS
# ==========================================

def get_email_details(message_id):

    logging.info(
        "Fetching email details: %s",
        message_id
    )

    try:

        response = requests.get(
            f"{MAILPIT_API_URL}/api/v1/message/{message_id}",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:

        logging.error(
            "Failed to fetch email details %s: %s",
            message_id,
            e
        )

        return {}


# ==========================================
# GET EMAIL CONTENT
# ==========================================

def get_email_content(email):

    snippet = email.get("Snippet")

    if snippet:
        return str(snippet).strip()

    text = email.get("Text")

    if text:
        return str(text).strip()

    body = email.get("Body")

    if body:
        return str(body).strip()

    return ""