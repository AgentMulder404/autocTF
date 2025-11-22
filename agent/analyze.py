import os
import requests
import json

def detect_vulns(scan_output: str) -> str:
    """Use xAI Grok to detect vulnerabilities from scan output"""

    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI_API_KEY environment variable not set")

    prompt = f"""You are a senior pentester. Given the following scan output, list confirmed vulnerabilities with endpoint and type (SQLi, XSS, etc.).
Only output JSON like:
{{"vulnerabilities": [{{"type": "SQLi", "endpoint": "/login.php", "param": "username"}}]}}

Scan output:
{scan_output[:16000]}"""

    # Direct API call to xAI - using only supported parameters
    payload = {
        "model": "grok-2-1212",  # Latest stable Grok-2 (grok-2-latest also works, grok-3-latest for newest)
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0,
        "max_tokens": 2000
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        print(f"❌ xAI API error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text[:500]}")
        raise RuntimeError(f"Failed to analyze vulnerabilities: {str(e)}")