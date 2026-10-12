from typing import Optional, List, Literal
from pydantic import BaseModel, Field


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


class EmailAnalysis(BaseModel):
    category: Literal[
        "spam",
        "personal",
        "family",
        "work",
        "newsletter",
        "order_update",
        "other"
    ] = "other"

    priority: Literal[
        "urgent",
        "high",
        "normal",
        "low"
    ] = "normal"

    summary: str = ""
    requires_reply: bool = False

    is_event: bool = False
    event_title: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None

    has_deadline: bool = False
    deadline: Optional[str] = None
    time_sensitive: bool = False

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

    is_for_today: bool = False
    is_for_this_week: bool = False

    todos: List[TodoItem] = Field(
        default_factory=list
    )

    recommended_actions: List[RecommendedAction] = Field(
        default_factory=list
    )