from langchain_openai import ChatOpenAI
import os

# Use xAI's Grok model (OpenAI-compatible API)
llm = ChatOpenAI(
    model="grok-beta",
    temperature=0,
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

def detect_vulns(scan_output: str) -> str:
    prompt = f"""
You are a senior pentester. Given the following scan output, list confirmed vulnerabilities with endpoint and type (SQLi, XSS, etc.).
Only output JSON like:
{{"vulnerabilities": [{{"type": "SQLi", "endpoint": "/login.php", "param": "username"}}]}}

Scan output:
{scan_output[:16000]}
"""
    return llm.invoke(prompt).content