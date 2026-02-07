import requests
import json
import os
from defusedxml.ElementTree import parse as safe_parse

def parse_test_failures(test_results_file):
    """Parse JUnit XML and return list of failed tests."""
    failures = []
    try:
        if not os.path.exists(test_results_file):
            return failures
        
        tree = safe_parse(test_results_file)
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
    if not webhook or not webhook.startswith("https://"):
        print("❌ Error: DISCORD_WEBHOOK is missing or invalid (must be HTTPS).")
        return
    
    sca_status = os.getenv('SCA_STATUS')
    sast_status = os.getenv('SAST_STATUS')
    qa_status = os.getenv('QA_STATUS')
    dast_status = os.getenv('DAST_STATUS')
    e2e_status = os.getenv('E2E_STATUS')
    test_results_file = os.getenv('TEST_RESULTS_FILE', 'test-results.xml')
    sha = os.getenv('GITHUB_SHA', '0000000')[:7]
    commit_msg = os.getenv('COMMIT_MSG', 'Manual Update').split('\n')[0]
    branch = os.getenv('GITHUB_REF_NAME')
    
    # Check if all tests passed
    failed_parts = []
    test_results = []
    
    if sca_status == 'success':
        test_results.append("SCA (Trivy): Passed")
    elif sca_status:
        test_results.append("❌ SCA (Trivy): Failed")
        failed_parts.append("SCA")
    
    if sast_status == 'success':
        test_results.append("SAST (Bandit): Passed")
    elif sast_status:
        test_results.append("❌ SAST (Bandit): Failed")
        failed_parts.append("SAST")
    
    if dast_status == 'success':
        test_results.append("DAST (OWASP ZAP): Passed")
    elif dast_status:
        test_results.append("❌ DAST (OWASP ZAP): Failed")
        failed_parts.append("DAST")
    
    if e2e_status == 'success':
        test_results.append("E2E Tests: Passed")
    elif e2e_status:
        test_results.append("❌ E2E Tests: Failed")
        failed_parts.append("E2E Tests")
    
    if qa_status == 'success':
        test_results.append("QA Tests: Passed")
    elif qa_status:
        test_results.append("❌ QA Tests: Failed")
        failed_parts.append("QA Tests")
    
    run_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}"
    
    if not failed_parts:
        # All tests passed - show simple message
        color = 3066993  # Green
        desc = f"✅ **Security & QA Checks Passed in** `{branch}`\n\n`{sha}` {commit_msg}\n\n" + "\n".join(test_results) + f"\n\n[View Details on GitHub]({run_url})"
        content = ""
    else:
        # Some tests failed - show individual results
        color = 15158332  # Red
        desc = f"🚨 **Security & QA Checks Failed in** `{branch}`\n\n`{sha}` {commit_msg}\n\nIssues in: {', '.join(failed_parts)}\n\n" + "\n".join(test_results)
        
        # Add individual test failures if QA tests failed
        if "QA Tests" in failed_parts:
            failures = parse_test_failures(test_results_file)
            if failures:
                desc += "\n\n**Failed Tests:**"
                for test_name, failure_msg in failures[:5]:  # Limit to 5 failures to avoid message size limit
                    desc += f"\n• `{test_name}`"
                if len(failures) > 5:
                    desc += f"\n• ... and {len(failures) - 5} more"
        
        desc += f"\n\n<@&{os.getenv('ROLE_ID')}>\n\n[View Details on GitHub]({run_url})"
        content = ""
    
    payload = {
        "content": content, 
        "embeds": [{
            "description": desc, 
            "color": color
        }]
    }
    
    try:
        response = requests.post(
            webhook,
            json=payload,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=10
        )
        response.raise_for_status()
        print(f"Successfully notified Discord. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send Discord notification: {e}")

send()