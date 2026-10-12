from analyzer import analyze_email


email = """
From: manager@company.com

Subject: Urgent: Project Update Required

Hi Divya,

Please send the project status report
before tomorrow at 10 AM.

Thanks,
Manager
"""


result = analyze_email(email)

print(result)