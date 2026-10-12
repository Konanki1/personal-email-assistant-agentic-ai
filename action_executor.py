import logging
import smtplib
import os
from email.message import EmailMessage
from datetime import datetime

from llm import llm


# ==========================================
# CONFIGURATION
# ==========================================

MAILPIT_HOST = os.getenv("MAILPIT_HOST", "localhost")
MAILPIT_SMTP_PORT = int(os.getenv("MAILPIT_SMTP_PORT", "1025"))

DEFAULT_FROM_EMAIL = os.getenv(
    "EMAIL_ADDRESS",
    "assistant@example.com"
)


# ==========================================
# GENERATE REPLY
# ==========================================

def generate_reply(email, subject):

    email_content = email.get(
        "Snippet",
        ""
    )

    prompt = f"""
Generate a short and appropriate email reply.

Email Subject:
{subject}

Email Content:
{email_content}

Write only the reply message.

Do not add explanations.
"""

    response = llm.invoke(prompt)

    return response.content.strip()


# ==========================================
# SEND EMAIL THROUGH MAILPIT
# ==========================================

def send_email(to_address, subject, body):

    if not to_address:
        raise ValueError("Recipient email address is missing")

    message = EmailMessage()

    message["From"] = DEFAULT_FROM_EMAIL
    message["To"] = to_address
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(
        MAILPIT_HOST,
        MAILPIT_SMTP_PORT
    ) as smtp:

        smtp.send_message(message)


# ==========================================
# EXECUTE ACTION
# ==========================================

def execute_action(action):

    action_type = action.get(
        "action_type"
    )

    subject = action.get(
        "subject",
        ""
    )

    email = action.get(
        "email",
        {}
    )

    logging.info(
        "Executing action: %s for email: %s",
        action_type,
        subject
    )


    # ======================================
    # REPLY
    # ======================================

    if action_type == "reply":

        reply_message = generate_reply(
            email,
            subject
        )

        # Get original sender
        sender = email.get(
            "From",
            {}
        )

        if isinstance(sender, dict):
            recipient = sender.get(
                "Address",
                ""
            )
        else:
            recipient = str(sender)

        if not recipient:

            return {
                "status": "failed",
                "message": (
                    f"Cannot send reply for '{subject}': "
                    "sender address is missing"
                )
            }

        # Send reply through Mailpit
        try:

            send_email(
                recipient,
                f"Re: {subject}",
                reply_message
            )

            print("\n" + "=" * 50)
            print(f"Reply Sent for: {subject}")
            print("=" * 50)
            print(reply_message)
            print("=" * 50)

            return {
                "status": "executed",
                "message": (
                    f"Reply sent successfully to {recipient}"
                ),
                "reply": reply_message,
                "recipient": recipient
            }

        except Exception as e:

            logging.error(
                "Failed to send reply: %s",
                e
            )

            return {
                "status": "failed",
                "message": (
                    f"Failed to send reply for '{subject}': {e}"
                ),
                "reply": reply_message
            }


    # ======================================
    # SEND
    # ======================================

    elif action_type == "send":

        recipient = action.get(
            "recipient"
        )

        message_body = action.get(
            "message",
            ""
        )

        if not recipient:

            return {
                "status": "failed",
                "message": (
                    f"Cannot send email '{subject}': "
                    "recipient is missing"
                )
            }

        if not message_body:

            return {
                "status": "failed",
                "message": (
                    f"Cannot send email '{subject}': "
                    "message body is missing"
                )
            }

        try:

            send_email(
                recipient,
                subject,
                message_body
            )

            return {
                "status": "executed",
                "message": (
                    f"Email sent successfully to {recipient}"
                ),
                "recipient": recipient
            }

        except Exception as e:

            logging.error(
                "Failed to send email: %s",
                e
            )

            return {
                "status": "failed",
                "message": (
                    f"Failed to send email: {e}"
                )
            }


    # ======================================
    # MARK AS SPAM
    # ======================================

    elif action_type == "mark_as_spam":

        # Mailpit does not behave like a real mailbox
        # with a separate Spam folder.
        #
        # For this project we record the classification
        # as spam.

        return {
            "status": "executed",
            "message": (
                f"Email classified as spam: {subject}"
            ),
            "category": "spam"
        }


    # ======================================
    # DELETE
    # ======================================

    elif action_type == "delete":

        # Deletion can be connected to the
        # Mailpit DELETE API later.

        return {
            "status": "executed",
            "message": (
                f"Delete action processed for: {subject}"
            )
        }


    # ======================================
    # DEADLINE REMINDER
    # ======================================

    elif action_type == "deadline_reminder":

        deadline = action.get(
            "deadline"
        )

        if not deadline:

            return {
                "status": "failed",
                "message": (
                    f"No deadline found for: {subject}"
                )
            }

        print("\n" + "=" * 50)
        print("DEADLINE REMINDER")
        print("=" * 50)
        print(f"Subject: {subject}")
        print(f"Deadline: {deadline}")
        print("=" * 50)

        return {
            "status": "executed",
            "message": (
                f"Deadline reminder created for: {subject}"
            ),
            "deadline": deadline
        }


    # ======================================
    # ADD TO CALENDAR
    # ======================================

    elif action_type == "add_to_calendar":

        event_title = action.get(
            "event_title"
        ) or subject

        event_date = action.get(
            "event_date"
        )

        event_time = action.get(
            "event_time"
        )

        if not event_date:

            return {
                "status": "failed",
                "message": (
                    f"Cannot add calendar event: "
                    f"event date is missing for '{subject}'"
                )
            }

        print("\n" + "=" * 50)
        print("CALENDAR EVENT")
        print("=" * 50)

        print(
            f"Title: {event_title}"
        )

        print(
            f"Date: {event_date}"
        )

        print(
            f"Time: {event_time}"
        )

        print("=" * 50)

        return {
            "status": "executed",
            "message": (
                f"Calendar event processed: {event_title}"
            ),
            "event_title": event_title,
            "event_date": event_date,
            "event_time": event_time
        }


    # ======================================
    # UNSUPPORTED ACTION
    # ======================================

    else:
        logging.warning(
            "Unsupported action: %s",
            action_type
        )
        return {
            "status": "not_supported",
            "message": (
                f"Action not supported: {action_type}"
            )
        }