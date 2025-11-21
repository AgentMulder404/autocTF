from mcp.exec_client import exec_command
import asyncio

async def run_recon(target_ip: str, target_url: str):
    tasks = [
        exec_command(f"nmap -A -T4 {target_ip}"),
        exec_command(f"gobuster dir -u {target_url} -w /usr/share/wordlists/dirb/common.txt -q"),
        exec_command(f"nikto -h {target_url}"),
    ]
    results = await asyncio.gather(*tasks)
    return "\n\n".join(results)