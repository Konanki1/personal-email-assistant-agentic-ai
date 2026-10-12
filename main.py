import logging

from graph import graph


logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

)


def print_query_result(result):

    print("\n" + "=" * 60)

    print("EMAIL ASSISTANT RESULT")

    print("=" * 60)

    if isinstance(result, list):

        if not result:

            print("\nNo matching emails found.")

        else:

            for index, item in enumerate(
                result,
                start=1
            ):

                print(f"\n{index}.")

                for key, value in item.items():

                    print(
                        f"   {key.replace('_', ' ').title()}: "
                        f"{value}"
                    )

    else:

        print(f"\n{result}")

    print("\n" + "=" * 60)


def main():

    logging.info(
        "Starting Personal Email Assistant"
    )

    initial_state = {

        "emails": [],

        "analyzed_emails": [],

        "recommended_actions": [],

        "approved_actions": [],

        "executed_actions": [],

        "report": "",

        "user_query": "",

        "query_result": None
    }


    # ==========================================
    # RUN MAIN EMAIL WORKFLOW
    # ==========================================

    result = graph.invoke(
        initial_state
    )

    logging.info(
        "Email analysis completed"
    )


    # ==========================================
    # EMAIL ASSISTANT SUMMARY
    # ==========================================

    emails = result.get(
        "emails",
        []
    )

    analyzed_emails = result.get(
        "analyzed_emails",
        []
    )

    recommended_actions = result.get(
        "recommended_actions",
        []
    )

    approved_actions = result.get(
        "approved_actions",
        []
    )

    executed_actions = result.get(
        "executed_actions",
        []
    )


    print("\n")

    print("=" * 60)

    print(
        "           EMAIL ASSISTANT SUMMARY"
    )

    print("=" * 60)

    print(
        f"\nTotal Emails: {len(emails)}"
    )

    print(
        f"Emails Analyzed: "
        f"{len(analyzed_emails)}"
    )

    print(
        f"Recommended Actions: "
        f"{len(recommended_actions)}"
    )

    print(
        f"Approved Actions: "
        f"{len(approved_actions)}"
    )

    print(
        f"Executed Actions: "
        f"{len(executed_actions)}"
    )
        # ==========================================
    # EMAIL CATEGORY COUNTS
    # ==========================================

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

        if not analysis:
            continue

        category = analysis.get(
            "category",
            "other"
        )

        if category not in category_counts:
            category = "other"

        category_counts[category] += 1


    print("\n" + "=" * 60)

    print(
        "             EMAIL CATEGORY SUMMARY"
    )

    print("=" * 60)

    print(
        f"\nJunk / Spam Emails: "
        f"{category_counts['spam']}"
    )

    print(
        f"Personal Emails: "
        f"{category_counts['personal']}"
    )

    print(
        f"Family Emails: "
        f"{category_counts['family']}"
    )

    print(
        f"Work Emails: "
        f"{category_counts['work']}"
    )

    print(
        f"Newsletter Emails: "
        f"{category_counts['newsletter']}"
    )

    print(
        f"Order Update Emails: "
        f"{category_counts['order_update']}"
    )

    print(
        f"Other Emails: "
        f"{category_counts['other']}"
    )

    # ==========================================
    # EXECUTED ACTIONS
    # ==========================================

    if executed_actions:

        print("\n" + "=" * 60)

        print(
            "             EXECUTED ACTIONS"
        )

        print("=" * 60)

        for index, action in enumerate(
            executed_actions,
            start=1
        ):

            print(
                f"\n{index}. Action Type: "
                f"{action.get('action_type')}"
            )

            print(
                f"   Subject: "
                f"{action.get('subject')}"
            )

            print(
                f"   Status: "
                f"{action.get('status')}"
            )

            print(
                f"   Result: "
                f"{action.get('message')}"
            )

    else:

        print(
            "\nNo actions were executed."
        )


    # ==========================================
    # EMAIL QUERY ASSISTANT
    # ==========================================

    print("\n" + "=" * 60)

    print(
        "        ASK ABOUT YOUR EMAILS"
    )

    print("=" * 60)

    print(
        "\nExamples:"
    )

    print(
        "- Show me urgent emails"
    )

    print(
        "- What deadlines do I have?"
    )

    print(
        "- Show emails requiring a reply"
    )

    print(
        "- What are my TODO items?"
    )

    print(
        "- Show my events"
    )

    print(
        "- Show important emails this week"
    )

    print(
        "- Search for project emails"
    )


    while True:

        user_query = input(
            "\nAsk a question "
            "(or type 'exit'): "
        ).strip()


        if user_query.lower() == "exit":

            print(
                "\nClosing Email Assistant..."
            )

            break


        if not user_query:

            print(
                "Please enter a question."
            )

            continue


        # ======================================
        # INVOKE ONLY QUERY NODE
        # ======================================

        from nodes import (
            handle_user_query_node
        )


        query_state = {

            "analyzed_emails":
                analyzed_emails,

            "user_query":
                user_query
        }


        query_response = (
            handle_user_query_node(
                query_state
            )
        )


        query_result = query_response.get(
            "query_result"
        )


        print_query_result(
            query_result
        )


    print("\n" + "=" * 60)

    print("      PERSONAL EMAIL ASSISTANT COMPLETED"
    )

    print("=" * 60 + "\n")


if __name__ == "__main__":

    main()