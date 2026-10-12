from typing import TypedDict, List, Dict, Any


class EmailAgentState(TypedDict):

    # Raw emails fetched from Mailpit
    emails: List[Dict[str, Any]]

    # Emails after AI analysis
    analyzed_emails: List[Dict[str, Any]]

    # Actions suggested by the assistant
    recommended_actions: List[Dict[str, Any]]

    # Actions approved by the user
    approved_actions: List[Dict[str, Any]]

    # Actions that were executed
    executed_actions: List[Dict[str, Any]]

    # Final generated email analysis report
    report: str

    # User query for local tools
    user_query: str

    # Result returned by the selected tool
    query_result: Any