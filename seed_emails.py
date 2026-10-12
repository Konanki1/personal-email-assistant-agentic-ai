import smtplib
import logging
from email.message import EmailMessage

from config import (
    MAILPIT_SMTP_HOST,
    MAILPIT_SMTP_PORT,
    USER_EMAIL
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def send_email(sender, recipient, subject, body):
    message = EmailMessage()

    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(
        MAILPIT_SMTP_HOST,
        MAILPIT_SMTP_PORT
    ) as server:
        server.send_message(message)

    logging.info(
        "Email sent successfully: %s",
        subject
    )


def seed_emails():

    emails = [

        # 1. FAMILY EMAIL
        {
            "sender": "mom@example.com",
            "subject": "Family Dinner on Sunday",
            "body": """
Hi Divya,

We are planning a family dinner this Sunday at 7 PM.

Please let us know if you can join.

Love,
Mom
"""
        },

        # 2. WORK EMAIL
        {
            "sender": "manager@company.com",
            "subject": "Urgent: Project Update Required",
            "body": """
Hi Divya,

Please send the project status report before tomorrow at 10 AM.

This is important for our client meeting.

Thanks,
Manager
"""
        },

        # 3. NEWSLETTER EMAIL
        {
            "sender": "newsletter@tech.com",
            "subject": "Weekly Technology Newsletter",
            "body": """
Hi,

Here are the latest technology news and articles.

You are receiving this email because you subscribed
to our weekly newsletter.
"""
        },

        # 4. ORDER UPDATE EMAIL
        {
            "sender": "orders@amazon-example.com",
            "subject": "Your Order Has Been Shipped",
            "body": """
Hi Divya,

Your order number 12345 has been shipped.

Expected delivery: Friday.
"""
        },

        # 5. SPAM EMAIL
        {
            "sender": "winner@spam-example.com",
            "subject": "Congratulations! You Won $1,000,000",
            "body": """
You have won one million dollars.

Click immediately to claim your prize!
"""
        },

        # 6. PERSONAL EMAIL
        {
            "sender": "cousin@example.com",
            "subject": "College Reunion Plans",
            "body": """
Hi Divya,

We are planning a college reunion next month.

It would be great if you could join us.

Let me know if you are interested.

Regards,
Your Cousin
"""
        },

        # 7. WORK EMAIL
        {
            "sender": "teamlead@company.com",
            "subject": "Code Review Meeting",
            "body": """
Hi Divya,

We will have a code review meeting on Thursday at 3 PM.

Please review your assigned modules before the meeting.

Regards,
Team Lead
"""
        },

        # 8. OTHER EMAIL
        {
            "sender": "library@citylibrary.com",
            "subject": "Library Book Return Reminder",
            "body": """
Hello Divya,

This is a reminder that the books borrowed from
the city library should be returned by September 10.

Thank you,
City Library
"""
        },

        # 9. FAMILY EMAIL
        {
            "sender": "sister@example.com",
            "subject": "Grandparents Visiting Next Week",
            "body": """
Hi Divya,

Grandparents are coming to visit us next week.

We are planning to spend some time together on Saturday.

Let me know if you will be home.

Love,
Sister
"""
        },

        # 10. SPAM EMAIL
        {
            "sender": "reward@unknown-mail.com",
            "subject": "Exclusive Cash Reward Waiting For You",
            "body": """
Dear Customer,

You have been selected for an exclusive cash reward
of $50,000.

Claim your reward immediately before it expires.

Congratulations!
"""
        }
    ]

    for email in emails:
        send_email(
            sender=email["sender"],
            recipient=USER_EMAIL,
            subject=email["subject"],
            body=email["body"]
        )


if __name__ == "__main__":

    logging.info("Starting email seeding...")

    seed_emails()

    logging.info("All mock emails sent successfully!")