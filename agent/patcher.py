def generate_patch(vuln_type: str, vulnerable_code: str) -> str:
    prompt = f"""
You are a senior secure developer. Fix this {vuln_type} vulnerability.
Only return the full corrected file content.

Vulnerable code:
{vulnerable_code}
"""
    return llm.invoke(prompt).content