import urllib.request, json, os
import xml.etree.ElementTree as ET

def parse_test_failures(test_results_file):
    """Parse JUnit XML and return list of failed tests."""
    failures = []
    try:
        if not os.path.exists(test_results_file):
            return failures
        
        tree = ET.parse(test_results_file)
        root = tree.getroot()
        
        for testcase in root.findall('.//testcase'):
            failure = testcase.find('failure')
            if failure is not None:
                test_name = testcase.get('name')
                failure_msg = failure.get('message', 'Unknown error')
                failures.append((test_name, failure_msg))
    except Exception as e:
        print(f"Warning: Could not parse test results file: {e}")
    
    return failures

def send():
    webhook = os.getenv('DISCORD_WEBHOOK')
    if not webhook or not webhook.startswith("http"):
        print("❌ Error: DISCORD_WEBHOOK is missing or invalid.")
        return
    
    sca_status = os.getenv('SCA_STATUS')
    sast_status = os.getenv('SAST_STATUS')
    qa_status = os.getenv('QA_STATUS')
    test_results_file = os.getenv('TEST_RESULTS_FILE', 'test-results.xml')
    
    # Check if all tests passed
    failed_parts = []
    test_results = []
    
    if sca_status == 'success':
        test_results.append("✅ SCA (Trivy): Passed")
    else:
        test_results.append("❌ SCA (Trivy): Failed")
        failed_parts.append("SCA")
    
    if sast_status == 'success':
        test_results.append("✅ SAST (Bandit): Passed")
    else:
        test_results.append("❌ SAST (Bandit): Failed")
        failed_parts.append("SAST")
    
    if qa_status == 'success':
        test_results.append("✅ QA Tests: Passed")
    else:
        test_results.append("❌ QA Tests: Failed")
        failed_parts.append("QA Tests")
    
    run_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}"
    
    if not failed_parts:
        # All tests passed - show simple message
        color = 3066993  # Green
        title = "✅ CI Check Passed"
        desc = "All scans passed."
        content = ""
    else:
        # Some tests failed - show individual results
        color = 15158332  # Red
        title = "❌ CI Check Failed"
        desc = f"Issues in: {', '.join(failed_parts)}\n\n" + "\n".join(test_results)
        
        # Add individual test failures if QA tests failed
        if "QA Tests" in failed_parts:
            failures = parse_test_failures(test_results_file)
            if failures:
                desc += "\n\n**Failed Tests:**"
                for test_name, failure_msg in failures[:5]:  # Limit to 5 failures to avoid message size limit
                    desc += f"\n• `{test_name}`"
                if len(failures) > 5:
                    desc += f"\n• ... and {len(failures) - 5} more"
        
        content = f"<@&{os.getenv('ROLE_ID')}>"
    
    payload = {
        "content": content, 
        "embeds": [{
            "title": title, 
            "description": desc, 
            "color": color, 
            "fields": [
                {"name": "Branch", "value": os.getenv('GITHUB_REF_NAME'), "inline": True}, 
                {"name": "Results", "value": f"[View Log]({run_url})", "inline": True}
            ]
        }]
    }
    
    # Creating request with User-Agent header to avoid 403 Forbidden
    req = urllib.request.Request(
        webhook, 
        data=json.dumps(payload).encode(), 
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Successfully notified Discord. Status: {response.status}")
    except Exception as e:
        print(f"❌ Failed to send Discord notification: {e}")

send()
