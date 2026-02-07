import requests
import json
import os

def send_discord():
    webhook_url = os.getenv('DISCORD_WEBHOOK')
    role_id = os.getenv('MAIN_ROLE_ID')
    repo = os.getenv('GITHUB_REPOSITORY')
    branch = os.getenv('GITHUB_REF_NAME')
    run_id = os.getenv('GITHUB_RUN_ID')
    event = os.getenv('EVENT_NAME')
    tag = os.getenv('RELEASE_TAG')
    sha = os.getenv('COMMIT_SHA', '0000000')[:7]
    msg = os.getenv('COMMIT_MSG', 'Main Update').split('\n')[0]
    zip_status = os.getenv('ZIP_STATUS', 'unknown').lower()

    if not webhook_url or not webhook_url.startswith("https://"):
        print("❌ Webhook URL missing or invalid (must be HTTPS)")
        return

    # Identify specific context for Production
    context = f"🚀 **Release** `{tag}`" if event == 'release' else f"🛠️ **Main Branch**"
    log_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    
    # Status-based styling
    if zip_status == 'success':
        icon = "✅"
        status_text = "PASSED"
        color = 3066993  # Green
    elif zip_status == 'skipped':
        icon = "⏭️"
        status_text = "SKIPPED"
        color = 10070709  # Gray
    elif zip_status == 'failure':
        icon = "❌"
        status_text = "FAILED"
        color = 15158332  # Red
    
    header = f"{icon} **Main Release Notification - {status_text}**\nContext: {context}"

    # Combine all text into the card description
    full_description = f"{header}\n\n`{sha}` {msg}\n\n[Open Workflow Details]({log_url})\n\n@everyone"

    payload = {
        "embeds": [{
            "title": "Main Release Pipeline",
            "description": full_description,
            "color": color
        }]
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=10
        )
        response.raise_for_status()
        print(f"Notification Sent: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_discord()
