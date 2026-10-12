from typing import Optional, List, Literal

from pydantic import BaseModel, Field


# ==========================================
# TODO / WORK ITEM
# ==========================================

class TodoItem(BaseModel):

    task: str

    due_date: Optional[str] = None

    work_type: Literal[
        "reply",
        "report",
        "meeting",
        "follow_up",
        "task",
        "other"
    ] = "other"


# ==========================================
# RECOMMENDED ACTION
# ==========================================

class RecommendedAction(BaseModel):

    action_type: Literal[
        "reply",
        "send",
        "mark_as_spam",
        "delete",
        "deadline_reminder",
        "add_to_calendar"
    ]

    description: str


# ==========================================
# EMAIL ANALYSIS
# ==========================================

class EmailAnalysis(BaseModel):

    # ======================================
    # EMAIL CLASSIFICATION
    # ======================================

    category: str = "other"


    # ======================================
    # PRIORITY ANALYSIS
    # ======================================

    priority: Literal[
        "urgent",
        "high",
        "normal",
        "low"
    ] = "normal"


    # ======================================
    # EMAIL SUMMARY
    # ======================================

    summary: str = ""


    # ======================================
    # REPLY DETECTION
    # ======================================

    requires_reply: bool = False


    # ======================================
    # EVENT / CALENDAR DETECTION
    # ======================================

    is_event: bool = False

    event_title: Optional[str] = None

    event_date: Optional[str] = None

    event_time: Optional[str] = None


    # ======================================
    # TIME / DATE / DEADLINE DETECTION
    # ======================================

    has_deadline: bool = False

    deadline: Optional[str] = None

    time_sensitive: bool = False


    # ======================================
    # WORK ITEM CLASSIFICATION
    # ======================================

    is_work_item: bool = False

    work_item_type: Optional[
        Literal[
            "reply",
            "report",
            "meeting",
            "follow_up",
            "task",
            "other"
        ]
    ] = None


    # ======================================
    # TODAY / THIS WEEK FLAGGING
    # ======================================

    is_for_today: bool = False

    is_for_this_week: bool = False


    # ======================================
    # TODOS
    # ======================================

    todos: List[TodoItem] = Field(
        default_factory=list
    )


    # ======================================
    # RECOMMENDED ACTIONS
    # ======================================

    recommended_actions: List[RecommendedAction] = Field(
        default_factory=list
    )