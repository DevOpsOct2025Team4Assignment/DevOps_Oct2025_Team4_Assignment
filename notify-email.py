import smtplib
import os
from email.message import EmailMessage

user = os.getenv('EMAIL_USER')
password = os.getenv('EMAIL_PASS')
recipient = os.getenv('EMAIL_TO')
status = os.getenv('CI_RESULT')
repo = os.getenv('GITHUB_REPOSITORY')
run_id = os.getenv('GITHUB_RUN_ID')
branch = os.getenv('GITHUB_REF_NAME')
sha = os.getenv('COMMIT_SHA', '0000000')[:7]
commit_msg = os.getenv('COMMIT_MSG', 'No message').split('\n')[0]

if not all([user, password, recipient]):
    print("❌ Error: Missing secrets.")
    exit(1)

# Status-based styling
if status == "success":
    icon = "✅"
    status_text = "PASSED"
else:
    icon = "❌"
    status_text = "FAILED"

# Email subject
msg = EmailMessage()
msg['Subject'] = f"{icon} CI {status_text} - {branch}"
msg['From'] = user
msg['To'] = recipient

# Structured email body similar to Discord messages
body = (
    f"CI Pipeline Result: {status_text}\n"
    f"Repository: {repo}\n"
    f"Branch: {branch}\n\n"
    f"Commit: {sha}\n"
    f"Message: {commit_msg}\n\n"
    f"View Logs: https://github.com/{repo}/actions/runs/{run_id}"
)
msg.set_content(body)

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
    print("✅ Email notification sent.")
except Exception as e:
    print(f"❌ Error: {e}")
