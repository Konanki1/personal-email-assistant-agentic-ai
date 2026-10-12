import logging
import time

from datetime import date, datetime, timedelta

from llm import llm
from schemas import EmailAnalysis


# ==========================================
# STRUCTURED LLM
# ==========================================

structured_llm = llm.with_structured_output(
    EmailAnalysis,
    method="json_schema",
    strict=False
)

# ==========================================
# HELPER: GET SENDER
# ==========================================

def _get_sender(email):
    sender_data = email.get("From", "")

    if isinstance(sender_data, dict):
        return (
            sender_data.get("Address")
            or sender_data.get("Email")
            or sender_data.get("Name")
            or ""
        )

    return str(sender_data)


# ==========================================
# HELPER: GET CONTENT
# ==========================================

def _get_content(email):
    """
    Get the best available email content.
    """

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


# ==========================================
# HELPER: NORMALIZE RESULT
# ==========================================

def _normalize_analysis(result):
    """
    Make sure the result returned by the LLM
    is safe for the rest of the application.
    """

    if result is None:
        return None

    # Pydantic model -> dictionary
    if hasattr(result, "model_dump"):
        data = result.model_dump()

    elif hasattr(result, "dict"):
        data = result.dict()

    elif isinstance(result, dict):
        data = result.copy()

    else:
        return None

    # ======================================
    # SAFE DEFAULTS
    # ======================================

    if data.get("summary") is None:
        data["summary"] = ""

    if data.get("category") is None:
        data["category"] = "other"

    if data.get("priority") is None:
        data["priority"] = "normal"

    if data.get("requires_reply") is None:
        data["requires_reply"] = False

    if data.get("is_event") is None:
        data["is_event"] = False

    if data.get("has_deadline") is None:
        data["has_deadline"] = False

    if data.get("time_sensitive") is None:
        data["time_sensitive"] = False

    if data.get("is_work_item") is None:
        data["is_work_item"] = False

    if data.get("is_for_today") is None:
        data["is_for_today"] = False

    if data.get("is_for_this_week") is None:
        data["is_for_this_week"] = False

    if data.get("todos") is None:
        data["todos"] = []

    if data.get("recommended_actions") is None:
        data["recommended_actions"] = []

    # ======================================
    # FIX WORK ITEM TYPE
    # ======================================

    allowed_work_types = {
        "reply",
        "report",
        "meeting",
        "follow_up",
        "task",
        "other",
    }

    work_item_type = data.get("work_item_type")

    if work_item_type == "status_report":
        data["work_item_type"] = "report"

    elif work_item_type not in allowed_work_types:
        if work_item_type is not None:
            data["work_item_type"] = "other"

    # ======================================
    # FIX TODOS
    # ======================================

    normalized_todos = []

    for todo in data.get("todos", []):

        # Correct format already
        if isinstance(todo, dict):

            task = todo.get("task")

            if not task:
                continue

            due_date = todo.get("due_date")

            work_type = todo.get(
                "work_type",
                "other"
            )

            if work_type == "status_report":
                work_type = "report"

            if work_type not in allowed_work_types:
                work_type = "other"

            normalized_todos.append({
                "task": str(task),
                "due_date": due_date,
                "work_type": work_type,
            })

        # LLM returned string instead of TodoItem
        elif isinstance(todo, str):

            task = todo.strip()

            if not task:
                continue

            work_type = "task"

            lower_task = task.lower()

            if "report" in lower_task:
                work_type = "report"

            elif "meeting" in lower_task:
                work_type = "meeting"

            elif "reply" in lower_task:
                work_type = "reply"

            normalized_todos.append({
                "task": task,
                "due_date": data.get("deadline"),
                "work_type": work_type,
            })

    data["todos"] = normalized_todos

    # ======================================
    # FIX RECOMMENDED ACTIONS
    # ======================================

    allowed_actions = {
        "reply",
        "send",
        "mark_as_spam",
        "delete",
        "deadline_reminder",
        "add_to_calendar",
    }

    normalized_actions = []

    for action in data.get(
        "recommended_actions",
        []
    ):

        # Correct dictionary format
        if isinstance(action, dict):

            action_type = action.get(
                "action_type"
            )

            if not action_type:
                continue

            if action_type not in allowed_actions:
                continue

            description = action.get(
                "description"
            )

            if description is None:
                description = ""

            normalized_actions.append({
                "action_type": action_type,
                "description": str(description),
            })

        # LLM returned just the action name
        elif isinstance(action, str):

            action_type = action.strip()

            if action_type not in allowed_actions:
                continue

            descriptions = {
                "reply":
                    "Reply to this email.",

                "send":
                    "Send the required information.",

                "mark_as_spam":
                    "Mark this email as spam.",

                "delete":
                    "Delete this email.",

                "deadline_reminder":
                    "Create a reminder for the detected deadline.",

                "add_to_calendar":
                    "Add the event to the calendar.",
            }

            normalized_actions.append({
                "action_type": action_type,
                "description":
                    descriptions.get(
                        action_type,
                        ""
                    ),
            })

    data["recommended_actions"] = (
        normalized_actions
    )

    # ======================================
    # EVENT DEFAULTS
    # ======================================

    if not data["is_event"]:

        data["event_title"] = None
        data["event_date"] = None
        data["event_time"] = None

    # ======================================
    # DEADLINE CONSISTENCY
    # ======================================

    if data.get("has_deadline"):

        data["time_sensitive"] = True

    # ======================================
    # REMOVE DUPLICATE ACTIONS
    # ======================================

    unique_actions = []
    seen_actions = set()

    for action in data.get(
        "recommended_actions",
        []
    ):

        action_type = action.get(
            "action_type"
        )

        if not action_type:
            continue

        if action_type in seen_actions:
            continue

        seen_actions.add(action_type)

        unique_actions.append(action)

    data["recommended_actions"] = (
        unique_actions
    )

    return data


# ==========================================
# LOCAL FALLBACK ANALYSIS
# ==========================================

def _fallback_analysis(email):
    """
    Local fallback used only when Groq cannot
    produce valid structured output.
    """

    subject = str(
        email.get("Subject", "")
    ).strip()

    content = _get_content(email)

    text = (
        subject + " " + content
    ).lower()

    today = date.today()

    # ======================================
    # DEFAULT VALUES
    # ======================================

    category = "other"
    priority = "normal"

    summary = (
        content[:200]
        if content
        else subject
    )

    requires_reply = False

    is_event = False
    has_deadline = False
    time_sensitive = False
    is_work_item = False

    event_title = None
    event_date = None
    event_time = None

    deadline = None

    todos = []
    recommended_actions = []

    work_item_type = None

    # ======================================
    # SPAM
    # ======================================

    spam_words = [
        "won $",
        "winner",
        "million",
        "lottery",
        "prize",
        "claim your",
        "congratulations",
    ]

    if any(
        word in text
        for word in spam_words
    ):

        category = "spam"
        priority = "low"

        recommended_actions.append({
            "action_type": "mark_as_spam",
            "description":
                "Mark this email as spam.",
        })

        return _build_fallback_result(
            category=category,
            priority=priority,
            summary="Spam email detected.",
            requires_reply=False,
            is_event=False,
            has_deadline=False,
            time_sensitive=False,
            is_work_item=False,
            event_title=None,
            event_date=None,
            event_time=None,
            deadline=None,
            todos=[],
            recommended_actions=
                recommended_actions,
            work_item_type=None,
        )

    # ======================================
    # NEWSLETTER
    # ======================================

    if (
        "newsletter" in text
        or "weekly technology" in text
        or "unsubscribe" in text
    ):

        category = "newsletter"
        priority = "low"

    # ======================================
    # ORDER
    # ======================================

    elif (
        "order" in text
        or "shipped" in text
        or "delivery" in text
    ):

        category = "order_update"
        priority = "normal"

    # ======================================
    # FAMILY
    # ======================================

    elif (
        "family" in text
        or "mom" in text
        or "dinner" in text
    ):

        category = "family"
        priority = "normal"

    # ======================================
    # WORK
    # ======================================

    elif (
        "project" in text
        or "client" in text
        or "manager" in text
        or "report" in text
        or "work" in text
    ):

        category = "work"

        if (
            "urgent" in text
            or "asap" in text
            or "immediately" in text
        ):
            priority = "urgent"

        else:
            priority = "normal"

    # ======================================
    # URGENT PRIORITY
    # ======================================

    if (
        "urgent" in text
        or "asap" in text
        or "immediately" in text
    ):

        priority = "urgent"

    # ======================================
    # REPLY REQUIRED
    # ======================================

    reply_words = [
        "please reply",
        "please respond",
        "let me know",
        "confirm",
        "can you join",
        "can you attend",
    ]

    if any(
        word in text
        for word in reply_words
    ):

        requires_reply = True

        recommended_actions.append({
            "action_type": "reply",
            "description":
                "Reply to this email.",
        })

    # ======================================
    # FAMILY DINNER EVENT
    # ======================================

    if "dinner" in text:

        is_event = True

        event_title = "Family Dinner"

        # Detect Sunday
        if "sunday" in text:

            days_until_sunday = (
                6 - today.weekday()
            ) % 7

            if days_until_sunday == 0:
                days_until_sunday = 7

            event_date = (
                today
                + timedelta(
                    days=days_until_sunday
                )
            ).isoformat()

        # Detect 7 PM
        if (
            "7 pm" in text
            or "7:00 pm" in text
        ):

            event_time = "7:00 PM"

        # Calendar action
        if event_date:

            recommended_actions.append({
                "action_type":
                    "add_to_calendar",

                "description":
                    "Add the family dinner to calendar.",
            })

    # ======================================
    # PROJECT DEADLINE
    # ======================================

    if (
        "deadline" in text
        or "before tomorrow" in text
        or "due tomorrow" in text
        or (
            "before" in text
            and "tomorrow" in text
        )
    ):

        has_deadline = True
        time_sensitive = True

        if "tomorrow" in text:

            tomorrow = (
                today
                + timedelta(days=1)
            )

            deadline = (
                f"{tomorrow.isoformat()}"
                "T10:00:00"
            )

            recommended_actions.append({
                "action_type":
                    "deadline_reminder",

                "description":
                    "Create a reminder for the detected deadline.",
            })

    # ======================================
    # WORK ITEM
    # ======================================

    work_words = [
        "send",
        "submit",
        "report",
        "complete",
        "prepare",
        "status report",
        "task",
    ]

    if any(
        word in text
        for word in work_words
    ):

        is_work_item = True

        if "report" in text:

            work_item_type = "report"

        else:

            work_item_type = "task"

        task_text = (
            "Complete the required work item"
        )

        if "status report" in text:

            task_text = (
                "Send project status report"
            )

        todos.append({
            "task": task_text,
            "due_date": deadline,
            "work_type":
                work_item_type,
        })

    # ======================================
    # BUILD RESULT
    # ======================================

    return _build_fallback_result(
        category=category,
        priority=priority,
        summary=summary,
        requires_reply=requires_reply,
        is_event=is_event,
        has_deadline=has_deadline,
        time_sensitive=time_sensitive,
        is_work_item=is_work_item,
        event_title=event_title,
        event_date=event_date,
        event_time=event_time,
        deadline=deadline,
        todos=todos,
        recommended_actions=
            recommended_actions,
        work_item_type=work_item_type,
    )


# ==========================================
# BUILD FALLBACK RESULT
# ==========================================

def _build_fallback_result(
    category,
    priority,
    summary,
    requires_reply,
    is_event,
    has_deadline,
    time_sensitive,
    is_work_item,
    event_title,
    event_date,
    event_time,
    deadline,
    todos,
    recommended_actions,
    work_item_type=None,
):

    """
    Build a dictionary compatible with
    EmailAnalysis.
    """

    today = date.today()

    is_for_today = False
    is_for_this_week = False

    # ======================================
    # EVENT DATE FLAGS
    # ======================================

    if event_date:

        try:

            parsed_event_date = datetime.fromisoformat(
                str(event_date)
            ).date()

            if parsed_event_date == today:

                is_for_today = True

            if (
                today
                <= parsed_event_date
                <= today + timedelta(days=6)
            ):

                is_for_this_week = True

        except Exception:
            pass

    # ======================================
    # DEADLINE DATE FLAGS
    # ======================================

    if deadline:

        try:

            deadline_date = datetime.fromisoformat(
                str(deadline).replace("Z", "")
            ).date()

            if deadline_date == today:

                is_for_today = True

            if (
                today
                <= deadline_date
                <= today + timedelta(days=6)
            ):

                is_for_this_week = True

        except Exception:
            pass

    return {

        "category": category,

        "priority": priority,

        "summary": summary or "",

        "requires_reply": requires_reply,

        "is_event": is_event,

        "event_title": event_title,

        "event_date": event_date,

        "event_time": event_time,

        "has_deadline": has_deadline,

        "deadline": deadline,

        "time_sensitive": time_sensitive,

        "is_work_item": is_work_item,

        "work_item_type":
            work_item_type,

        "is_for_today":
            is_for_today,

        "is_for_this_week":
            is_for_this_week,

        "todos": todos,

        "recommended_actions":
            recommended_actions,
    }


# ==========================================
# AI EMAIL ANALYSIS
# ==========================================

def analyze_email(email):

    subject = str(
        email.get("Subject", "")
    ).strip()

    sender = _get_sender(email)

    content = _get_content(email)

    today = date.today().isoformat()

    logging.info(
        "Starting AI analysis for: %s",
        subject,
    )

    # ======================================
    # STRICT STRUCTURED PROMPT
    # ======================================

    prompt = f"""
You are an email classification system.

Analyze exactly ONE email.

Today is:
{today}

Subject:
{subject}

Sender:
{sender}

Content:
{content}

Return ONLY the EmailAnalysis object.

IMPORTANT:
Follow the EmailAnalysis schema exactly.

Do NOT return explanations.

Do NOT return markdown.

Do NOT return JSON strings.

Do NOT invent fields.

==================================================
ALLOWED VALUES
==================================================

category:
- spam
- personal
- family
- work
- newsletter
- order_update
- other

priority:
- urgent
- high
- normal
- low

work_item_type:
- reply
- report
- meeting
- follow_up
- task
- other
- null

action_type:
- reply
- send
- mark_as_spam
- delete
- deadline_reminder
- add_to_calendar

==================================================
TODO FORMAT
==================================================

EVERY todo MUST be an OBJECT.

Correct:

{{
    "task": "Send project status report",
    "due_date": "2026-09-01T10:00:00",
    "work_type": "report"
}}

INCORRECT:

"todos": [
    "Send project status report"
]

NEVER return a string inside todos.

==================================================
RECOMMENDED ACTION FORMAT
==================================================

EVERY recommended action MUST be an OBJECT.

Correct:

{{
    "action_type": "deadline_reminder",
    "description": "Create a reminder for the detected deadline."
}}

INCORRECT:

"recommended_actions": [
    "deadline_reminder"
]

NEVER return strings inside recommended_actions.

==================================================
WORK ITEM TYPE
==================================================

If the email is about a status report,
use:

"work_item_type": "report"

NEVER use:

"status_report"

==================================================
EVENT RULES
==================================================

If there is no event:

event_title = null
event_date = null
event_time = null
is_event = false

Only mark is_event=true when the email clearly describes
an actual event.

For relative dates such as "Sunday", calculate the date
using today's date.

Do not invent dates.

==================================================
DEADLINE RULES
==================================================

If there is no deadline:

has_deadline = false
deadline = null

If there is a real deadline:

has_deadline = true
time_sensitive = true

For "tomorrow at 10 AM", calculate the actual date
using today's date.

==================================================
TODO RULES
==================================================

Only create a todo when the email requires a task or work item.

For a project status report request, return:

"todos": [
    {{
        "task": "Send project status report",
        "due_date": "YYYY-MM-DDT10:00:00",
        "work_type": "report"
    }}
]

==================================================
ACTION RULES
==================================================

Spam:
recommend mark_as_spam.

Required reply:
recommend reply.

Clear event:
recommend add_to_calendar.

Real deadline:
recommend deadline_reminder.

Normal informational emails:
usually no action.

Do not create duplicate actions.

==================================================
FINAL REQUIREMENT
==================================================

Every field must match the EmailAnalysis schema.

Especially:

todos = array of TodoItem objects.

recommended_actions = array of RecommendedAction objects.

work_item_type must be one of:
reply, report, meeting, follow_up, task, other, null.

Return only the structured EmailAnalysis result.
"""

    # ======================================
    # TRY GROQ
    # ======================================

    max_attempts = 1

    for attempt in range(
        1,
        max_attempts + 1,
    ):

        try:

            logging.info(
                "Groq analysis attempt %d/%d for '%s'",
                attempt,
                max_attempts,
                subject,
            )

            result = structured_llm.invoke(
                prompt
            )

            normalized = _normalize_analysis(
                result
            )

            if normalized is None:

                raise ValueError(
                    "Groq returned an empty or invalid structured result."
                )

            logging.info(
                "Email analysis successful for '%s'",
                subject,
            )

            # ==================================
            # RETURN PYDANTIC OBJECT
            # ==================================

            try:

                return EmailAnalysis(
                    **normalized
                )

            except Exception as validation_error:

                logging.warning(
                    "Normalized result failed EmailAnalysis validation: %s",
                    validation_error,
                )

                # Try fallback if schema validation
                # still fails
                raise validation_error

        except Exception as e:

            logging.warning(
                "Groq analysis attempt %d failed for '%s': %s",
                attempt,
                subject,
                str(e),
            )

            if attempt < max_attempts:

                time.sleep(2)

            else:

                logging.warning(
                    "Using local fallback analysis for '%s'",
                    subject,
                )

                fallback = _fallback_analysis(
                    email
                )

                logging.info(
                    "Fallback analysis completed for '%s'",
                    subject,
                )

                try:

                    return EmailAnalysis(
                        **fallback
                    )

                except Exception as fallback_error:

                    logging.error(
                        "Fallback EmailAnalysis validation failed: %s",
                        fallback_error,
                    )

                    return fallback