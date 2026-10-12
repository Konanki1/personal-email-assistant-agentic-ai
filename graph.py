from langgraph.graph import StateGraph, START, END

from state import EmailAgentState

from nodes import (
    read_emails_node,
    analyze_emails_node,
    flag_time_sensitive_emails_node,
    build_recommended_actions_node,
    store_results_node,
    generate_report_node,
    approve_actions_node,
    execute_actions_node
)


# ==========================================
# CREATE WORKFLOW
# ==========================================

workflow = StateGraph(
    EmailAgentState
)


# ==========================================
# ADD NODES
# ==========================================

workflow.add_node(
    "read_emails",
    read_emails_node
)

workflow.add_node(
    "analyze_emails",
    analyze_emails_node
)

workflow.add_node(
    "flag_time_sensitive_emails",
    flag_time_sensitive_emails_node
)

workflow.add_node(
    "build_recommended_actions",
    build_recommended_actions_node
)

workflow.add_node(
    "store_results",
    store_results_node
)

workflow.add_node(
    "generate_report",
    generate_report_node
)

workflow.add_node(
    "approve_actions",
    approve_actions_node
)

workflow.add_node(
    "execute_actions",
    execute_actions_node
)


# ==========================================
# CONNECT NODES
# ==========================================

workflow.add_edge(
    START,
    "read_emails"
)

workflow.add_edge(
    "read_emails",
    "analyze_emails"
)

workflow.add_edge(
    "analyze_emails",
    "flag_time_sensitive_emails"
)

workflow.add_edge(
    "flag_time_sensitive_emails",
    "build_recommended_actions"
)

workflow.add_edge(
    "build_recommended_actions",
    "store_results"
)

workflow.add_edge(
    "store_results",
    "generate_report"
)

workflow.add_edge(
    "generate_report",
    "approve_actions"
)

workflow.add_edge(
    "approve_actions",
    "execute_actions"
)

workflow.add_edge(
    "execute_actions",
    END
)


# ==========================================
# COMPILE GRAPH
# ==========================================

graph = workflow.compile()