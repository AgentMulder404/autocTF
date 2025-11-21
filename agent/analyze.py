from langchain_openai import ChatOpenAI
# from langchain_groq import ChatGroq
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# llm = ChatGroq(model="llama3-70b-8192")

def detect_vulns(scan_output: str) -> str:
    prompt = f"""
You are a senior pentester. Given the following scan output, list confirmed vulnerabilities with endpoint and type (SQLi, XSS, etc.).
Only output JSON like:
{{"vulnerabilities": [{{"type": "SQLi", "endpoint": "/login.php", "param": "username"}}]}}

Scan output:
{scan_output[:16000]}
"""
    return llm.invoke(prompt).content