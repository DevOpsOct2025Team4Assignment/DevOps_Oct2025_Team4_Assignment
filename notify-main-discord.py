import urllib.request
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

    if not webhook_url or not webhook_url.startswith("https://"):
        print("❌ Webhook URL missing or invalid (must be HTTPS)")
        return

    # Identify specific context for Production
    context = f"🚀 **Release** `{tag}`" if event == 'release' else f"🛠️ **Main Branch**"
    log_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    
    header = f"✅ **Main Release Notification**\nContext: {context}"
    footer = f"View logs <@&{role_id}>"
    color = 3066993 # Green

    # Combine all text into the card description
    full_description = f"{header}\n\n`{sha}` {msg}\n\n{footer}\n\n[Open Workflow Details]({log_url})"

    payload = {
        "embeds": [{
            "title": "Main Release Pipeline",
            "description": full_description,
            "color": color
        }]
    }

    req = urllib.request.Request(
        webhook_url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Notification Sent: {resp.status}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_discord()
