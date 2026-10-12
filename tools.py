import logging
from datetime import datetime, date


# ==========================================
# MOCK ACTION TOOLS
# ==========================================

def create_todo(task):

    logging.info(
        "MOCK ACTION: Creating todo -> %s",
        task
    )

    return {
        "status": "success",
        "action": "create_todo",
        "task": task
    }


def add_calendar_event(event):

    logging.info(
        "MOCK ACTION: Adding calendar event -> %s",
        event
    )

    return {
        "status": "success",
        "action": "add_calendar_event",
        "event": event
    }


def flag_email(subject):

    logging.info(
        "MOCK ACTION: Flagging email -> %s",
        subject
    )

    return {
        "status": "success",
        "action": "flag_email",
        "subject": subject
    }


def mark_as_junk(subject):

    logging.info(
        "MOCK ACTION: Marking as junk -> %s",
        subject
    )

    return {
        "status": "success",
        "action": "mark_as_junk",
        "subject": subject
    }


def prepare_reply(subject):

    logging.info(
        "MOCK ACTION: Preparing reply -> %s",
        subject
    )

    return {
        "status": "success",
        "action": "prepare_reply",
        "subject": subject
    }


# ==========================================
# EMAIL RETRIEVAL TOOLS
# ==========================================

def get_urgent_emails(analyzed_emails):

    logging.info(
        "TOOL: Getting urgent emails"
    )

    urgent_emails = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        priority = analysis.get(
            "priority"
        )

        if priority == "urgent":

            urgent_emails.append({

                "subject": item.get(
                    "email",
                    {}
                ).get(
                    "Subject"
                ),

                "summary": analysis.get(
                    "summary"
                ),

                "priority": priority

            })

    return urgent_emails


# ==========================================
# GET EMAILS REQUIRING REPLY
# ==========================================

def get_reply_required_emails(analyzed_emails):

    logging.info(
        "TOOL: Getting emails requiring reply"
    )

    reply_emails = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        if analysis.get(
            "requires_reply"
        ):

            reply_emails.append({

                "subject": item.get(
                    "email",
                    {}
                ).get(
                    "Subject"
                ),

                "summary": analysis.get(
                    "summary"
                )

            })

    return reply_emails


# ==========================================
# GET EMAILS WITH DEADLINES
# ==========================================

def get_deadline_emails(analyzed_emails):

    logging.info(
        "TOOL: Getting emails with deadlines"
    )

    deadline_emails = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        if analysis.get(
            "has_deadline"
        ):

            deadline_emails.append({

                "subject": item.get(
                    "email",
                    {}
                ).get(
                    "Subject"
                ),

                "deadline": analysis.get(
                    "deadline"
                ),

                "summary": analysis.get(
                    "summary"
                )

            })

    return deadline_emails


# ==========================================
# GET TODAY'S EMAILS
# ==========================================

def get_today_emails(analyzed_emails):

    logging.info(
        "TOOL: Getting today's important emails"
    )

    today_emails = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        if analysis.get(
            "is_for_today"
        ):

            today_emails.append({

                "subject": item.get(
                    "email",
                    {}
                ).get(
                    "Subject"
                ),

                "priority": analysis.get(
                    "priority"
                ),

                "summary": analysis.get(
                    "summary"
                )

            })

    return today_emails


# ==========================================
# GET THIS WEEK'S EMAILS
# ==========================================

def get_week_emails(analyzed_emails):

    logging.info(
        "TOOL: Getting this week's important emails"
    )

    week_emails = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        if analysis.get(
            "is_for_this_week"
        ):

            week_emails.append({

                "subject": item.get(
                    "email",
                    {}
                ).get(
                    "Subject"
                ),

                "priority": analysis.get(
                    "priority"
                ),

                "summary": analysis.get(
                    "summary"
                )

            })

    return week_emails


# ==========================================
# GET ALL TODO ITEMS
# ==========================================

def get_all_todos(analyzed_emails):

    logging.info(
        "TOOL: Getting all TODO items"
    )

    all_todos = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        todos = analysis.get(
            "todos",
            []
        )

        for todo in todos:

            all_todos.append({

                "subject": item.get(
                    "email",
                    {}
                ).get(
                    "Subject"
                ),

                "task": todo.get(
                    "task"
                )

            })

    return all_todos


# ==========================================
# GET ALL EVENTS
# ==========================================

def get_all_events(analyzed_emails):

    logging.info(
        "TOOL: Getting all events"
    )

    events = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        if analysis.get(
            "is_event"
        ):

            events.append({

                "subject": item.get(
                    "email",
                    {}
                ).get(
                    "Subject"
                ),

                "event_title": analysis.get(
                    "event_title"
                ),

                "event_date": analysis.get(
                    "event_date"
                ),

                "event_time": analysis.get(
                    "event_time"
                )

            })

    return events


# ==========================================
# SEARCH EMAILS BY CATEGORY
# ==========================================

def get_emails_by_category(
    analyzed_emails,
    category
):

    logging.info(
        "TOOL: Getting emails by category -> %s",
        category
    )

    matching_emails = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        email_category = analysis.get(
            "category"
        )

        if email_category == category:

            matching_emails.append({

                "subject": item.get(
                    "email",
                    {}
                ).get(
                    "Subject"
                ),

                "summary": analysis.get(
                    "summary"
                ),

                "priority": analysis.get(
                    "priority"
                )

            })

    return matching_emails


# ==========================================
# SEARCH EMAIL BY SUBJECT
# ==========================================

def search_email_by_subject(
    analyzed_emails,
    keyword
):

    logging.info(
        "TOOL: Searching emails -> %s",
        keyword
    )

    matching_emails = []

    keyword = keyword.lower()

    for item in analyzed_emails:

        email = item.get(
            "email",
            {}
        )

        subject = email.get(
            "Subject",
            ""
        )

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        # Search in subject
        # Also search in summary and category
        searchable_text = " ".join([
            subject,
            analysis.get("summary") or "",
            analysis.get("category") or ""
        ]).lower()

        if keyword in searchable_text:

            result = {
                "subject": subject,
                "category": analysis.get(
                    "category"
                ),
                "priority": analysis.get(
                    "priority"
                ),
                "summary": analysis.get(
                    "summary"
                )
            }

            # Add deadline only if it exists
            if analysis.get("has_deadline"):

                result["deadline"] = analysis.get(
                    "deadline"
                )

            # Add TODO items if they exist
            todos = analysis.get(
                "todos",
                []
            )

            if todos:

                todo_tasks = []

                for todo in todos:

                    task = todo.get(
                        "task"
                    )

                    if task:
                        todo_tasks.append(task)

                if todo_tasks:

                    result["todos"] = ", ".join(
                        todo_tasks
                    )

            # Add event information if it exists
            if analysis.get("is_event"):

                result["event"] = analysis.get(
                    "event_title"
                )

                result["event_date"] = analysis.get(
                    "event_date"
                )

                result["event_time"] = analysis.get(
                    "event_time"
                )

            matching_emails.append(
                result
            )

    return matching_emails