import requests
import json
import os

def send_discord():
    webhook_url = os.getenv('DISCORD_WEBHOOK')
    status = os.getenv('CI_RESULT')
    role_id = os.getenv('DEV_ROLE_ID')
    repo = os.getenv('GITHUB_REPOSITORY')
    branch = os.getenv('GITHUB_REF_NAME')
    run_id = os.getenv('GITHUB_RUN_ID')
    sha = os.getenv('COMMIT_SHA', '0000000')[:7]
    msg = os.getenv('COMMIT_MSG', 'Manual Update').split('\n')[0]

    if not webhook_url or not webhook_url.startswith("https://"):
        print("❌ Error: Webhook secret is missing or invalid (must be HTTPS).")
        return

    # Logic for Pass/Fail styling
    if status == 'success':
        header = f"✅ **Tests passed in** `{branch}`"
        footer = ""
        color = 3066993 # Green
    else:
        header = f"🚨 **Tests failed in** `{branch}`"
        footer = f"<@&{role_id}>"
        color = 15158332 # Red

    # All content inside the description field of the embed
    full_description = f"{header}\n\n`{sha}` {msg}\n\n{footer}\n\n[View Details on GitHub](https://github.com/{repo}/actions/runs/{run_id})"

    payload = {
        "embeds": [{
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
        print(f"Notification Sent! Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send: {e}")

if __name__ == "__main__":
    send_discord()
