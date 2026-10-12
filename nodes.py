import logging

from datetime import datetime, date, timedelta

from email_client import get_emails,mark_email_processed
from analyzer import analyze_email
from storage import save_analysis
from action_executor import execute_action


# ==========================================
# READ EMAILS
# ==========================================

def read_emails_node(state):

    logging.info("LANGGRAPH NODE: Reading emails")

    emails = get_emails()

    logging.info(
        "Total emails fetched: %d",
        len(emails)
    )

    return {
        "emails": emails
    }


# ==========================================
# ANALYZE EMAILS
# ==========================================

# ==========================================
# ANALYZE EMAILS
# ==========================================

def analyze_emails_node(state):

    logging.info(
        "LANGGRAPH NODE: Analyzing emails"
    )

    analyzed_emails = []

    for index, email in enumerate(
        state.get("emails", []),
        start=1
    ):

        try:

            logging.info(
                "Analyzing email %d",
                index
            )

            analysis = analyze_email(email)

            logging.info(
                "Email %d priority: %s",
                index,
                analysis.priority
            )

            if analysis.has_deadline:

                logging.info(
                    "Deadline detected: %s",
                    analysis.deadline
                )

            if analysis.is_work_item:

                logging.info(
                    "Work item detected: %s",
                    analysis.work_item_type
                )

            analyzed_emails.append({

                "email": email,

                "analysis":
                    analysis.model_dump()

            })

            # ==================================
            # MARK EMAIL AS PROCESSED
            # ==================================

            email_id = email.get("ID")

            if email_id:

                mark_email_processed(
                    email_id
                )

            logging.info(
                "Email %d analyzed successfully",
                index
            )

        except Exception as e:

            logging.error(
                "Failed to analyze email %d: %s",
                index,
                e
            )

            analyzed_emails.append({

                "email": email,

                "analysis": None,

                "error": str(e)

            })
    return {

        "analyzed_emails":
            analyzed_emails

    }
def flag_time_sensitive_emails_node(state):

    logging.info(
        "LANGGRAPH NODE: Flagging emails for today and this week"
    )

    today = date.today()

    start_of_week = today - timedelta(
        days=today.weekday()
    )

    end_of_week = start_of_week + timedelta(
        days=6
    )

    analyzed_emails = state.get(
        "analyzed_emails",
        []
    )

    for item in analyzed_emails:

        analysis = item.get("analysis")

        if analysis is None:
            continue

        analysis["is_for_today"] = False
        analysis["is_for_this_week"] = False

        # ======================================
        # CHECK DEADLINE
        # ======================================

        deadline = analysis.get("deadline")

        if deadline:

            try:

                deadline_date = datetime.fromisoformat(
                    deadline
                ).date()

                if deadline_date == today:

                    analysis["is_for_today"] = True

                if (
                    start_of_week
                    <= deadline_date
                    <= end_of_week
                ):

                    analysis["is_for_this_week"] = True

            except (
                ValueError,
                TypeError
            ):

                logging.warning(
                    "Invalid deadline date: %s",
                    deadline
                )

        # ======================================
        # CHECK EVENT DATE
        # ======================================

        event_date = analysis.get(
            "event_date"
        )

        if event_date:

            try:

                parsed_event_date = datetime.fromisoformat(
                    event_date
                ).date()

                if parsed_event_date == today:

                    analysis["is_for_today"] = True

                if (
                    start_of_week
                    <= parsed_event_date
                    <= end_of_week
                ):

                    analysis["is_for_this_week"] = True

            except (
                ValueError,
                TypeError
            ):

                logging.warning(
                    "Invalid event date: %s",
                    event_date
                )

        # ======================================
        # LOG FLAGS
        # ======================================

        subject = item.get(
            "email",
            {}
        ).get(
            "Subject",
            "Unknown Subject"
        )

        if analysis["is_for_today"]:

            logging.info(
                "FLAGGED FOR TODAY: %s",
                subject
            )

        if analysis["is_for_this_week"]:

            logging.info(
                "FLAGGED FOR THIS WEEK: %s",
                subject
            )

    return {
        "analyzed_emails":
            analyzed_emails
    }


# ==========================================
# BUILD RECOMMENDED ACTIONS
# ==========================================

# ==========================================
# BUILD RECOMMENDED ACTIONS
# ==========================================

def build_recommended_actions_node(state):
    logging.info("LANGGRAPH NODE: Building recommended actions")

    recommended_actions = []

    for item in state.get("analyzed_emails", []):

        email = item.get("email", {})
        analysis = item.get("analysis")

        if analysis is None:
            logging.warning(
                "Skipping email because analysis failed: %s",
                email.get("Subject")
            )
            continue

        actions = analysis.get("recommended_actions", [])

        # Avoid duplicate action types
        added = set()

        for action in actions:

            action_type = action.get("action_type")

            # ----------------------------------
            # Skip invalid SEND actions
            # ----------------------------------
            if action_type == "send":
                continue

            # ----------------------------------
            # Calendar requires a valid date
            # ----------------------------------
            if (
                action_type == "add_to_calendar"
                and not analysis.get("event_date")
            ):
                continue

            if action_type in added:
                continue

            added.add(action_type)

            action_data = {
                "email_id": email.get("ID"),
                "subject": email.get("Subject"),
                "action_type": action_type,
                "description": action.get("description"),
                "email": email
            }

            if action_type == "deadline_reminder":
                action_data["deadline"] = analysis.get("deadline")

            if action_type == "add_to_calendar":
                action_data["event_title"] = analysis.get("event_title")
                action_data["event_date"] = analysis.get("event_date")
                action_data["event_time"] = analysis.get("event_time")

            recommended_actions.append(action_data)

        # ----------------------------------
        # Fallback reply
        # ----------------------------------
        if (
            analysis.get("requires_reply")
            and "reply" not in added
        ):
            recommended_actions.append({
                "email_id": email.get("ID"),
                "subject": email.get("Subject"),
                "action_type": "reply",
                "description": "Reply required",
                "email": email
            })

        # ----------------------------------
        # Fallback deadline reminder
        # ----------------------------------
        if (
            analysis.get("has_deadline")
            and "deadline_reminder" not in added
        ):
            recommended_actions.append({
                "email_id": email.get("ID"),
                "subject": email.get("Subject"),
                "action_type": "deadline_reminder",
                "description": "Create reminder for deadline",
                "deadline": analysis.get("deadline"),
                "email": email
            })

        # ----------------------------------
        # Fallback calendar
        # ----------------------------------
        if (
            analysis.get("is_event")
            and analysis.get("event_date")
            and "add_to_calendar" not in added
        ):
            recommended_actions.append({
                "email_id": email.get("ID"),
                "subject": email.get("Subject"),
                "action_type": "add_to_calendar",
                "description": "Add event to calendar",
                "event_title": analysis.get("event_title"),
                "event_date": analysis.get("event_date"),
                "event_time": analysis.get("event_time"),
                "email": email
            })

    logging.info(
        "Total recommended actions: %d",
        len(recommended_actions)
    )

    return {
        "recommended_actions": recommended_actions
    }

# ==========================================
# GENERATE EMAIL REPORT
# ==========================================
# ==========================================
# STORE RESULTS
# ==========================================

def store_results_node(state):
    logging.info("LANGGRAPH NODE: Storing results")

    data_to_save = {
        "analyzed_emails": state.get(
            "analyzed_emails",
            []
        ),
        "recommended_actions": state.get(
            "recommended_actions",
            []
        )
    }

    save_analysis(data_to_save)

    logging.info("Analysis saved successfully")

    return {}

def generate_report_node(state):

    logging.info(
        "LANGGRAPH NODE: Generating report"
    )

    emails = state.get(
        "emails",
        []
    )

    analyzed_emails = state.get(
        "analyzed_emails",
        []
    )

    recommended_actions = state.get(
        "recommended_actions",
        []
    )

    report = "\n"

    report += "=" * 60
    report += "\nEMAIL ANALYSIS REPORT\n"
    report += "=" * 60

    # ======================================
    # TOTALS
    # ======================================

    report += (
        f"\n\nTotal Emails: {len(emails)}"
    )

    report += (
        f"\nEmails Analyzed: "
        f"{len(analyzed_emails)}"
    )
        # ======================================
    # CATEGORY COUNTS
    # ======================================

    category_counts = {
        "spam": 0,
        "personal": 0,
        "family": 0,
        "work": 0,
        "newsletter": 0,
        "order_update": 0,
        "other": 0
    }

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        category = analysis.get(
            "category",
            "other"
        )

        if category not in category_counts:

            category = "other"

        category_counts[category] += 1


    # ======================================
    # CATEGORY SUMMARY
    # ======================================

    report += "\n\n" + "=" * 60
    report += "\nEMAIL CATEGORY SUMMARY"
    report += "\n" + "=" * 60

    report += (
        f"\n\nJunk / Spam Emails: "
        f"{category_counts['spam']}"
    )

    report += (
        f"\nPersonal Emails: "
        f"{category_counts['personal']}"
    )

    report += (
        f"\nFamily Emails: "
        f"{category_counts['family']}"
    )

    report += (
        f"\nWork Emails: "
        f"{category_counts['work']}"
    )

    report += (
        f"\nNewsletter Emails: "
        f"{category_counts['newsletter']}"
    )

    report += (
        f"\nOrder Update Emails: "
        f"{category_counts['order_update']}"
    )

    report += (
        f"\nOther Emails: "
        f"{category_counts['other']}"
    )

    report += (
        f"\nRecommended Actions: "
        f"{len(recommended_actions)}"
    )

    # ======================================
    # TODAY / THIS WEEK
    # ======================================

    today_emails = []
    week_emails = []

    for item in analyzed_emails:

        analysis = item.get(
            "analysis"
        )

        if analysis is None:
            continue

        subject = item.get(
            "email",
            {}
        ).get(
            "Subject",
            "Unknown Subject"
        )

        if analysis.get(
            "is_for_today"
        ):

            today_emails.append(
                subject
            )

        if analysis.get(
            "is_for_this_week"
        ):

            week_emails.append(
                subject
            )

    report += "\n\n" + "=" * 60
    report += "\nIMPORTANT EMAILS FOR TODAY\n"
    report += "=" * 60

    if today_emails:

        for subject in today_emails:

            report += (
                f"\n- {subject}"
            )

    else:

        report += (
            "\nNo important emails for today."
        )

    report += "\n\n" + "=" * 60
    report += "\nIMPORTANT EMAILS FOR THIS WEEK\n"
    report += "=" * 60

    if week_emails:

        for subject in week_emails:

            report += (
                f"\n- {subject}"
            )

    else:

        report += (
            "\nNo important emails for this week."
        )

    # ======================================
    # EMAIL SUMMARY
    # ======================================

    report += "\n\n" + "=" * 60
    report += "\nEMAIL SUMMARY\n"
    report += "=" * 60

    for index, item in enumerate(
        analyzed_emails,
        start=1
    ):

        email = item.get(
            "email",
            {}
        )

        analysis = item.get(
            "analysis"
        )

        report += (
            f"\n\n{index}. Subject: "
            f"{email.get('Subject')}"
        )

        if analysis is None:

            report += (
                "\n   Analysis: Failed"
            )

            continue

        report += (
            f"\n   Category: "
            f"{analysis.get('category')}"
        )

        report += (
            f"\n   Priority: "
            f"{analysis.get('priority')}"
        )

        report += (
            f"\n   Summary: "
            f"{analysis.get('summary')}"
        )

        if analysis.get(
            "requires_reply"
        ):

            report += (
                "\n   Reply Required: Yes"
            )

        if analysis.get(
            "has_deadline"
        ):

            report += (
                f"\n   Deadline: "
                f"{analysis.get('deadline')}"
            )

        if analysis.get(
            "is_event"
        ):

            report += (
                f"\n   Event: "
                f"{analysis.get('event_title')}"
            )

            report += (
                f"\n   Event Date: "
                f"{analysis.get('event_date')}"
            )

            report += (
                f"\n   Event Time: "
                f"{analysis.get('event_time')}"
            )

        todos = analysis.get(
            "todos",
            []
        )

        if todos:

            report += "\n   Todos:"

            for todo in todos:

                report += (
                    f"\n      - "
                    f"{todo.get('task')}"
                )

    # ======================================
    # RECOMMENDED ACTIONS
    # ======================================

    report += "\n\n" + "=" * 60
    report += "\nRECOMMENDED ACTIONS\n"
    report += "=" * 60

    if not recommended_actions:

        report += (
            "\n\nNo actions recommended."
        )

    else:

        for index, action in enumerate(
            recommended_actions,
            start=1
        ):

            report += (
                f"\n\n{index}. Subject: "
                f"{action.get('subject')}"
            )

            report += (
                f"\n   Action: "
                f"{action.get('action_type')}"
            )

            report += (
                f"\n   Description: "
                f"{action.get('description')}"
            )

    report += "\n\n" + "=" * 60

    print(report)

    logging.info(
        "Email analysis report generated"
    )

    return {
        "report": report
    }


# ==========================================
# APPROVE ACTIONS
# ==========================================

def approve_actions_node(state):

    logging.info(
        "LANGGRAPH NODE: Approving recommended actions"
    )

    approved_actions = []

    actions = state.get(
        "recommended_actions",
        []
    )

    if not actions:

        logging.info(
            "No recommended actions to approve"
        )

        return {
            "approved_actions": []
        }

    for index, action in enumerate(
        actions,
        start=1
    ):

        print("\n" + "=" * 50)

        print(
            f"Action {index}"
        )

        print(
            f"Subject: "
            f"{action.get('subject')}"
        )

        print(
            f"Action Type: "
            f"{action.get('action_type')}"
        )

        print(
            f"Description: "
            f"{action.get('description')}"
        )

        choice = input(
            "\nApprove this action? (yes/no): "
        ).strip().lower()

        if choice in [
            "yes",
            "y"
        ]:

            approved_actions.append(
                action
            )

            logging.info(
                "Action %d approved",
                index
            )

        else:

            logging.info(
                "Action %d rejected",
                index
            )

    logging.info(
        "Total approved actions: %d",
        len(approved_actions)
    )

    return {
        "approved_actions":
            approved_actions
    }


# ==========================================
# EXECUTE APPROVED ACTIONS
# ==========================================

def execute_actions_node(state):

    logging.info(
        "LANGGRAPH NODE: Executing approved actions"
    )

    executed_actions = []

    for action in state.get(
        "approved_actions",
        []
    ):

        original_email = None

        # ======================================
        # FIND ORIGINAL EMAIL
        # ======================================

        for item in state.get(
            "analyzed_emails",
            []
        ):

            email = item.get(
                "email",
                {}
            )

            if (
                email.get("ID")
                == action.get("email_id")
            ):

                original_email = email
                break

        # ======================================
        # EMAIL NOT FOUND
        # ======================================

        if original_email is None:

            logging.error(
                "Original email not found for action: %s",
                action.get("action_type")
            )

            executed_actions.append({

                **action,

                "status":
                    "failed",

                "message":
                    "Original email not found"

            })

            continue

        # ======================================
        # PREPARE ACTION
        # ======================================

        action_to_execute = {

            **action,

            "email":
                original_email

        }

        # ======================================
        # EXECUTE
        # ======================================

        try:

            result = execute_action(
                action_to_execute
            )

        except Exception as e:

            logging.error(
                "Failed to execute action %s: %s",
                action.get("action_type"),
                str(e)
            )

            result = {

                "status":
                    "failed",

                "message":
                    str(e)

            }

        executed_actions.append({

            **action_to_execute,

            **result

        })

    logging.info(
        "Total executed actions: %d",
        len(executed_actions)
    )

    return {

        "executed_actions":
            executed_actions

    }


# ==========================================
# HANDLE USER QUERY USING LOCAL TOOLS
# ==========================================

def handle_user_query_node(state):

    logging.info(
        "LANGGRAPH NODE: Handling user query"
    )

    from tools import (

        get_urgent_emails,

        get_reply_required_emails,

        get_deadline_emails,

        get_today_emails,

        get_week_emails,

        get_all_todos,

        get_all_events,

        get_emails_by_category,

        search_email_by_subject

    )

    user_query = state.get(
        "user_query",
        ""
    ).strip().lower()

    analyzed_emails = state.get(
        "analyzed_emails",
        []
    )

    # ======================================
    # EMPTY QUERY
    # ======================================

    if not user_query:

        return {

            "query_result":
                "Please enter a valid question."

        }

    # ======================================
    # URGENT EMAILS
    # ======================================

    if "urgent" in user_query:

        result = get_urgent_emails(
            analyzed_emails
        )

        return {
            "query_result": result
        }

    # ======================================
    # REPLY REQUIRED
    # ======================================

    if (
        "reply" in user_query
        or "respond" in user_query
    ):

        result = get_reply_required_emails(
            analyzed_emails
        )

        return {
            "query_result": result
        }

    # ======================================
    # DEADLINES
    # ======================================

    if (
        "deadline" in user_query
        or "deadlines" in user_query
        or "due" in user_query
    ):

        result = get_deadline_emails(
            analyzed_emails
        )

        return {
            "query_result": result
        }

    # ======================================
    # TODO ITEMS
    # ======================================

    if (
        "todo" in user_query
        or "task" in user_query
        or "tasks" in user_query
    ):

        result = get_all_todos(
            analyzed_emails
        )

        return {
            "query_result": result
        }

    # ======================================
    # MEETINGS / EVENTS / CALENDAR
    #
    # IMPORTANT:
    # This block comes BEFORE "THIS WEEK"
    # so:
    #
    # "What meetings do I have this week?"
    #
    # will not accidentally call get_week_emails()
    # ======================================

    if (
        "meeting" in user_query
        or "meetings" in user_query
        or "event" in user_query
        or "events" in user_query
        or "calendar" in user_query
        or "appointment" in user_query
        or "appointments" in user_query
    ):

        result = get_all_events(
            analyzed_emails
        )

        return {
            "query_result": result
        }

    # ======================================
    # TODAY
    # ======================================

    if "today" in user_query:

        result = get_today_emails(
            analyzed_emails
        )

        return {
            "query_result": result
        }

    # ======================================
    # THIS WEEK
    # ======================================

    if (
        "week" in user_query
        or "weekly" in user_query
    ):

        result = get_week_emails(
            analyzed_emails
        )

        return {
            "query_result": result
        }

    # ======================================
    # CATEGORY SEARCH
    # ======================================

    categories = [

        "spam",

        "newsletter",

        "family",

        "personal",

        "order",

        "order_update",

        "work",

        "other"

    ]

    for category in categories:

        if category in user_query:

            result = get_emails_by_category(

                analyzed_emails,

                category

            )

            return {

                "query_result":
                    result

            }

    # ======================================
    # SUBJECT SEARCH
    # ======================================

    search_keywords = [

        "project",

        "family",

        "order",

        "newsletter",

        "technology",

        "dinner"

    ]

    for keyword in search_keywords:

        if keyword in user_query:

            result = search_email_by_subject(

                analyzed_emails,

                keyword

            )

            return {

                "query_result":
                    result

            }

    # ======================================
    # DEFAULT
    # ======================================

    return {

        "query_result":

            "Sorry, I could not understand the query. "

            "Try asking about urgent emails, deadlines, "

            "replies, todos, meetings, events, today, "

            "this week, categories, or a subject."

    }
